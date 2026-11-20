-- =============================================================================
-- PageVault - MySQL EXPLAIN & Query Optimization Benchmark
-- DBMS Demonstration of Index Strategies & Relational Query Plans
-- =============================================================================
USE pagevault_db;

-- -----------------------------------------------------------------------------
-- Experiment 1: Primary Key / Unique Index Lookup vs Full Table Scan
-- -----------------------------------------------------------------------------
-- Query A: Fast Unique Index Lookup (O(log N))
-- Expected: type = 'const', key = 'uq_books_isbn', rows = 1
EXPLAIN ANALYZE
SELECT book_id, title, price 
FROM books 
WHERE isbn = '978-0078022159';

-- Query B: Non-indexed column search requires Full Table Scan (O(N))
-- Expected: type = 'ALL', possible_keys = NULL, rows = total_rows
EXPLAIN ANALYZE
SELECT book_id, title, price 
FROM books 
WHERE language = 'English';

-- -----------------------------------------------------------------------------
-- Experiment 2: B-Tree Range Scan with Composite Index
-- -----------------------------------------------------------------------------
-- Query: Filters on Category and Price Range (in BDT)
-- Uses composite index 'idx_books_cat_price'
-- Expected: type = 'range' / 'ref', key = 'idx_books_cat_price'
EXPLAIN ANALYZE
SELECT book_id, title, price, category_id
FROM books
WHERE category_id = 1 AND price BETWEEN 500.00 AND 1500.00;

-- -----------------------------------------------------------------------------
-- Experiment 3: Full-Text Index vs Wildcard LIKE '%pattern%'
-- -----------------------------------------------------------------------------
-- Query A: Wildcard LIKE (Cannot use standard B-Tree index due to leading '%')
-- Costly sequential character scanning on every row
EXPLAIN ANALYZE
SELECT book_id, title, description 
FROM books 
WHERE description LIKE '%distributed%';

-- Query B: MySQL Full-Text Search (Uses Inverted Index)
-- Expected: type = 'fulltext', key = 'ft_books_search'
EXPLAIN ANALYZE
SELECT book_id, title, description,
       MATCH(title, description) AGAINST('+database +concurrency' IN BOOLEAN MODE) AS score
FROM books 
WHERE MATCH(title, description) AGAINST('+database +concurrency' IN BOOLEAN MODE)
ORDER BY score DESC;

-- -----------------------------------------------------------------------------
-- Experiment 4: Multi-Table Relational JOIN with Aggregation
-- -----------------------------------------------------------------------------
-- Evaluates join order, foreign key indexes, and temporary table usage for GROUP BY
EXPLAIN ANALYZE
SELECT 
    b.title,
    c.name AS category,
    p.name AS publisher,
    ROUND(AVG(r.rating), 2) AS avg_rating,
    COUNT(r.review_id) AS review_count
FROM books b
INNER JOIN categories c ON b.category_id = c.category_id
LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
LEFT JOIN reviews r ON b.book_id = r.book_id
WHERE b.price < 1000.00
GROUP BY b.book_id, c.name, p.name
HAVING avg_rating >= 4.0
ORDER BY avg_rating DESC;
