-- =============================================================================
-- PageVault - Online Bookshop & Book Management System
-- DBMS Course Project: Relational MySQL Schema (3NF Compliant)
-- =============================================================================

CREATE DATABASE IF NOT EXISTS pagevault_db
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE pagevault_db;

-- -----------------------------------------------------------------------------
-- 1. Table: Categories
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS categories;
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(50) DEFAULT 'book',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 2. Table: Publishers
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS publishers;
CREATE TABLE publishers (
    publisher_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    country VARCHAR(100) DEFAULT 'Unknown',
    founded_year INT,
    website VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_publisher_name (name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 3. Table: Authors
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS authors;
CREATE TABLE authors (
    author_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    bio TEXT,
    birth_year INT,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_author_name (name)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 4. Table: Books
-- Central entity with Normalized Foreign Keys and Multi-Column Indexes
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS books;
CREATE TABLE books (
    book_id INT AUTO_INCREMENT PRIMARY KEY,
    isbn VARCHAR(20) NOT NULL UNIQUE,
    title VARCHAR(255) NOT NULL,
    subtitle VARCHAR(255),
    publisher_id INT,
    category_id INT,
    price DECIMAL(10, 2) NOT NULL,
    discount_pct DECIMAL(5, 2) DEFAULT 0.00,
    stock_qty INT NOT NULL DEFAULT 0,
    publication_year INT,
    page_count INT,
    language VARCHAR(50) DEFAULT 'English',
    cover_image VARCHAR(500),
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints with Referential Actions
    CONSTRAINT fk_books_publisher
        FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT fk_books_category
        FOREIGN KEY (category_id) REFERENCES categories(category_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
        
    -- Single and Composite B-Tree Indexes for Fast Filtering & Sorting
    INDEX idx_books_price (price),
    INDEX idx_books_year (publication_year),
    INDEX idx_books_cat_price (category_id, price),
    INDEX idx_books_stock (stock_qty),
    
    -- FULLTEXT Index for Advanced MySQL Full-Text Search Queries
    FULLTEXT KEY ft_books_search (title, description)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 5. Table: Book_Authors (Many-to-Many Junction Table)
-- Resolves M:N relationship between Books and Authors (1st & 2nd NF)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS book_authors;
CREATE TABLE book_authors (
    book_id INT NOT NULL,
    author_id INT NOT NULL,
    is_primary BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (book_id, author_id),
    CONSTRAINT fk_ba_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ba_author
        FOREIGN KEY (author_id) REFERENCES authors(author_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_ba_author (author_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 6. Table: Users
-- Role-based authentication (Customer, Librarian, Admin)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS users;
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    role ENUM('Customer', 'Librarian', 'Admin') DEFAULT 'Customer',
    status ENUM('Active', 'Suspended', 'Pending') DEFAULT 'Active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_users_email (email),
    INDEX idx_users_role (role)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 7. Table: Password_Resets
-- Dedicated table for secure Forgot Password / Reset Token flow
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS password_resets;
CREATE TABLE password_resets (
    reset_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    reset_token VARCHAR(128) NOT NULL UNIQUE,
    reset_code VARCHAR(10) NOT NULL,
    expires_at DATETIME NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_resets_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_resets_token (reset_token),
    INDEX idx_resets_code (reset_code),
    INDEX idx_resets_expiry (expires_at)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 8. Table: Reviews
-- Relational feedback with check constraints and aggregate indexing
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS reviews;
CREATE TABLE reviews (
    review_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    user_id INT NOT NULL,
    rating TINYINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_title VARCHAR(150),
    review_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reviews_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    INDEX idx_reviews_book_rating (book_id, rating),
    INDEX idx_reviews_user (user_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 9. Table: Orders (E-Commerce Checkout & Fulfillment)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS order_items;
DROP TABLE IF EXISTS orders;
CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    order_code VARCHAR(50) NOT NULL UNIQUE,
    user_id INT,
    customer_name VARCHAR(150) NOT NULL,
    customer_phone VARCHAR(30) NOT NULL,
    delivery_address TEXT NOT NULL,
    district VARCHAR(60) NOT NULL DEFAULT 'Dhaka',
    payment_method ENUM('Cash on Delivery', 'bKash', 'Nagad', 'Card') NOT NULL DEFAULT 'Cash on Delivery',
    payment_status ENUM('Pending', 'Completed', 'Failed') NOT NULL DEFAULT 'Pending',
    order_status ENUM('Confirmed', 'Processing', 'Shipped', 'Delivered', 'Cancelled') NOT NULL DEFAULT 'Confirmed',
    subtotal DECIMAL(10, 2) NOT NULL,
    delivery_fee DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_orders_user
        FOREIGN KEY (user_id) REFERENCES users(user_id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_orders_code (order_code),
    INDEX idx_orders_customer_phone (customer_phone)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 10. Table: Order_Items (Relational Line Items)
-- -----------------------------------------------------------------------------
CREATE TABLE order_items (
    item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    book_id INT NOT NULL,
    quantity INT NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_oi_order
        FOREIGN KEY (order_id) REFERENCES orders(order_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_oi_book
        FOREIGN KEY (book_id) REFERENCES books(book_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_oi_order (order_id),
    INDEX idx_oi_book (book_id)
) ENGINE=InnoDB;

-- -----------------------------------------------------------------------------
-- 11. Table: Book_Audit_Log
-- Captures data modifications (Triggers demonstration)
-- -----------------------------------------------------------------------------
DROP TABLE IF EXISTS book_audit_log;
CREATE TABLE book_audit_log (
    log_id INT AUTO_INCREMENT PRIMARY KEY,
    book_id INT NOT NULL,
    action VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE, PURCHASE
    changed_by VARCHAR(80) DEFAULT 'System',
    old_price DECIMAL(10, 2),
    new_price DECIMAL(10, 2),
    old_stock INT,
    new_stock INT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
