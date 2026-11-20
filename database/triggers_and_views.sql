-- =============================================================================
-- PageVault - Views and Triggers (Advanced DBMS Concepts)
-- =============================================================================
USE pagevault_db;

-- -----------------------------------------------------------------------------
-- View 1: vw_BookFullCatalog
-- Pre-computed relational projection joining books, authors, categories, publishers & ratings
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_BookFullCatalog;
CREATE VIEW vw_BookFullCatalog AS
SELECT 
    b.book_id,
    b.isbn,
    b.title,
    b.subtitle,
    b.price,
    b.discount_pct,
    ROUND(b.price * (1 - (b.discount_pct / 100)), 2) AS effective_price,
    b.stock_qty,
    b.publication_year,
    b.language,
    b.cover_image,
    b.description,
    c.category_id,
    c.name AS category_name,
    p.publisher_id,
    p.name AS publisher_name,
    p.country AS publisher_country,
    COALESCE(GROUP_CONCAT(DISTINCT a.name ORDER BY ba.is_primary DESC, a.name SEPARATOR ', '), 'Unknown') AS authors,
    ROUND(COALESCE(AVG(r.rating), 0), 1) AS avg_rating,
    COUNT(DISTINCT r.review_id) AS total_reviews
FROM books b
LEFT JOIN categories c ON b.category_id = c.category_id
LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
LEFT JOIN book_authors ba ON b.book_id = ba.book_id
LEFT JOIN authors a ON ba.author_id = a.author_id
LEFT JOIN reviews r ON b.book_id = r.book_id
GROUP BY b.book_id, c.category_id, p.publisher_id;

-- -----------------------------------------------------------------------------
-- View 2: vw_CategoryAnalytics
-- Aggregate statistics per category (COUNT, AVG, SUM, MIN, MAX)
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_CategoryAnalytics;
CREATE VIEW vw_CategoryAnalytics AS
SELECT 
    c.category_id,
    c.name AS category_name,
    c.slug,
    COUNT(b.book_id) AS total_titles,
    COALESCE(SUM(b.stock_qty), 0) AS total_inventory_units,
    ROUND(COALESCE(AVG(b.price), 0), 2) AS avg_unit_price,
    MIN(b.price) AS lowest_price,
    MAX(b.price) AS highest_price
FROM categories c
LEFT JOIN books b ON c.category_id = b.category_id
GROUP BY c.category_id, c.name, c.slug;

-- -----------------------------------------------------------------------------
-- View 3: vw_LowStockAlerts
-- Materialized filtering for inventory management
-- -----------------------------------------------------------------------------
DROP VIEW IF EXISTS vw_LowStockAlerts;
CREATE VIEW vw_LowStockAlerts AS
SELECT 
    b.book_id,
    b.isbn,
    b.title,
    b.stock_qty,
    b.price,
    c.name AS category_name
FROM books b
JOIN categories c ON b.category_id = c.category_id
WHERE b.stock_qty <= 20
ORDER BY b.stock_qty ASC;

-- -----------------------------------------------------------------------------
-- Trigger 1: trg_audit_book_update
-- Automatically tracks modifications to pricing or inventory levels
-- -----------------------------------------------------------------------------
DELIMITER $$

DROP TRIGGER IF EXISTS trg_audit_book_update$$
CREATE TRIGGER trg_audit_book_update
AFTER UPDATE ON books
FOR EACH ROW
BEGIN
    IF (OLD.price <> NEW.price OR OLD.stock_qty <> NEW.stock_qty) THEN
        INSERT INTO book_audit_log (
            book_id,
            action,
            changed_by,
            old_price,
            new_price,
            old_stock,
            new_stock
        )
        VALUES (
            NEW.book_id,
            'UPDATE',
            CURRENT_USER(),
            OLD.price,
            NEW.price,
            OLD.stock_qty,
            NEW.stock_qty
        );
    END IF;
END$$

-- -----------------------------------------------------------------------------
-- Trigger 2: trg_audit_book_delete
-- -----------------------------------------------------------------------------
DROP TRIGGER IF EXISTS trg_audit_book_delete$$
CREATE TRIGGER trg_audit_book_delete
AFTER DELETE ON books
FOR EACH ROW
BEGIN
    INSERT INTO book_audit_log (
        book_id,
        action,
        changed_by,
        old_price,
        new_price,
        old_stock,
        new_stock
    )
    VALUES (
        OLD.book_id,
        'DELETE',
        CURRENT_USER(),
        OLD.price,
        NULL,
        OLD.stock_qty,
        NULL
    );
END$$

DELIMITER ;
