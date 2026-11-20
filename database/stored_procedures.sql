-- =============================================================================
-- PageVault - Stored Procedures (DBMS SQL Routine Demonstration)
-- =============================================================================
USE pagevault_db;

DELIMITER $$

-- -----------------------------------------------------------------------------
-- Procedure 1: sp_SearchBooksAdvanced
-- Demonstrates Dynamic Relational Filtering, LEFT JOIN, Aggregation, and Pagination
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_SearchBooksAdvanced$$
CREATE PROCEDURE sp_SearchBooksAdvanced(
    IN p_search_term VARCHAR(255),
    IN p_category_id INT,
    IN p_min_price DECIMAL(10, 2),
    IN p_max_price DECIMAL(10, 2),
    IN p_min_rating DECIMAL(3, 2),
    IN p_in_stock_only BOOLEAN,
    IN p_sort_by VARCHAR(50),
    IN p_offset INT,
    IN p_limit INT
)
BEGIN
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
        b.cover_image,
        c.category_id,
        c.name AS category_name,
        p.publisher_id,
        p.name AS publisher_name,
        GROUP_CONCAT(DISTINCT a.name ORDER BY ba.is_primary DESC, a.name SEPARATOR ', ') AS author_names,
        ROUND(COALESCE(AVG(r.rating), 0), 1) AS avg_rating,
        COUNT(DISTINCT r.review_id) AS total_reviews
    FROM books b
    INNER JOIN categories c ON b.category_id = c.category_id
    LEFT JOIN publishers p ON b.publisher_id = p.publisher_id
    LEFT JOIN book_authors ba ON b.book_id = ba.book_id
    LEFT JOIN authors a ON ba.author_id = a.author_id
    LEFT JOIN reviews r ON b.book_id = r.book_id
    WHERE 
        -- Full-Text & Pattern Search Condition
        (
            p_search_term IS NULL OR p_search_term = ''
            OR MATCH(b.title, b.description) AGAINST(p_search_term IN BOOLEAN MODE)
            OR b.title LIKE CONCAT('%', p_search_term, '%')
            OR b.isbn LIKE CONCAT('%', p_search_term, '%')
            OR a.name LIKE CONCAT('%', p_search_term, '%')
        )
        -- Category Filter
        AND (p_category_id IS NULL OR p_category_id <= 0 OR b.category_id = p_category_id)
        -- Price Range Filter
        AND (p_min_price IS NULL OR b.price >= p_min_price)
        AND (p_max_price IS NULL OR b.price <= p_max_price)
        -- In Stock Only Toggle
        AND (p_in_stock_only IS FALSE OR b.stock_qty > 0)
    GROUP BY b.book_id, c.category_id, p.publisher_id
    HAVING 
        -- Aggregate Rating Threshold
        (p_min_rating IS NULL OR p_min_rating <= 0 OR avg_rating >= p_min_rating)
    ORDER BY
        CASE WHEN p_sort_by = 'price_asc' THEN effective_price END ASC,
        CASE WHEN p_sort_by = 'price_desc' THEN effective_price END DESC,
        CASE WHEN p_sort_by = 'rating_desc' THEN avg_rating END DESC,
        CASE WHEN p_sort_by = 'year_desc' THEN b.publication_year END DESC,
        CASE WHEN p_sort_by = 'title_asc' THEN b.title END ASC,
        b.book_id ASC
    LIMIT p_limit OFFSET p_offset;
END$$

-- -----------------------------------------------------------------------------
-- Procedure 2: sp_InitiatePasswordReset
-- Creates an expirable token and 6-digit code for the Forgot Password workflow
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_InitiatePasswordReset$$
CREATE PROCEDURE sp_InitiatePasswordReset(
    IN p_email VARCHAR(150),
    IN p_token VARCHAR(128),
    IN p_code VARCHAR(10),
    IN p_duration_minutes INT,
    OUT p_status_code INT,
    OUT p_message VARCHAR(255)
)
BEGIN
    DECLARE v_user_id INT DEFAULT NULL;
    
    -- Check if user exists
    SELECT user_id INTO v_user_id FROM users WHERE email = p_email LIMIT 1;
    
    IF v_user_id IS NULL THEN
        SET p_status_code = 404;
        SET p_message = 'No account associated with this email address.';
    ELSE
        -- Deactivate older pending tokens for this user
        UPDATE password_resets 
        SET is_used = TRUE 
        WHERE user_id = v_user_id AND is_used = FALSE;
        
        -- Insert new reset token record
        INSERT INTO password_resets (user_id, reset_token, reset_code, expires_at, is_used)
        VALUES (v_user_id, p_token, p_code, DATE_ADD(NOW(), INTERVAL p_duration_minutes MINUTE), FALSE);
        
        SET p_status_code = 200;
        SET p_message = 'Password reset code generated successfully.';
    END IF;
END$$

-- -----------------------------------------------------------------------------
-- Procedure 3: sp_CompletePasswordReset
-- Atomic password reset transaction verifying token validity and expiration
-- -----------------------------------------------------------------------------
DROP PROCEDURE IF EXISTS sp_CompletePasswordReset$$
CREATE PROCEDURE sp_CompletePasswordReset(
    IN p_token_or_code VARCHAR(128),
    IN p_new_password_hash VARCHAR(255),
    OUT p_status_code INT,
    OUT p_message VARCHAR(255)
)
proc_block: BEGIN
    DECLARE v_reset_id INT DEFAULT NULL;
    DECLARE v_user_id INT DEFAULT NULL;
    DECLARE v_expires_at DATETIME;
    DECLARE v_is_used BOOLEAN;
    
    -- Handlers for transaction integrity
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_status_code = 500;
        SET p_message = 'Database error during transaction execution.';
    END;

    START TRANSACTION;
    
    -- Find active token or code (locking row FOR UPDATE)
    SELECT reset_id, user_id, expires_at, is_used
    INTO v_reset_id, v_user_id, v_expires_at, v_is_used
    FROM password_resets
    WHERE (reset_token = p_token_or_code OR reset_code = p_token_or_code)
      AND is_used = FALSE
    ORDER BY created_at DESC
    LIMIT 1
    FOR UPDATE;
    
    IF v_reset_id IS NULL THEN
        ROLLBACK;
        SET p_status_code = 400;
        SET p_message = 'Invalid or expired password reset token.';
        LEAVE proc_block;
    END IF;
    
    IF NOW() > v_expires_at THEN
        ROLLBACK;
        SET p_status_code = 410;
        SET p_message = 'Password reset token has expired. Please request a new one.';
        LEAVE proc_block;
    END IF;
    
    -- Update the user's password
    UPDATE users 
    SET password_hash = p_new_password_hash, updated_at = NOW()
    WHERE user_id = v_user_id;
    
    -- Invalidate the token
    UPDATE password_resets
    SET is_used = TRUE
    WHERE reset_id = v_reset_id;
    
    COMMIT;
    SET p_status_code = 200;
    SET p_message = 'Password has been successfully updated.';
END proc_block$$

DELIMITER ;
