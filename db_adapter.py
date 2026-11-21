"""
PageVault Database Adapter
Handles database abstraction, prepared query generation, relational algebra mapping,
order management with ACID transactions, live typeahead search, and SQLite/MySQL dual-mode.
"""

import sqlite3
import hashlib
import secrets
import time
import os
from datetime import datetime, timedelta
import config

# Global connection flag
DB_MODE = 'SQLITE'
mysql_module = None

try:
    import pymysql
    import pymysql.cursors
    mysql_module = pymysql
except ImportError:
    try:
        import mysql.connector
        mysql_module = mysql.connector
    except ImportError:
        mysql_module = None


def hash_password(password: str) -> str:
    """Return SHA-256 hash of password for security."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


class DatabaseAdapter:
    def __init__(self):
        self.mode = 'SQLITE'
        self.sqlite_db_path = os.path.join(os.path.dirname(__file__), 'pagevault.db')
        self._init_database()

    def _test_mysql(self):
        if not mysql_module:
            return False
        try:
            conn = mysql_module.connect(**config.MYSQL_CONFIG)
            conn.close()
            return True
        except Exception:
            return False

    def _init_database(self):
        """Initializes database schema and seed data in embedded store if needed."""
        if self._test_mysql():
            self.mode = 'MYSQL'
            print("[PageVault] Connected to MySQL Server!")
            return

        self.mode = 'SQLITE'
        print(f"[PageVault] Running in Embedded Relational Mode ({self.sqlite_db_path})")
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Create Tables
        cursor.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            category_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            icon TEXT DEFAULT 'book',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS publishers (
            publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            country TEXT DEFAULT 'Unknown',
            founded_year INTEGER,
            website TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS authors (
            author_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            bio TEXT,
            birth_year INTEGER,
            country TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS books (
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            subtitle TEXT,
            publisher_id INTEGER,
            category_id INTEGER,
            price REAL NOT NULL,
            discount_pct REAL DEFAULT 0.0,
            stock_qty INTEGER NOT NULL DEFAULT 0,
            publication_year INTEGER,
            page_count INTEGER,
            language TEXT DEFAULT 'English',
            cover_image TEXT,
            description TEXT,
            is_deleted INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE SET NULL,
            FOREIGN KEY (category_id) REFERENCES categories(category_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS book_authors (
            book_id INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            is_primary INTEGER DEFAULT 1,
            PRIMARY KEY (book_id, author_id),
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT DEFAULT 'Customer',
            status TEXT DEFAULT 'Active',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS password_resets (
            reset_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            reset_token TEXT NOT NULL UNIQUE,
            reset_code TEXT NOT NULL,
            expires_at DATETIME NOT NULL,
            is_used INTEGER DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
            review_title TEXT,
            review_text TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_code TEXT NOT NULL UNIQUE,
            user_id INTEGER,
            customer_name TEXT NOT NULL,
            customer_phone TEXT NOT NULL,
            delivery_address TEXT NOT NULL,
            district TEXT NOT NULL DEFAULT 'Dhaka',
            payment_method TEXT NOT NULL,
            payment_status TEXT NOT NULL DEFAULT 'Pending',
            order_status TEXT NOT NULL DEFAULT 'Confirmed',
            subtotal REAL NOT NULL,
            delivery_fee REAL NOT NULL,
            total_amount REAL NOT NULL,
            transaction_id TEXT DEFAULT '',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS order_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
            FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE RESTRICT
        );

        CREATE TABLE IF NOT EXISTS book_audit_log (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            changed_by TEXT DEFAULT 'System',
            old_price REAL,
            new_price REAL,
            old_stock INTEGER,
            new_stock INTEGER,
            changed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for high-throughput query optimization
        CREATE INDEX IF NOT EXISTS idx_books_price ON books (price);
        CREATE INDEX IF NOT EXISTS idx_books_year ON books (publication_year);
        CREATE INDEX IF NOT EXISTS idx_books_cat_price ON books (category_id, price);
        CREATE INDEX IF NOT EXISTS idx_books_stock ON books (stock_qty);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users (email);
        CREATE INDEX IF NOT EXISTS idx_resets_token ON password_resets (reset_token);
        CREATE INDEX IF NOT EXISTS idx_orders_code ON orders (order_code);

        CREATE TABLE IF NOT EXISTS customer_queries (
            query_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT NOT NULL,
            customer_phone TEXT DEFAULT '',
            topic TEXT NOT NULL,
            message TEXT NOT NULL,
            status TEXT DEFAULT 'New',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Ensure transaction_id column exists in existing database files
        try:
            cursor.execute("ALTER TABLE orders ADD COLUMN transaction_id TEXT DEFAULT ''")
        except Exception:
            pass

        # Check if seed data exists or requires full 100 catalog expansion
        cursor.execute("SELECT COUNT(*) AS cnt FROM books WHERE is_deleted = 0")
        if cursor.fetchone()['cnt'] < 100:
            self._seed_sqlite(cursor)

        # Enforce Tamim Tahmid as the primary and only Admin (email: tamimtahmid270@gmail.com / pwd: Tamim27#)
        admin_hash = hash_password('Tamim27#')
        cursor.execute("SELECT user_id FROM users WHERE email = 'tamimtahmid270@gmail.com'")
        admin_row = cursor.fetchone()
        if admin_row:
            cursor.execute("UPDATE users SET password_hash = ?, role = 'Admin', status = 'Active' WHERE email = 'tamimtahmid270@gmail.com'", (admin_hash,))
        else:
            cursor.execute("INSERT INTO users (username, email, password_hash, full_name, role, status) VALUES ('tamim_tahmid', 'tamimtahmid270@gmail.com', ?, 'Tamim Tahmid', 'Admin', 'Active')", (admin_hash,))

        # Demote any other accounts from Admin to Customer
        cursor.execute("UPDATE users SET role = 'Customer' WHERE email != 'tamimtahmid270@gmail.com' AND role = 'Admin'")

        conn.commit()
        conn.close()

    def _seed_sqlite(self, cursor):
        """Populates initial seed records with 100 verified books across 12 diverse genres."""
        try:
            import populate_100_books
            populate_100_books.seed_into_cursor(cursor)
        except Exception as e:
            print(f"[Seed] Error seeding 100 books: {e}")

        # Ensure default test accounts
        pw_hash = hash_password('Password123!')
        admin_pw_hash = hash_password('Tamim27#')
        users = [
            (1, 'librarian_sarah', 'librarian@pagevault.com', pw_hash, 'Sarah Jenkins', 'Customer', 'Active'),
            (2, 'alex_reader', 'alex@example.com', pw_hash, 'Alex Morgan', 'Customer', 'Active'),
            (3, 'sophia_code', 'sophia@tech.edu', pw_hash, 'Sophia Chen', 'Customer', 'Active'),
            (4, 'tamim_tahmid', 'tamimtahmid270@gmail.com', admin_pw_hash, 'Tamim Tahmid', 'Admin', 'Active')
        ]
        cursor.executemany("INSERT OR IGNORE INTO users (user_id, username, email, password_hash, full_name, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)", users)

    def _get_connection(self):
        if self.mode == 'MYSQL':
            return mysql_module.connect(**config.MYSQL_CONFIG)
        conn = sqlite3.connect(self.sqlite_db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def get_categories(self):
        """Returns all categories with book counts."""
        conn = self._get_connection()
        cursor = conn.cursor()
        query = """
        SELECT c.category_id, c.name, c.slug, c.icon, c.description,
               COUNT(b.book_id) AS book_count
        FROM categories c
        LEFT JOIN books b ON c.category_id = b.category_id AND b.is_deleted = 0
        GROUP BY c.category_id, c.name, c.slug, c.icon, c.description
        ORDER BY c.name ASC
        """
        cursor.execute(query)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_publishers(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT publisher_id, name, country FROM publishers ORDER BY name ASC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_authors(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT author_id, name, country FROM authors ORDER BY name ASC")
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def get_live_suggestions(self, query_text: str, limit: int = 5):
        """Returns rapid instant search suggestions for the typeahead dropdown."""
        query_text = query_text.strip()
        if not query_text:
            return []

        conn = self._get_connection()
        cursor = conn.cursor()
        sql = """
        SELECT 
            b.book_id,
            b.title,
            b.cover_image,
            b.price,
            b.discount_pct,
            ROUND(b.price * (1.0 - (b.discount_pct / 100.0)), 2) AS effective_price,
            c.name AS category_name,
            GROUP_CONCAT(DISTINCT a.name) AS author_names
        FROM books b
        INNER JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        WHERE b.is_deleted = 0 AND (b.title LIKE ? OR a.name LIKE ? OR b.isbn LIKE ?)
        GROUP BY b.book_id
        ORDER BY b.title ASC
        LIMIT ?
        """
        pat = f"%{query_text}%"
        cursor.execute(sql, (pat, pat, pat, limit))
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return results

    def search_books(self, params: dict):
        """
        Main DBMS search feature:
        Generates dynamic MySQL query, tracks parameterization, builds relational algebra,
        and provides EXPLAIN optimization analysis.
        """
        start_time = time.perf_counter()

        keyword = params.get('q', '').strip()
        category_id = params.get('category_id')
        min_price = params.get('min_price')
        max_price = params.get('max_price')
        min_rating = params.get('min_rating')
        in_stock = params.get('in_stock', False)
        sort_by = params.get('sort', 'relevance')
        page = int(params.get('page', 1))
        page_size = int(params.get('page_size', 12))
        offset = (page - 1) * page_size

        where_clauses = ["b.is_deleted = 0"]
        sql_params = []
        algebra_selections = []

        if keyword:
            where_clauses.append("(b.title LIKE ? OR b.description LIKE ? OR a.name LIKE ? OR b.isbn LIKE ? OR c.name LIKE ?)")
            pat = f"%{keyword}%"
            sql_params.extend([pat, pat, pat, pat, pat])
            algebra_selections.append(f"search_term('{keyword}')")

        if category_id and str(category_id).isdigit() and int(category_id) > 0:
            where_clauses.append("b.category_id = ?")
            sql_params.append(int(category_id))
            algebra_selections.append(f"category_id = {category_id}")

        if min_price is not None and str(min_price) != '':
            try:
                min_p = float(min_price)
                where_clauses.append("b.price >= ?")
                sql_params.append(min_p)
                algebra_selections.append(f"price ≥ ৳{min_p}")
            except ValueError:
                pass

        if max_price is not None and str(max_price) != '':
            try:
                max_p = float(max_price)
                where_clauses.append("b.price <= ?")
                sql_params.append(max_p)
                algebra_selections.append(f"price ≤ ৳{max_p}")
            except ValueError:
                pass

        publisher_id = params.get('publisher_id')
        if publisher_id and str(publisher_id).isdigit() and int(publisher_id) > 0:
            where_clauses.append("b.publisher_id = ?")
            sql_params.append(int(publisher_id))
            algebra_selections.append(f"publisher_id = {publisher_id}")

        on_sale = params.get('on_sale')
        if on_sale in [True, 'true', '1', 1]:
            where_clauses.append("b.discount_pct > 0")
            algebra_selections.append("discount_pct > 0")

        year_min = params.get('year_min')
        if year_min and str(year_min).isdigit():
            where_clauses.append("b.publication_year >= ?")
            sql_params.append(int(year_min))
            algebra_selections.append(f"year >= {year_min}")

        year_max = params.get('year_max')
        if year_max and str(year_max).isdigit():
            where_clauses.append("b.publication_year <= ?")
            sql_params.append(int(year_max))
            algebra_selections.append(f"year <= {year_max}")

        if in_stock in [True, 'true', '1', 1]:
            where_clauses.append("b.stock_qty > 0")
            algebra_selections.append("stock_qty > 0")

        popular = params.get('popular')
        is_popular_mode = popular in [True, 'true', '1', 1] or sort_by == 'popular'
        if is_popular_mode:
            where_clauses.append("b.stock_qty > 0")
            algebra_selections.append("stock_qty > 0 (available titles)")

        having_clause = ""
        having_algebra = ""
        if min_rating and str(min_rating) != '':
            try:
                mr = float(min_rating)
                if mr > 0:
                    having_clause = "HAVING avg_rating >= ?"
                    sql_params.append(mr)
                    having_algebra = f"HAVING AVG(rating) ≥ {mr}"
            except ValueError:
                pass

        order_by = "b.book_id ASC"
        if is_popular_mode or sort_by == 'popular':
            order_by = "total_ordered DESC, avg_rating DESC, b.stock_qty DESC"
        elif sort_by == 'price_asc':
            order_by = "effective_price ASC"
        elif sort_by == 'price_desc':
            order_by = "effective_price DESC"
        elif sort_by == 'rating_desc':
            order_by = "avg_rating DESC, total_reviews DESC"
        elif sort_by == 'year_desc':
            order_by = "b.publication_year DESC"
        elif sort_by == 'year_asc':
            order_by = "b.publication_year ASC"
        elif sort_by == 'title_asc':
            order_by = "b.title ASC"
        elif sort_by == 'discount_desc':
            order_by = "b.discount_pct DESC"

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        conn = self._get_connection()
        cursor = conn.cursor()

        # Execute Count query
        count_sql = f"""
        SELECT COUNT(DISTINCT b.book_id) AS total_count
        FROM books b
        INNER JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN reviews r ON b.book_id = r.book_id
        WHERE {where_sql}
        """
        count_params = sql_params[:-1] if having_clause else sql_params[:]
        cursor.execute(count_sql, count_params)
        count_row = cursor.fetchone()
        total_records = count_row['total_count'] if isinstance(count_row, (dict, sqlite3.Row)) else count_row[0]

        # Execute Main Search Query
        main_sql = f"""
        SELECT 
            b.book_id,
            b.isbn,
            b.title,
            b.subtitle,
            b.price,
            b.discount_pct,
            ROUND(b.price * (1.0 - (b.discount_pct / 100.0)), 2) AS effective_price,
            b.stock_qty,
            b.publication_year,
            b.cover_image,
            b.description,
            c.category_id,
            c.name AS category_name,
            p.name AS publisher_name,
            GROUP_CONCAT(DISTINCT a.name) AS authors,
            ROUND(COALESCE(AVG(r.rating), 0), 1) AS avg_rating,
            COUNT(DISTINCT r.review_id) AS total_reviews,
            COALESCE(oi_summary.total_ordered, 0) AS total_ordered
        FROM books b
        INNER JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN reviews r ON b.book_id = r.book_id
        LEFT JOIN (
            SELECT book_id, SUM(quantity) AS total_ordered
            FROM order_items
            GROUP BY book_id
        ) oi_summary ON b.book_id = oi_summary.book_id
        WHERE {where_sql}
        GROUP BY b.book_id, c.name, p.name
        {having_clause}
        ORDER BY {order_by}
        LIMIT ? OFFSET ?
        """
        run_params = sql_params + [page_size, offset]
        cursor.execute(main_sql, run_params)
        books = [dict(row) for row in cursor.fetchall()]

        conn.close()
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        total_pages = max(1, (total_records + page_size - 1) // page_size) if total_records else 1
        start_index = (page - 1) * page_size + 1 if total_records > 0 else 0
        end_index = min(page * page_size, total_records)

        return {
            'books': books,
            'total_count': total_records,
            'page': page,
            'page_size': page_size,
            'total_pages': total_pages,
            'start_index': start_index,
            'end_index': end_index,
            'execution_time_ms': elapsed_ms,
            'db_engine': self.mode
        }

    def get_popular_books(self, limit: int = 12):
        """Returns top available books ranked by order history sales from the database."""
        return self.search_books({'popular': True, 'page_size': limit})

    def get_book_details(self, book_id: int):
        """Fetches full book details including reviews, publisher, and authors."""
        conn = self._get_connection()
        cursor = conn.cursor()

        sql = """
        SELECT 
            b.*,
            c.name AS category_name,
            p.name AS publisher_name,
            p.website AS publisher_website,
            p.country AS publisher_country,
            GROUP_CONCAT(DISTINCT a.name) AS author_names,
            ROUND(COALESCE(AVG(r.rating), 0), 1) AS avg_rating,
            COUNT(DISTINCT r.review_id) AS total_reviews
        FROM books b
        LEFT JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN reviews r ON b.book_id = r.book_id
        WHERE b.book_id = ? AND b.is_deleted = 0
        GROUP BY b.book_id
        """
        cursor.execute(sql, (book_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None

        book_data = dict(row)

        rev_sql = """
        SELECT r.review_id, r.rating, r.review_title, r.review_text, r.created_at,
               u.full_name AS user_name, u.role AS user_role
        FROM reviews r
        JOIN users u ON r.user_id = u.user_id
        WHERE r.book_id = ?
        ORDER BY r.created_at DESC
        """
        cursor.execute(rev_sql, (book_id,))
        book_data['reviews'] = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return book_data

    # -------------------------------------------------------------------------
    # ACID Transactional Checkout & Order Management
    # -------------------------------------------------------------------------
    def create_order(self, order_data: dict):
        """
        Executes ACID transactional order placement:
        1. Validates input
        2. Acquires row locks / verifies inventory stock
        3. Deducts stock quantity atomically
        4. Inserts Order and Order Items
        5. Commits transaction or rolls back on any error
        """
        customer_name = order_data.get('customer_name', '').strip()
        customer_phone = order_data.get('customer_phone', '').strip()
        delivery_address = order_data.get('delivery_address', '').strip()
        district = order_data.get('district', 'Dhaka')
        payment_method = order_data.get('payment_method', 'Cash on Delivery')
        user_id = order_data.get('user_id')
        items = order_data.get('items', [])

        if not (customer_name and customer_phone and delivery_address and items):
            return {'success': False, 'message': 'Missing mandatory customer shipping or order item details.'}

        # Calculate fees
        delivery_fee = 60.0 if district.lower() == 'dhaka' else 120.0
        subtotal = 0.0

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Begin explicit transaction
            cursor.execute("BEGIN TRANSACTION")

            # 1. Verify stock for each book
            for item in items:
                b_id = item['book_id']
                qty = int(item['quantity'])
                cursor.execute("SELECT stock_qty, price, discount_pct, title FROM books WHERE book_id = ? AND is_deleted = 0", (b_id,))
                b_row = cursor.fetchone()
                if not b_row:
                    raise ValueError(f"Book #{b_id} is no longer available in the catalog.")
                if b_row['stock_qty'] < qty:
                    raise ValueError(f"Insufficient stock for '{b_row['title']}'. Only {b_row['stock_qty']} copies left.")
                
                effective_unit_price = round(b_row['price'] * (1.0 - (b_row['discount_pct'] / 100.0)), 2)
                item['unit_price'] = effective_unit_price
                item['total_price'] = round(effective_unit_price * qty, 2)
                subtotal += item['total_price']

            total_amount = round(subtotal + delivery_fee, 2)

            # 2. Generate unique Order Code
            order_code = f"PV-{int(time.time()) % 1000000:06d}-{secrets.randbelow(900)+100}"

            # 3. Insert Order
            trx_id = order_data.get('transaction_id', '')
            pay_status = 'Completed' if payment_method in ['bKash', 'Nagad', 'Card'] or trx_id else 'Pending'

            cursor.execute("""
                INSERT INTO orders (order_code, user_id, customer_name, customer_phone, delivery_address, district, payment_method, payment_status, order_status, subtotal, delivery_fee, total_amount, transaction_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, ?, ?, ?)
            """, (
                order_code, user_id, customer_name, customer_phone, delivery_address, district,
                payment_method, pay_status,
                subtotal, delivery_fee, total_amount, trx_id
            ))
            order_id = cursor.lastrowid

            # 4. Insert Order Items & Deduct Stock
            for item in items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, book_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (order_id, item['book_id'], item['quantity'], item['unit_price'], item['total_price']))

                # Atomic stock deduction
                cursor.execute("UPDATE books SET stock_qty = stock_qty - ?, updated_at = CURRENT_TIMESTAMP WHERE book_id = ?",
                               (item['quantity'], item['book_id']))

                # Audit log
                cursor.execute("INSERT INTO book_audit_log (book_id, action, changed_by, old_stock, new_stock) VALUES (?, 'PURCHASE', 'OrderSystem', NULL, NULL)",
                               (item['book_id'],))

            conn.commit()
            conn.close()
            return {
                'success': True,
                'order_id': order_id,
                'order_code': order_code,
                'transaction_id': trx_id,
                'payment_status': pay_status,
                'payment_method': payment_method,
                'total_amount': total_amount,
                'subtotal': subtotal,
                'delivery_fee': delivery_fee,
                'message': f"Order #{order_code} confirmed successfully!"
            }
        except Exception as e:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': str(e)}

    # -------------------------------------------------------------------------
    # Authentication & Forgot Password Operations
    # -------------------------------------------------------------------------
    def authenticate_user(self, identifier: str, password: str):
        """Authenticates user via username or email."""
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed = hash_password(password)

        cursor.execute("""
            SELECT user_id, username, email, full_name, role, status
            FROM users
            WHERE (email = ? OR username = ?) AND password_hash = ?
        """, (identifier.lower().strip(), identifier.strip(), hashed))

        user = cursor.fetchone()
        conn.close()
        if user:
            return dict(user)
        return None

    def register_user(self, username: str, email: str, password: str, full_name: str, role='Customer'):
        """Registers a new user into the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        hashed = hash_password(password)

        try:
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, full_name, role)
                VALUES (?, ?, ?, ?, ?)
            """, (username.strip(), email.lower().strip(), hashed, full_name.strip(), role))
            conn.commit()
            user_id = cursor.lastrowid
            conn.close()
            return {'success': True, 'user_id': user_id, 'message': 'Registration successful.'}
        except Exception as e:
            conn.close()
            return {'success': False, 'message': f"Account creation failed: {str(e)}"}

    def initiate_forgot_password(self, email: str):
        """
        Handles Forgot Password step 1:
        Validates user, creates a secure reset_token and 6-digit code with 1-hour expiration.
        """
        email = email.lower().strip()
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id, full_name FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return {'success': False, 'message': 'No account registered with that email address.'}

        user_id = user['user_id']
        full_name = user['full_name']

        token = secrets.token_urlsafe(32)
        code = str(secrets.randbelow(900000) + 100000)
        expires_at = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')

        cursor.execute("UPDATE password_resets SET is_used = 1 WHERE user_id = ? AND is_used = 0", (user_id,))
        cursor.execute("""
            INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at, is_used)
            VALUES (?, ?, ?, ?, 0)
        """, (user_id, token, code, expires_at))

        conn.commit()
        conn.close()

        return {
            'success': True,
            'email': email,
            'full_name': full_name,
            'token': token,
            'code': code,
            'expires_at': expires_at,
            'message': 'Password reset request generated successfully.'
        }

    def complete_password_reset(self, identifier_token_or_code: str, new_password: str):
        """
        Handles Forgot Password step 2:
        Verifies token or code, checks expiry, updates password_hash in transaction.
        """
        token_or_code = identifier_token_or_code.strip()
        new_hash = hash_password(new_password)
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT reset_id, user_id, expires_at, is_used
            FROM password_resets
            WHERE (reset_token = ? OR reset_code = ?)
            ORDER BY created_at DESC LIMIT 1
        """, (token_or_code, token_or_code))

        record = cursor.fetchone()
        if not record:
            conn.close()
            return {'success': False, 'message': 'Invalid verification code or reset token.'}

        if record['is_used'] == 1:
            conn.close()
            return {'success': False, 'message': 'This reset token has already been used.'}

        try:
            exp_time = datetime.strptime(record['expires_at'], '%Y-%m-%d %H:%M:%S')
            if datetime.now() > exp_time:
                conn.close()
                return {'success': False, 'message': 'Verification code has expired. Please request a new one.'}
        except Exception:
            pass

        try:
            cursor.execute("UPDATE users SET password_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?", (new_hash, record['user_id']))
            cursor.execute("UPDATE password_resets SET is_used = 1 WHERE reset_id = ?", (record['reset_id'],))
            conn.commit()
            conn.close()
            return {'success': True, 'message': 'Your password has been successfully reset. You may now log in.'}
        except Exception as e:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': f"Database error updating password: {str(e)}"}

    # -------------------------------------------------------------------------
    # Book Inventory / Product Management CRUD
    # -------------------------------------------------------------------------
    def create_book(self, data: dict):
        """Creates a new book with audit logging."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO books (isbn, title, subtitle, publisher_id, category_id, price, discount_pct, stock_qty, publication_year, page_count, language, cover_image, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['isbn'], data['title'], data.get('subtitle', ''),
                data.get('publisher_id', 1), data.get('category_id', 1),
                float(data.get('price', 650.00)), float(data.get('discount_pct', 0)),
                int(data.get('stock_qty', 10)), int(data.get('publication_year', 2024)),
                int(data.get('page_count', 300)), data.get('language', 'English'),
                data.get('cover_image', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg'),
                data.get('description', '')
            ))
            book_id = cursor.lastrowid

            author_id = data.get('author_id', 1)
            cursor.execute("INSERT INTO book_authors (book_id, author_id, is_primary) VALUES (?, ?, 1)", (book_id, author_id))

            cursor.execute("INSERT INTO book_audit_log (book_id, action, changed_by, new_price, new_stock) VALUES (?, 'INSERT', 'Admin', ?, ?)",
                           (book_id, float(data.get('price', 650.00)), int(data.get('stock_qty', 10))))

            conn.commit()
            conn.close()
            return {'success': True, 'book_id': book_id, 'message': 'Book successfully added to catalog.'}
        except Exception as e:
            conn.close()
            return {'success': False, 'message': str(e)}

    def delete_book(self, book_id: int):
        """Soft-deletes a book maintaining order history integrity."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE books SET is_deleted = 1, updated_at = CURRENT_TIMESTAMP WHERE book_id = ?", (book_id,))
            cursor.execute("INSERT INTO book_audit_log (book_id, action, changed_by) VALUES (?, 'SOFT_DELETE', 'Admin')", (book_id,))
            conn.commit()
            conn.close()
            return {'success': True, 'message': f'Book #{book_id} archived from catalog.'}
        except Exception as e:
            conn.close()
            return {'success': False, 'message': str(e)}

    def update_book(self, book_id: int, data: dict):
        """Updates book metadata with transaction safety and audit logging. Supports partial updates like restock."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT * FROM books WHERE book_id = ? AND is_deleted = 0", (book_id,))
            existing = cursor.fetchone()
            if not existing:
                conn.close()
                return {'success': False, 'message': 'Book not found or has been archived.'}

            old_price = float(existing['price'])
            old_stock = int(existing['stock_qty'])
            new_price = float(data.get('price', old_price))
            if 'stock_add' in data:
                new_stock = old_stock + int(data['stock_add'])
            else:
                new_stock = int(data.get('stock_qty', old_stock))

            isbn = data.get('isbn', existing['isbn'])
            title = data.get('title', existing['title'])
            subtitle = data.get('subtitle', existing['subtitle'] or '')
            publisher_id = int(data.get('publisher_id', existing['publisher_id'] or 1))
            category_id = int(data.get('category_id', existing['category_id'] or 1))
            discount_pct = float(data.get('discount_pct', existing['discount_pct'] or 0))
            pub_year = int(data.get('publication_year', existing['publication_year'] or 2024))
            page_count = int(data.get('page_count', existing['page_count'] or 300))
            language = data.get('language', existing['language'] or 'English')
            cover_image = data.get('cover_image', existing['cover_image'] or '')
            description = data.get('description', existing['description'] or '')

            cursor.execute("""
                UPDATE books SET
                    isbn = ?,
                    title = ?,
                    subtitle = ?,
                    publisher_id = ?,
                    category_id = ?,
                    price = ?,
                    discount_pct = ?,
                    stock_qty = ?,
                    publication_year = ?,
                    page_count = ?,
                    language = ?,
                    cover_image = ?,
                    description = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE book_id = ?
            """, (
                isbn, title, subtitle,
                publisher_id, category_id,
                new_price, discount_pct,
                new_stock, pub_year,
                page_count, language,
                cover_image, description,
                book_id
            ))

            if 'author_id' in data and data['author_id']:
                cursor.execute("UPDATE book_authors SET author_id = ? WHERE book_id = ? AND is_primary = 1",
                               (int(data['author_id']), book_id))

            action_name = 'RESTOCK' if (old_stock != new_stock and old_price == new_price) else 'UPDATE'
            cursor.execute("""
                INSERT INTO book_audit_log (book_id, action, changed_by, old_price, new_price, old_stock, new_stock)
                VALUES (?, ?, 'Admin', ?, ?, ?, ?)
            """, (book_id, action_name, old_price, new_price, old_stock, new_stock))

            conn.commit()
            conn.close()
            return {'success': True, 'book_id': book_id, 'message': f'Book "{title}" updated successfully.'}
        except Exception as e:
            conn.rollback()
            conn.close()
            return {'success': False, 'message': str(e)}

    def update_order_status(self, order_id: int, new_status: str):
        """Updates the status of an order (Confirmed, On Transit, Delivered, Cancelled)."""
        valid_statuses = ['Confirmed', 'On Transit', 'Delivered', 'Cancelled']
        if new_status not in valid_statuses:
            return {'success': False, 'message': f"Invalid status '{new_status}'. Allowed: {', '.join(valid_statuses)}"}

        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT order_id, order_code FROM orders WHERE order_id = ?", (order_id,))
            order = cursor.fetchone()
            if not order:
                conn.close()
                return {'success': False, 'message': f'Order #{order_id} not found.'}

            cursor.execute("UPDATE orders SET order_status = ? WHERE order_id = ?",
                           (new_status, order_id))
            conn.commit()
            conn.close()
            return {
                'success': True,
                'order_id': order_id,
                'order_code': order['order_code'],
                'status': new_status,
                'message': f"Order #{order['order_code']} status changed to '{new_status}'."
            }
        except Exception as e:
            conn.close()
            return {'success': False, 'message': str(e)}
            conn.rollback()
            conn.close()
            return {'success': False, 'message': str(e)}

    def get_admin_dashboard_data(self):
        """Returns comprehensive catalog stats, recent orders, inventory alerts, and full books catalog."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Total Active Books
        cursor.execute("SELECT COUNT(*) AS total_books FROM books WHERE is_deleted = 0")
        total_books = cursor.fetchone()['total_books']

        # 2. Total Categories
        cursor.execute("SELECT COUNT(*) AS total_cats FROM categories")
        total_categories = cursor.fetchone()['total_cats']

        # 3. Inventory Alerts (Strictly Low Stock <= 20 threshold)
        cursor.execute("SELECT COUNT(*) AS low_stock_count FROM books WHERE is_deleted = 0 AND stock_qty <= 20")
        low_stock_count = cursor.fetchone()['low_stock_count']

        # 4. Total Orders & Revenue
        cursor.execute("SELECT COUNT(*) AS total_orders, COALESCE(SUM(total_amount), 0) AS total_revenue FROM orders")
        order_stats = cursor.fetchone()
        total_orders = order_stats['total_orders']
        total_revenue = round(order_stats['total_revenue'], 2)

        # 5. Recent Orders (Latest 10)
        cursor.execute("""
            SELECT order_id, order_code, customer_name, customer_phone, delivery_address,
                   district, payment_method, payment_status, order_status, total_amount,
                   COALESCE(transaction_id, '') AS transaction_id, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_orders = [dict(r) for r in cursor.fetchall()]

        # 6. Low stock items (Strictly <= 20 units; ignore items > 20)
        cursor.execute("""
            SELECT b.book_id, b.isbn, b.title, b.stock_qty, b.price, b.cover_image, c.name AS category_name,
                   COALESCE(GROUP_CONCAT(DISTINCT a.name), 'Unknown') AS authors
            FROM books b
            INNER JOIN categories c ON b.category_id = c.category_id
            LEFT JOIN book_authors ba ON b.book_id = ba.book_id
            LEFT JOIN authors a ON ba.author_id = a.author_id
            WHERE b.is_deleted = 0 AND b.stock_qty <= 20
            GROUP BY b.book_id
            ORDER BY b.stock_qty ASC
            LIMIT 15
        """)
        low_stock_items = [dict(r) for r in cursor.fetchall()]

        # 7. All Books with details for Admin Table
        cursor.execute("""
            SELECT 
                b.book_id, b.isbn, b.title, b.subtitle, b.price, b.discount_pct,
                ROUND(b.price * (1.0 - (b.discount_pct / 100.0)), 2) AS effective_price,
                b.stock_qty, b.publication_year, b.page_count, b.language, b.cover_image, b.description,
                b.category_id, b.publisher_id,
                c.name AS category_name, p.name AS publisher_name,
                COALESCE(GROUP_CONCAT(DISTINCT a.name), 'Unknown') AS author_names,
                ba.author_id AS primary_author_id
            FROM books b
            INNER JOIN categories c ON b.category_id = c.category_id
            LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
            LEFT JOIN book_authors ba ON b.book_id = ba.book_id AND ba.is_primary = 1
            LEFT JOIN authors a ON ba.author_id = a.author_id
            WHERE b.is_deleted = 0
            GROUP BY b.book_id
            ORDER BY b.book_id DESC
        """)
        all_books = [dict(r) for r in cursor.fetchall()]

        # 8. Active Password Resets (Auditing & Admin Verification)
        cursor.execute("""
            SELECT r.reset_id, r.user_id, u.email, u.full_name, r.reset_code, r.expires_at, r.is_used, r.created_at
            FROM password_resets r
            INNER JOIN users u ON r.user_id = u.user_id
            WHERE r.is_used = 0
            ORDER BY r.created_at DESC
            LIMIT 5
        """)
        active_resets = [dict(r) for r in cursor.fetchall()]

        # 9. Recent Customer Queries
        cursor.execute("""
            SELECT query_id, customer_name, customer_email, customer_phone, topic, message, status, created_at
            FROM customer_queries
            ORDER BY created_at DESC
            LIMIT 15
        """)
        recent_queries = [dict(r) for r in cursor.fetchall()]

        conn.close()
        return {
            'metrics': {
                'total_books': total_books,
                'total_categories': total_categories,
                'low_stock_count': low_stock_count,
                'total_orders': total_orders,
                'total_revenue': total_revenue,
                'engine': self.mode
            },
            'recent_orders': recent_orders,
            'low_stock_items': low_stock_items,
            'books': all_books,
            'active_resets': active_resets,
            'recent_queries': recent_queries
        }

    def create_customer_query(self, data: dict):
        """Records a new customer inquiry submitted via the support floating widget."""
        conn = self._get_connection()
        cursor = conn.cursor()

        name = (data.get('name') or data.get('customer_name') or '').strip()
        email = (data.get('email') or data.get('customer_email') or '').strip()
        phone = (data.get('phone') or data.get('customer_phone') or '').strip()
        topic = (data.get('topic') or '').strip()
        message = (data.get('message') or '').strip()

        if self.mode == 'MYSQL':
            cursor.execute("""
                INSERT INTO customer_queries (customer_name, customer_email, customer_phone, topic, message)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, email, phone, topic, message))
            query_id = cursor.lastrowid
        else:
            cursor.execute("""
                INSERT INTO customer_queries (customer_name, customer_email, customer_phone, topic, message)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, topic, message))
            query_id = cursor.lastrowid

        conn.commit()
        conn.close()
        return {
            'query_id': query_id,
            'customer_name': name,
            'customer_email': email,
            'customer_phone': phone,
            'topic': topic,
            'message': message,
            'status': 'New'
        }


db = DatabaseAdapter()
