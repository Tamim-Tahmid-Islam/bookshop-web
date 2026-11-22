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
            suggestions = db.get_live_suggestions(q, limit=6, filters=flat_params)
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

        # 1.3 API: Popular Books Ranked by Order History
        if path == '/api/popular-books':
            limit = int(flat_params.get('limit', 12))
            res = db.get_popular_books(limit=limit)
            self._send_json(200, res)
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

        # 3.2 API: Admin Dashboard Data (Protected - tamimtahmid270@gmail.com only)
        if path == '/api/admin/dashboard':
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
            data = db.get_admin_dashboard_data()
            self._send_json(200, data)
            return

        # 3.3 API: Book Requests (Retrieves customer book requests)
        if path == '/api/book-requests':
            limit = int(flat_params.get('limit', 50))
            requests = db.get_book_requests(limit=limit)
            self._send_json(200, {'success': True, 'requests': requests})
            return

        # 3.4 API: User Orders History (with 12-hour cancellation status)
        if path == '/api/user/orders':
            user_id = flat_params.get('user_id')
            email = flat_params.get('email')
            phone = flat_params.get('phone')
            name = flat_params.get('name')
            order_code = flat_params.get('order_code')
            orders = db.get_user_orders(user_id=user_id, email=email, phone=phone, order_code=order_code, name=name)
            self._send_json(200, {'success': True, 'orders': orders})
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
                self.send_header('Cache-Control', 'public, max-age=3600')
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
                delivery = mailer.send_password_reset_email(res['email'], res['full_name'], res['code'])
                if delivery.get('delivered'):
                    self._send_json(200, {
                        'success': True,
                        'email': res['email'],
                        'message': 'We have sent you a code to verify.'
                    })
                else:
                    err_msg = delivery.get('message', 'Email dispatch error.')
                    self._send_json(500, {
                        'success': False,
                        'email': res['email'],
                        'message': f"Failed to send email: {err_msg}"
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

        # 5. API: Add New Book (Admin only)
        if path == '/api/books':
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
            res = db.create_book(body)
            self._send_json(201 if res['success'] else 400, res)
            return

        # 5.1 API: Update Book (POST fallback - Admin only)
        if path.startswith('/api/books/') and path.endswith('/update'):
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
            try:
                book_id = int(path.split('/')[-2])
                res = db.update_book(book_id, body)
                self._send_json(200 if res['success'] else 400, res)
            except ValueError:
                self._send_json(400, {'error': 'Invalid book ID'})
            return

        # 6. API: Checkout & Create Order (Transactional Order Placement)
        if path == '/api/orders':
            res = db.create_order(body)
            if res['success']:
                customer_email = (body.get('customer_email') or body.get('email') or res.get('customer_email') or '').strip()
                user_id = body.get('user_id')
                if not customer_email and user_id:
                    try:
                        u_info = db.get_user_by_id(user_id)
                        if u_info and u_info.get('email'):
                            customer_email = u_info['email'].strip()
                    except Exception as err:
                        print(f"[Order] Could not retrieve user email from user_id: {err}")

                customer_name = (body.get('customer_name') or res.get('customer_name') or '').strip()
                if not customer_name and user_id:
                    try:
                        u_info = db.get_user_by_id(user_id)
                        if u_info and u_info.get('full_name'):
                            customer_name = u_info['full_name'].strip()
                    except Exception:
                        pass
                if not customer_name:
                    customer_name = 'Customer'

                # Send order confirmation email
                # Delivered to the customer's personal email (if specified/signed in) AND alerts operations desk
                try:
                    target_cust_email = customer_email or "tamimtahmid270@gmail.com"
                    print(f"[Order] Delivering confirmation receipt to customer account: {target_cust_email}")
                    email_result = mailer.send_order_confirmation_email(
                        to_email=target_cust_email,
                        customer_name=customer_name,
                        order_code=res['order_code'],
                        total_amount=res['total_amount'],
                        delivery_address=body.get('delivery_address', ''),
                        payment_method=body.get('payment_method', 'Cash on Delivery'),
                        items=body.get('items', []),
                        transaction_id=res.get('transaction_id', '')
                    )
                    res['email_dispatch'] = email_result
                except Exception as e:
                    print(f"[Order] Order confirmation email dispatch failed: {e}")
                    res['email_dispatch'] = {'delivered': False, 'error': str(e)}

                # Automatically mark status as Confirmed upon placing order
                if res.get('order_id'):
                    db.update_order_status(res['order_id'], 'Confirmed')
            self._send_json(201 if res['success'] else 400, res)
            return

        # 6.1 API: Update Order Status (Admin only)
        if path == '/api/orders/update-status':
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
            try:
                order_id = int(body.get('order_id', 0))
            except (ValueError, TypeError):
                order_id = 0
            new_status = body.get('status', '').strip()
            if not order_id or not new_status:
                self._send_json(400, {'success': False, 'message': 'order_id and status are required.'})
                return
            res = db.update_order_status(order_id, new_status)
            self._send_json(200 if res['success'] else 400, res)
            return

        # 6.2 API: Cancel Order (Customer 12-hour self-cancellation & online refund)
        if path == '/api/orders/cancel':
            order_id = body.get('order_id')
            if not order_id:
                self._send_json(400, {'success': False, 'message': 'order_id is required.'})
                return
            user_id = body.get('user_id')
            user_email = body.get('email') or body.get('user_email')
            cancel_reason = body.get('cancel_reason') or 'Customer requested cancellation'
            res = db.cancel_user_order(int(order_id), user_id=user_id, user_email=user_email, cancel_reason=cancel_reason)
            if res.get('success'):
                # Dispatch cancellation email
                cust_email = res.get('customer_email') or user_email
                if cust_email:
                    try:
                        mailer.send_order_cancellation_email(
                            customer_name=res.get('customer_name', 'Customer'),
                            customer_email=cust_email,
                            order_code=res.get('order_code', ''),
                            total_amount=res.get('total_amount', 0.0),
                            delivery_fee=res.get('delivery_fee', 60.0),
                            refund_amount=res.get('refund_amount', 0.0),
                            payment_method=res.get('payment_method', 'Cash on Delivery'),
                            is_online_paid=res.get('is_online_paid', False),
                            cancel_reason=res.get('cancel_reason', ''),
                            placed_at=res.get('placed_at', ''),
                            cancelled_at=res.get('cancelled_at', '')
                        )
                    except Exception as email_err:
                        print(f"[App] Order cancellation email dispatch error: {email_err}")
                self._send_json(200, res)
            else:
                self._send_json(400, res)
            return

        # 7. API: Customer Support Query (Dispatches email to tamimtahmid270@gmail.com)
        if path == '/api/support/query':
            customer_name = (body.get('name') or body.get('customer_name') or '').strip()
            customer_email = (body.get('email') or body.get('customer_email') or '').strip()
            customer_phone = (body.get('phone') or body.get('customer_phone') or '').strip()
            topic = (body.get('topic') or '').strip()
            message = (body.get('message') or '').strip()

            if not customer_name or not customer_email or not topic or not message:
                self._send_json(400, {'success': False, 'message': 'Name, email, topic, and message details are required.'})
                return

            # Store in database
            query_record = db.create_customer_query({
                'customer_name': customer_name,
                'customer_email': customer_email,
                'customer_phone': customer_phone,
                'topic': topic,
                'message': message
            })

            # Dispatch email using customer information to designated support email
            email_res = mailer.send_support_query_email(
                customer_name=customer_name,
                customer_email=customer_email,
                customer_phone=customer_phone,
                topic=topic,
                message=message
            )

            self._send_json(200, {
                'success': True,
                'message': 'Thank you! Your query has been submitted and an email notification has been dispatched.',
                'query_id': query_record.get('query_id'),
                'delivered': email_res.get('delivered', False)
            })
            return

        # 8. API: Book Request (Customer requests title not currently in catalog)
        if path == '/api/book-requests':
            book_title = (body.get('book_title') or body.get('title') or '').strip()
            requester_name = (body.get('requester_name') or body.get('name') or '').strip()
            requester_email = (body.get('requester_email') or body.get('email') or '').strip()
            requester_phone = (body.get('requester_phone') or body.get('phone') or '').strip()
            author_name = (body.get('author_name') or body.get('author') or '').strip()
            isbn = (body.get('isbn') or '').strip()
            genre_or_topic = (body.get('genre_or_topic') or body.get('genre') or '').strip()
            notes = (body.get('notes') or '').strip()
            user_id = body.get('user_id')

            if not book_title or not requester_name or not requester_email:
                self._send_json(400, {'success': False, 'message': 'Book title, your name, and email address are required.'})
                return

            # Store in database
            req_record = db.create_book_request({
                'user_id': user_id,
                'requester_name': requester_name,
                'requester_email': requester_email,
                'requester_phone': requester_phone,
                'book_title': book_title,
                'author_name': author_name,
                'isbn': isbn,
                'genre_or_topic': genre_or_topic,
                'notes': notes
            })

            # Dispatch notification to admin and auto-reply receipt to customer
            email_res = mailer.send_book_request_email(
                customer_name=requester_name,
                customer_email=requester_email,
                customer_phone=requester_phone,
                book_title=book_title,
                author_name=author_name,
                isbn=isbn,
                notes=notes,
                genre_or_topic=genre_or_topic
            )

            self._send_json(200, {
                'success': True,
                'message': 'Your book request has been received and queued for catalog sourcing!',
                'request_id': req_record.get('request_id'),
                'delivered': email_res.get('delivered', False)
            })
            return

        self._send_json(404, {'error': 'Endpoint not found'})

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        body = self._read_body_json()

        if path.startswith('/api/books/'):
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
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
            admin_email = self.headers.get('X-Admin-Email', '').strip().lower()
            admin_role = self.headers.get('X-Admin-Role', '').strip()
            if admin_email != 'tamimtahmid270@gmail.com' or admin_role != 'Admin':
                self._send_json(403, {'success': False, 'message': 'Access forbidden: Admin access only.'})
                return
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
