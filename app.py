"""
PageVault - Web Server & RESTful API Handler
Built with Python standard library (zero third-party dependencies required).
Runs seamlessly on Windows, macOS, and Linux out of the box.
"""

import http.server
import socketserver
import json
import urllib.parse
import os
import mimetypes
import time
import config
from db_adapter import db
import mailer


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')


class PageVaultRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Enable CORS and disable aggressive caching for development
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def _send_json(self, status_code: int, data: dict):
        response_bytes = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(response_bytes)))
        self.end_headers()
        self.wfile.write(response_bytes)

    def _read_body_json(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        body_bytes = self.rfile.read(content_length)
        try:
            return json.loads(body_bytes.decode('utf-8'))
        except Exception:
            return {}

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query_params = urllib.parse.parse_qs(parsed.query)
        flat_params = {k: v[0] for k, v in query_params.items()}

        # 1. API: Search Books with DBMS query analytics
        if path == '/api/search':
            result = db.search_books(flat_params)
            self._send_json(200, result)
            return

        # 1.1 API: Live Search Suggestions (Typeahead Dropdown)
        if path == '/api/suggestions':
            q = flat_params.get('q', '')
            suggestions = db.get_live_suggestions(q)
            self._send_json(200, {'suggestions': suggestions})
            return

        # 1.2 Health Check Endpoint (Enterprise Observability)
        if path in ['/healthz', '/api/health']:
            self._send_json(200, {
                'status': 'healthy',
                'service': 'PageVault Bookshop API',
                'database_engine': db.mode,
                'timestamp': time.time(),
                'version': '2.0.0'
            })
            return

        # 2. API: Categories
        if path == '/api/categories':
            categories = db.get_categories()
            self._send_json(200, {'categories': categories})
            return

        # 3. API: Publishers
        if path == '/api/publishers':
            publishers = db.get_publishers()
            self._send_json(200, {'publishers': publishers})
            return

        # 3.1 API: Authors
        if path == '/api/authors':
            authors = db.get_authors()
            self._send_json(200, {'authors': authors})
            return

        # 3.2 API: Admin Dashboard Data
        if path == '/api/admin/dashboard':
            data = db.get_admin_dashboard_data()
            self._send_json(200, data)
            return

        # 4. API: Single Book details
        if path.startswith('/api/books/'):
            try:
                book_id = int(path.split('/')[-1])
                book = db.get_book_details(book_id)
                if book:
                    self._send_json(200, {'book': book})
                else:
                    self._send_json(404, {'error': 'Book not found'})
            except ValueError:
                self._send_json(400, {'error': 'Invalid book ID'})
            return

        # 5. API: Database status & metadata
        if path == '/api/db-status':
            self._send_json(200, {
                'mode': db.mode,
                'mysql_config': {
                    'host': config.MYSQL_CONFIG['host'],
                    'port': config.MYSQL_CONFIG['port'],
                    'database': config.MYSQL_CONFIG['database'],
                    'user': config.MYSQL_CONFIG['user']
                },
                'total_categories': len(db.get_categories()),
                'status': 'Operational'
            })
            return

        # 6. Serve Frontend Homepage
        if path in ['', '/', '/index.html']:
            index_path = os.path.join(TEMPLATES_DIR, 'index.html')
            if os.path.exists(index_path):
                with open(index_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # 7. Serve Static files (/static/...)
        if path.startswith('/static/'):
            rel_path = path[len('/static/'):]
            file_path = os.path.join(STATIC_DIR, rel_path.replace('/', os.sep))
            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime_type, _ = mimetypes.guess_type(file_path)
                with open(file_path, 'rb') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-Type', mime_type or 'application/octet-stream')
                self.send_header('Content-Length', str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return

        # Fallback 404
        self.send_response(404)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'404 Not Found')

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        # 1. API: Login
        if path == '/api/auth/login':
            identifier = body.get('identifier', '')
            password = body.get('password', '')
            user = db.authenticate_user(identifier, password)
            if user:
                self._send_json(200, {
                    'success': True,
                    'user': user,
                    'message': f'Welcome back, {user["full_name"]}!'
                })
            else:
                self._send_json(401, {
                    'success': False,
                    'message': 'Invalid username/email or password.'
                })
            return

        # 2. API: Register
        if path == '/api/auth/register':
            username = body.get('username', '')
            email = body.get('email', '')
            password = body.get('password', '')
            full_name = body.get('full_name', '')
            if not (username and email and password and full_name):
                self._send_json(400, {'success': False, 'message': 'All fields are required.'})
                return
            res = db.register_user(username, email, password, full_name)
            self._send_json(200 if res['success'] else 400, res)
            return

        # 3. API: Forgot Password (Step 1: Request Code / Token)
        if path == '/api/auth/forgot-password':
            email = body.get('email', '')
            if not email:
                self._send_json(400, {'success': False, 'message': 'Please enter an email address.'})
                return
            res = db.initiate_forgot_password(email)
            if res['success']:
                mailer.send_password_reset_email(res['email'], res['full_name'], res['code'])
                self._send_json(200, {
                    'success': True,
                    'email': res['email'],
                    'message': 'We have sent you a code to verify.'
                })
            else:
                self._send_json(404, {'success': False, 'message': res['message']})
            return

        # 4. API: Reset Password (Step 2: Submit New Password with Code/Token)
        if path == '/api/auth/reset-password':
            token_or_code = body.get('token_or_code', '')
            new_password = body.get('new_password', '')
            if not token_or_code or not new_password:
                self._send_json(400, {'success': False, 'message': 'Verification code and new password are required.'})
                return
            res = db.complete_password_reset(token_or_code, new_password)
            self._send_json(200 if res['success'] else 400, res)
            return

        # 5. API: Add New Book
        if path == '/api/books':
            res = db.create_book(body)
            self._send_json(201 if res['success'] else 400, res)
            return

        # 5.1 API: Update Book (POST fallback)
        if path.startswith('/api/books/') and path.endswith('/update'):
            try:
                book_id = int(path.split('/')[-2])
                res = db.update_book(book_id, body)
                self._send_json(200 if res['success'] else 400, res)
            except ValueError:
                self._send_json(400, {'error': 'Invalid book ID'})
            return

        # 6. API: Checkout & Create Order (Transactional ACID Order Placement)
        if path == '/api/orders':
            res = db.create_order(body)
            self._send_json(201 if res['success'] else 400, res)
            return

        self._send_json(404, {'error': 'Endpoint not found'})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        if path.startswith('/api/books/'):
            try:
                book_id = int(path.split('/')[-1])
                res = db.update_book(book_id, body)
                self._send_json(200 if res['success'] else 400, res)
            except ValueError:
                self._send_json(400, {'error': 'Invalid book ID'})
            return

        self._send_json(404, {'error': 'Endpoint not found'})

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        if path.startswith('/api/books/'):
            try:
                book_id = int(path.split('/')[-1])
                res = db.delete_book(book_id)
                self._send_json(200 if res['success'] else 400, res)
            except ValueError:
                self._send_json(400, {'error': 'Invalid book ID'})
            return
        self._send_json(404, {'error': 'Endpoint not found'})


def run(host=config.SERVER_HOST, port=config.SERVER_PORT):
    # Ensure port reuse
    socketserver.TCPServer.allow_reuse_address = True
    server_address = (host, port)
    with socketserver.TCPServer(server_address, PageVaultRequestHandler) as httpd:
        print("=" * 65)
        print("  📚 PageVault - Online Bookshop & Book Management System")
        print(f"  🚀 Server running at: http://{host}:{port}/")
        print(f"  💾 Database Mode: {db.mode}")
        print("=" * 65)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server gracefully...")
            httpd.server_close()


if __name__ == '__main__':
    run()
