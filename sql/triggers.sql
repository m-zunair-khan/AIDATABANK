-- ============================================================
-- AI MODEL REGISTRY — Database Triggers
-- Project : AI Model Registry
-- Engine  : MySQL 8.x (InnoDB) on Aiven Cloud
-- Contents: 3 Triggers for data validation and automation
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  1. trg_validate_pricing
--     BEFORE INSERT on pricing_history
--     Ensures both price columns are non-negative.
-- ────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS trg_validate_pricing;

DELIMITER //
CREATE TRIGGER trg_validate_pricing
BEFORE INSERT ON pricing_history
FOR EACH ROW
BEGIN
    IF NEW.input_price_per_1m_tokens < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Input price per 1M tokens cannot be negative.';
    END IF;

    IF NEW.output_price_per_1m_tokens < 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Output price per 1M tokens cannot be negative.';
    END IF;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  2. trg_review_rating_check
--     BEFORE INSERT on user_reviews
--     Validates rating range (1-5) and auto-trims whitespace
--     from reviewer_name.
-- ────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS trg_review_rating_check;

DELIMITER //
CREATE TRIGGER trg_review_rating_check
BEFORE INSERT ON user_reviews
FOR EACH ROW
BEGIN
    -- Auto-trim whitespace from reviewer name
    SET NEW.reviewer_name = TRIM(NEW.reviewer_name);

    -- Validate rating range (redundant with CHECK but good practice)
    IF NEW.rating < 1 OR NEW.rating > 5 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Rating must be between 1 and 5.';
    END IF;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  3. trg_error_resolve_timestamp
--     BEFORE UPDATE on error_reports
--     Auto-sets resolved_at = NOW() when status changes to
--     'resolved' or 'wont_fix'.
-- ────────────────────────────────────────────────────────────
DROP TRIGGER IF EXISTS trg_error_resolve_timestamp;

DELIMITER //
CREATE TRIGGER trg_error_resolve_timestamp
BEFORE UPDATE ON error_reports
FOR EACH ROW
BEGIN
    IF NEW.status IN ('resolved', 'wont_fix')
       AND (OLD.status NOT IN ('resolved', 'wont_fix') OR OLD.status IS NULL) THEN
        SET NEW.resolved_at = NOW();
    END IF;
END //
DELIMITER ;

-- ============================================================
--  End of Triggers — 3 triggers created
-- ============================================================
