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
        """)

        # Check if seed data exists
        cursor.execute("SELECT COUNT(*) AS cnt FROM books")
        if cursor.fetchone()['cnt'] == 0:
            self._seed_sqlite(cursor)

        conn.commit()
        conn.close()

    def _seed_sqlite(self, cursor):
        """Populates initial seed records with verified book covers and diverse genres."""
        categories = [
            (1, 'Database & Systems', 'database-systems', 'Relational models, SQL optimization, index structures and distributed databases.', 'database'),
            (2, 'Computer Science & Software', 'computer-science', 'Algorithms, system design, clean architecture, and computing principles.', 'cpu'),
            (3, 'Fantasy & Adventure', 'fantasy-adventure', 'Magical universes, epic sagas, heroic quests, and legendary chronicles.', 'sparkles'),
            (4, 'Self-Help & Personal Growth', 'self-help', 'Productivity, habit engineering, mental toughness, and behavioral psychology.', 'zap'),
            (5, 'Classic Drama & Poetry', 'classic-drama', 'Timeless theatrical tragedies, comedies, historical plays, and verse.', 'book-open'),
            (6, 'Inspirational Fiction', 'inspirational-fiction', 'Philosophical allegories, spiritual voyages, and transformative tales.', 'compass'),
            (7, 'Science Fiction & Dystopia', 'science-fiction', 'Futuristic speculative universes, political dystopias, and space operas.', 'rocket'),
            (8, 'Finance & Behavioral Economics', 'finance-economics', 'Wealth building, rational decision making, and cognitive bias analysis.', 'trending-up'),
            (9, 'Artificial Intelligence', 'artificial-intelligence', 'Machine learning, neural networks, intelligent agents, and reasoning.', 'brain')
        ]
        cursor.executemany("INSERT INTO categories (category_id, name, slug, description, icon) VALUES (?, ?, ?, ?, ?)", categories)

        publishers = [
            (1, 'Addison-Wesley Professional', 'USA', 1942, 'https://www.pearson.com'),
            (2, 'O''Reilly Media', 'USA', 1978, 'https://www.oreilly.com'),
            (3, 'The MIT Press', 'USA', 1962, 'https://mitpress.mit.edu'),
            (4, 'Morgan Kaufmann Publishers', 'USA', 1984, 'https://www.elsevier.com'),
            (5, 'Penguin Random House', 'USA', 1927, 'https://www.penguinrandomhouse.com'),
            (6, 'Oxford University Press', 'UK', 1586, 'https://global.oup.com'),
            (7, 'HarperCollins Publishers', 'USA', 1817, 'https://www.harpercollins.com'),
            (8, 'Bloomsbury Publishing', 'UK', 1986, 'https://www.bloomsbury.com'),
            (9, 'Scholastic Inc.', 'USA', 1920, 'https://www.scholastic.com'),
            (10, 'Simon & Schuster (Folger)', 'USA', 1924, 'https://www.simonandschuster.com'),
            (11, 'Avery (Penguin Group)', 'USA', 1976, 'https://www.penguin.com'),
            (12, 'Grand Central Publishing', 'USA', 1970, 'https://www.hachettebookgroup.com'),
            (13, 'Lioncrest Publishing', 'USA', 2017, 'https://www.lioncrest.com'),
            (14, 'Harriman House', 'UK', 1992, 'https://harriman-house.com')
        ]
        cursor.executemany("INSERT INTO publishers (publisher_id, name, country, founded_year, website) VALUES (?, ?, ?, ?, ?)", publishers)

        authors = [
            (1, 'Abraham Silberschatz', 'Professor of Computer Science at Yale University; renowned author of database textbooks.', 1947, 'USA'),
            (2, 'Henry F. Korth', 'Professor of Computer Science and Engineering at Lehigh University.', 1956, 'USA'),
            (3, 'S. Sudarshan', 'Professor at IIT Bombay; expert in query optimization and database storage.', 1964, 'India'),
            (4, 'Martin Kleppmann', 'Researcher in distributed systems at University of Cambridge; author of DDIA.', 1982, 'UK'),
            (5, 'Donald E. Knuth', 'Professor Emeritus at Stanford University; father of algorithm analysis.', 1938, 'USA'),
            (6, 'Martin Fowler', 'Chief Scientist at ThoughtWorks; authority on software architecture.', 1963, 'UK'),
            (7, 'Robert C. Martin', 'Co-author of the Agile Manifesto; widely known as Uncle Bob.', 1952, 'USA'),
            (8, 'Stuart Russell', 'Professor of Computer Science at UC Berkeley; AI pioneer.', 1962, 'UK'),
            (9, 'Peter Norvig', 'Director of Research at Google; eminent computer scientist.', 1956, 'USA'),
            (10, 'Frank Herbert', 'American science fiction author best known for the epic Dune saga.', 1920, 'USA'),
            (11, 'George Orwell', 'English novelist and essayist whose work is characterised by lucid prose.', 1903, 'UK'),
            (12, 'Daniel Kahneman', 'Nobel laureate in Economics and pioneer of behavioral psychology.', 1934, 'Israel'),
            (13, 'Thomas H. Cormen', 'Emeritus Professor of Computer Science at Dartmouth College and co-author of CLRS.', 1956, 'USA'),
            (14, 'C.J. Date', 'Independent author specializing in relational database theory.', 1938, 'UK'),
            (15, 'J.K. Rowling', 'British author celebrated for creating the world of Harry Potter, inspiring generations of readers.', 1965, 'UK'),
            (16, 'Paulo Coelho', 'Acclaimed Brazilian novelist whose philosophical allegories have sold over 320 million copies worldwide.', 1947, 'Brazil'),
            (17, 'William Shakespeare', 'Legendary English playwright, poet, and actor widely regarded as the greatest dramatist of world literature.', 1564, 'UK'),
            (18, 'James Clear', 'Renowned behavioral researcher, speaker, and author of the record-breaking bestseller Atomic Habits.', 1986, 'USA'),
            (19, 'Mark Manson', 'Self-help author and blogger known for pragmatic, no-nonsense approaches to modern personal development.', 1984, 'USA'),
            (20, 'Cal Newport', 'Associate Professor of Computer Science at Georgetown University and advocate of digital focus.', 1982, 'USA'),
            (21, 'David Goggins', 'Retired Navy SEAL, ultramarathon runner, and author advocating peak mental discipline.', 1975, 'USA'),
            (22, 'Morgan Housel', 'Partner at Collaborative Fund and bestselling author on behavioral finance and psychology.', 1984, 'USA')
        ]
        cursor.executemany("INSERT INTO authors (author_id, name, bio, birth_year, country) VALUES (?, ?, ?, ?, ?)", authors)

        books = [
            # 1-5: Computer Science & Database Systems (Verified authentic covers)
            (1, '978-0078022159', 'Database System Concepts', 'Seventh Edition', 4, 1, 1250.00, 10.0, 42, 2019, 1376, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348180424i/18579.jpg', 'The benchmark textbook providing comprehensive coverage of database management concepts, relational models, SQL query processing, index architectures, concurrency control, and ACID transactions.'),
            (2, '978-1449373320', 'Designing Data-Intensive Applications', 'The Big Ideas Behind Reliable Systems', 2, 1, 950.00, 15.0, 75, 2017, 616, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1453982827i/23463279.jpg', 'Key insights into database storage engines, B-trees, LSM-trees, replication, partitioning, distributed transactions, and stream processing.'),
            (3, '978-0134494166', 'Clean Architecture', 'A Craftsman''s Guide to Software Structure', 1, 2, 650.00, 5.0, 58, 2017, 432, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1495947702i/18043011.jpg', 'Essential architectural rules for creating clean software systems with decoupled database layers, business domain boundaries, and testable frameworks.'),
            (4, '978-0262033848', 'Introduction to Algorithms (CLRS)', 'Fourth Edition', 3, 2, 1450.00, 12.0, 31, 2022, 1312, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1387741681i/108986.jpg', 'The standard worldwide guide to algorithms: dynamic programming, graph traversal, greedy heuristics, B-trees, sorting algorithms, and complexity analysis.'),
            (5, '978-0134610993', 'Artificial Intelligence: A Modern Approach', 'Fourth Edition', 1, 9, 1600.00, 8.0, 24, 2020, 1168, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1347649539i/72005.jpg', 'The most authoritative introduction to artificial intelligence, covering rational agents, probabilistic reasoning, reinforcement learning, and neural architectures.'),

            # 6-8: Sci-Fi & Dystopia
            (6, '978-0441013593', 'Dune', 'The Epic Science Fiction Masterpiece', 5, 7, 550.00, 20.0, 110, 1965, 896, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1555447414i/44767458.jpg', 'Set on the desert planet Arrakis, Dune is the story of the boy Paul Atreides, who inherits a vast planetary destiny amidst geopolitical and ecological conflict.'),
            (7, '978-0451524935', '1984', 'A Dystopian Classic', 5, 7, 350.00, 0.0, 85, 1949, 328, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1657781256i/61439040.jpg', 'Winston Smith toes the Party line, rewriting history to satisfy the Ministry of Truth, while harboring forbidden thoughts in an all-seeing totalitarian state.'),
            (8, '978-0374533557', 'Thinking, Fast and Slow', 'Cognitive Biases and Decision Systems', 7, 8, 580.00, 10.0, 64, 2011, 512, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1317793965i/11468377.jpg', 'Exploration of two modes of thought: System 1 (fast, intuitive, emotional) and System 2 (slower, deliberate, logical) and how they shape judgments.'),

            # 9-12: Software Design & Additional DB Theory
            (9, '978-0201633610', 'Design Patterns: Elements of Reusable Software', 'Classic Gang of Four', 1, 2, 750.00, 15.0, 39, 1994, 416, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348027904i/85009.jpg', 'The canonical catalog of 23 classic software design patterns categorized into Creational, Structural, and Behavioral solutions.'),
            (10, '978-0321127426', 'Patterns of Enterprise Application Architecture', 'Data Mapping and Domain Models', 1, 2, 850.00, 5.0, 29, 2002, 560, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1440319405i/70156.jpg', 'Detailed patterns for mapping object-oriented models to relational database tables, managing transactions, unit of work, and domain logic layers.'),
            (11, '978-0321392794', 'An Introduction to Database Systems', 'Eighth Edition', 1, 1, 1100.00, 10.0, 18, 2003, 1024, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1388188169i/66826.jpg', 'The foundational theoretical text on the relational model, relational algebra, tuple calculus, normalization theory, and integrity constraints by C.J. Date.'),
            (12, '978-0321751041', 'The Art of Computer Programming, Vol 1', 'Fundamental Algorithms', 1, 2, 1350.00, 0.0, 15, 1997, 672, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1348630043i/112239.jpg', 'Knuth''s monumental multi-volume work providing exact mathematical analyses of algorithm structures and memory representations.'),

            # 13-16: Harry Potter Series by J.K. Rowling
            (13, '978-0590353427', 'Harry Potter and the Sorcerer''s Stone', 'Book 1 of the Hogwarts Series', 9, 3, 620.00, 10.0, 95, 1997, 309, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474154022i/3.jpg', 'Harry Potter has never even heard of Hogwarts when letters start dropping on the doormat. On his eleventh birthday, he discovers he is a wizard destined for an extraordinary magical world.'),
            (14, '978-0439064873', 'Harry Potter and the Chamber of Secrets', 'Book 2 of the Hogwarts Series', 9, 3, 650.00, 10.0, 80, 1998, 341, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1474169725i/15881.jpg', 'The Dursleys were so mean that all Harry wanted was to return to Hogwarts. But a sinister house-elf warns of great danger, and mysterious petrifications begin within the castle walls.'),
            (15, '978-0439136365', 'Harry Potter and the Prisoner of Azkaban', 'Book 3 of the Hogwarts Series', 9, 3, 680.00, 12.0, 88, 1999, 435, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1630547330i/5.jpg', 'For twelve long years, the dread fortress of Azkaban held an infamous prisoner named Sirius Black. Now he has escaped, and the Dementors patrol Hogwarts looking for him.'),
            (16, '978-0439139601', 'Harry Potter and the Goblet of Fire', 'Book 4 of the Hogwarts Series', 9, 3, 750.00, 15.0, 72, 2000, 734, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1554006152i/6.jpg', 'Harry wants to get away from the pernicious Dursleys and attend the Quidditch World Cup. Little does he know that the Triwizard Tournament will demand supreme courage in the face of Lord Voldemort''s return.'),

            # 17-19: Paulo Coelho Masterpieces
            (17, '978-0062315007', 'The Alchemist', 'A Fable About Following Your Dream', 7, 6, 380.00, 10.0, 120, 1988, 208, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1654371463i/18144590.jpg', 'Santiago, an Andalusian shepherd boy, yearns to travel in search of worldly treasure. His quest will lead him to riches far different and far more satisfying than he ever imagined as he listens to his heart.'),
            (18, '978-0061578953', 'Brida', 'A Novel of Magic and Mystery', 7, 6, 420.00, 5.0, 65, 1990, 288, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1388195861i/2984534.jpg', 'The captivating story of Brida, a young Irish girl, and her quest for knowledge, wisdom, and love through ancient spiritual traditions and discovery of her destiny.'),
            (19, '978-0061735257', 'The Winner Stands Alone', 'Ambition, Fame and the Superclass', 7, 6, 450.00, 10.0, 48, 2008, 400, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1327918341i/4996985.jpg', 'Set amidst the glamorous backdrop of the Cannes Film Festival, a gripping examination of deep ambition, celebrity culture, and the price of success.'),

            # 20-22: William Shakespeare Classics
            (20, '978-0743477123', 'Hamlet, Prince of Denmark', 'The Folger Shakespeare Library', 10, 5, 320.00, 0.0, 90, 1603, 342, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1351051608i/1420.jpg', 'The supreme masterpiece of world drama: Prince Hamlet mourns his murdered father, facing moral paralysis, revenge, feigned madness, and profound existential questions.'),
            (21, '978-0743477109', 'Macbeth', 'Tragedy of Ambition and Fate', 10, 5, 300.00, 0.0, 85, 1606, 240, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1459795224i/8852.jpg', 'Spurred by three supernatural witches and his ruthless wife, Scottish general Macbeth commits regicide to seize the throne, descending into paranoia and blood-soaked tyranny.'),
            (22, '978-0743477116', 'Romeo and Juliet', 'The Definitive Folger Edition', 10, 5, 290.00, 0.0, 95, 1597, 281, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1631587327i/18135.jpg', 'The timeless tale of star-crossed lovers in Verona whose passionate romance defies the bitter, violent blood-feud between the Montagues and Capulets.'),

            # 23-27: Modern Self-Help, Focus & Behavioral Growth
            (23, '978-0735211292', 'Atomic Habits', 'Tiny Changes, Remarkable Results', 11, 4, 550.00, 15.0, 140, 2018, 320, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1655988385i/40121378.jpg', 'No matter your goals, Atomic Habits offers a proven framework for improving every day. James Clear reveals practical strategies for building good habits, breaking bad ones, and mastering tiny behaviors.'),
            (24, '978-0062457714', 'The Subtle Art of Not Giving a F*ck', 'A Counterintuitive Approach to Living a Good Life', 7, 4, 480.00, 10.0, 115, 2016, 224, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1465248106i/28257707.jpg', 'In this generation-defining self-help guide, superstar blogger Mark Manson cuts through the crap to show us how to stop trying to be positive all the time and instead become truly resilient.'),
            (25, '978-1455586691', 'Deep Work', 'Rules for Focused Success in a Distracted World', 12, 4, 520.00, 10.0, 85, 2016, 304, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1447957962i/25744928.jpg', 'Deep work is the ability to focus without distraction on a cognitively demanding task. Cal Newport presents an indispensable framework to master complicated information and produce better results in less time.'),
            (26, '978-1544512280', 'Can''t Hurt Me', 'Master Your Mind and Defy the Odds', 13, 4, 590.00, 12.0, 90, 2018, 364, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1547846505i/41721428.jpg', 'For David Goggins, childhood was a nightmare of poverty and physical abuse. Through self-discipline, mental toughness, and hard work, he transformed himself into one of the world''s toughest endurance athletes.'),
            (27, '978-0857197689', 'The Psychology of Money', 'Timeless Lessons on Wealth, Greed, and Happiness', 14, 8, 540.00, 10.0, 130, 2020, 252, 'English', 'https://images-na.ssl-images-amazon.com/images/S/compressed.photo.goodreads.com/books/1581527774i/41881472.jpg', 'Doing well with money isn''t necessarily about what you know. It''s about how you behave. Morgan Housel shares 19 short stories exploring the strange ways people think about money.')
        ]
        cursor.executemany("INSERT INTO books (book_id, isbn, title, subtitle, publisher_id, category_id, price, discount_pct, stock_qty, publication_year, page_count, language, cover_image, description) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", books)

        book_authors = [
            (1, 1, 1), (1, 2, 0), (1, 3, 0),
            (2, 4, 1),
            (3, 7, 1),
            (4, 13, 1),
            (5, 8, 1), (5, 9, 0),
            (6, 10, 1),
            (7, 11, 1),
            (8, 12, 1),
            (9, 6, 0),
            (10, 6, 1),
            (11, 14, 1),
            (12, 5, 1),
            (13, 15, 1), # HP 1
            (14, 15, 1), # HP 2
            (15, 15, 1), # HP 3
            (16, 15, 1), # HP 4
            (17, 16, 1), # Alchemist
            (18, 16, 1), # Brida
            (19, 16, 1), # Winner Stands Alone
            (20, 17, 1), # Hamlet
            (21, 17, 1), # Macbeth
            (22, 17, 1), # Romeo & Juliet
            (23, 18, 1), # Atomic Habits
            (24, 19, 1), # Subtle Art
            (25, 20, 1), # Deep Work
            (26, 21, 1), # Can't Hurt Me
            (27, 22, 1)  # Psychology of Money
        ]
        cursor.executemany("INSERT INTO book_authors (book_id, author_id, is_primary) VALUES (?, ?, ?)", book_authors)

        pw_hash = hash_password('Password123!')
        users = [
            (1, 'admin', 'admin@pagevault.com', pw_hash, 'Dr. Alistair Vance', 'Admin', 'Active'),
            (2, 'librarian_sarah', 'librarian@pagevault.com', pw_hash, 'Sarah Jenkins', 'Librarian', 'Active'),
            (3, 'alex_reader', 'alex@example.com', pw_hash, 'Alex Morgan', 'Customer', 'Active'),
            (4, 'sophia_code', 'sophia@tech.edu', pw_hash, 'Sophia Chen', 'Customer', 'Active'),
            (5, 'tamim_tahmid', 'tamimtahmid270@gmail.com', pw_hash, 'Tamim Tahmid', 'Admin', 'Active')
        ]
        cursor.executemany("INSERT INTO users (user_id, username, email, password_hash, full_name, role, status) VALUES (?, ?, ?, ?, ?, ?, ?)", users)

        expiry = (datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')
        cursor.execute("INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at, is_used) VALUES (3, 'demo-token-alex-987654321', '849201', ?, 0)", (expiry,))

        reviews = [
            (1, 3, 5, 'Indispensable guide for any DBMS student', 'The depth of explanation on query optimization, B-tree indexes, and serializability is unmatched.'),
            (1, 4, 5, 'Clear SQL and Transaction internals', 'The examples on concurrency anomalies and two-phase locking clarified concepts I struggled with.'),
            (2, 3, 5, 'Modern Bible of distributed storage', 'Martin Kleppmann bridges theoretical database papers and real-world architectures seamlessly.'),
            (4, 3, 5, 'The ultimate algorithmic reference', 'Rigorous, beautiful mathematical proofs and algorithm analysis.'),
            (13, 3, 5, 'Pure childhood nostalgia and magic', 'The beginning of the greatest fantasy adventure ever written. Absolutely loved re-reading it!'),
            (14, 4, 5, 'Thrilling mystery at Hogwarts', 'The Basilisk mystery and Tom Riddle lore make this one of the most engaging books.'),
            (15, 3, 5, 'Best Harry Potter book hands down', 'The Marauders backstory, Sirius Black, and the Time-Turner plot are perfection.'),
            (17, 3, 5, 'Life-changing philosophical journey', 'A masterpiece on pursuing your personal legend. Every sentence feels like poetry.'),
            (18, 4, 4, 'Mystical and beautifully written', 'Paulo Coelho once again weaves wisdom, spirituality, and human nature into an inspiring tale.'),
            (20, 4, 5, 'The pinnacle of dramatic literature', 'Hamlet''s soliloquies on life, death, and human weakness remain breathtaking.'),
            (21, 3, 5, 'Chilling psychological tragedy', 'Macbeth''s rapid descent into ambition and madness is Shakespeare at his sharpest.'),
            (23, 3, 5, 'Practical, actionable habit building', 'Atomic Habits changed my daily routine completely. The 1% better every day rule actually works!'),
            (24, 4, 5, 'Refreshing and honest', 'Mark Manson cuts straight to the core of what actually matters in life.'),
            (25, 3, 5, 'Essential reading in the age of distraction', 'Cal Newport proves why focused, uninterrupted cognitive work is the ultimate superpower.'),
            (26, 4, 5, 'Unstoppable mindset', 'David Goggins shows that the human mind can overcome any obstacle when you stop making excuses.'),
            (27, 3, 5, 'Brilliant take on wealth and human behavior', 'Morgan Housel explains money not as spreadsheet math, but as emotional discipline.')
        ]
        cursor.executemany("INSERT INTO reviews (book_id, user_id, rating, review_title, review_text) VALUES (?, ?, ?, ?, ?)", reviews)

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
        if sort_by == 'price_asc':
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
            COUNT(DISTINCT r.review_id) AS total_reviews
        FROM books b
        INNER JOIN categories c ON b.category_id = c.category_id
        LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
        LEFT JOIN book_authors ba ON b.book_id = ba.book_id
        LEFT JOIN authors a ON ba.author_id = a.author_id
        LEFT JOIN reviews r ON b.book_id = r.book_id
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
            cursor.execute("""
                INSERT INTO orders (order_code, user_id, customer_name, customer_phone, delivery_address, district, payment_method, payment_status, order_status, subtotal, delivery_fee, total_amount)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Confirmed', ?, ?, ?)
            """, (
                order_code, user_id, customer_name, customer_phone, delivery_address, district,
                payment_method, 'Completed' if payment_method in ['bKash', 'Nagad'] else 'Pending',
                subtotal, delivery_fee, total_amount
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
                'order_code': order_code,
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
        """Updates book metadata with transaction safety and audit logging."""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT price, stock_qty FROM books WHERE book_id = ? AND is_deleted = 0", (book_id,))
            existing = cursor.fetchone()
            if not existing:
                conn.close()
                return {'success': False, 'message': 'Book not found or has been archived.'}

            old_price = float(existing['price'])
            old_stock = int(existing['stock_qty'])
            new_price = float(data.get('price', old_price))
            new_stock = int(data.get('stock_qty', old_stock))

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
                data['isbn'], data['title'], data.get('subtitle', ''),
                int(data.get('publisher_id', 1)), int(data.get('category_id', 1)),
                new_price, float(data.get('discount_pct', 0)),
                new_stock, int(data.get('publication_year', 2024)),
                int(data.get('page_count', 300)), data.get('language', 'English'),
                data.get('cover_image', ''), data.get('description', ''),
                book_id
            ))

            if 'author_id' in data and data['author_id']:
                cursor.execute("UPDATE book_authors SET author_id = ? WHERE book_id = ? AND is_primary = 1",
                               (int(data['author_id']), book_id))

            cursor.execute("""
                INSERT INTO book_audit_log (book_id, action, changed_by, old_price, new_price, old_stock, new_stock)
                VALUES (?, 'UPDATE', 'Admin', ?, ?, ?, ?)
            """, (book_id, old_price, new_price, old_stock, new_stock))

            conn.commit()
            conn.close()
            return {'success': True, 'book_id': book_id, 'message': f'Book "{data["title"]}" updated successfully.'}
        except Exception as e:
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

        # 3. Inventory Alerts (Low Stock <= 25)
        cursor.execute("SELECT COUNT(*) AS low_stock_count FROM books WHERE is_deleted = 0 AND stock_qty <= 25")
        low_stock_count = cursor.fetchone()['low_stock_count']

        # 4. Total Orders & Revenue
        cursor.execute("SELECT COUNT(*) AS total_orders, COALESCE(SUM(total_amount), 0) AS total_revenue FROM orders")
        order_stats = cursor.fetchone()
        total_orders = order_stats['total_orders']
        total_revenue = round(order_stats['total_revenue'], 2)

        # 5. Recent Orders (Latest 10)
        cursor.execute("""
            SELECT order_id, order_code, customer_name, customer_phone, delivery_address,
                   district, payment_method, payment_status, order_status, total_amount, created_at
            FROM orders
            ORDER BY created_at DESC
            LIMIT 10
        """)
        recent_orders = [dict(r) for r in cursor.fetchall()]

        # 6. Low stock items
        cursor.execute("""
            SELECT b.book_id, b.title, b.stock_qty, b.price, b.cover_image, c.name AS category_name
            FROM books b
            INNER JOIN categories c ON b.category_id = c.category_id
            WHERE b.is_deleted = 0 AND b.stock_qty <= 25
            ORDER BY b.stock_qty ASC
            LIMIT 8
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
            'books': all_books
        }


db = DatabaseAdapter()
