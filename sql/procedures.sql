-- ============================================================
-- AI MODEL REGISTRY — Stored Procedures
-- Project : AI Model Registry
-- Engine  : MySQL 8.x (InnoDB) on Aiven Cloud
-- Contents: 5 Stored Procedures for search, comparison,
--           ranking, recommendation, and reporting
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  1. sp_search_models
--     Search models by name (LIKE) with optional filters:
--       - free only
--       - minimum context length
--       - max price (input price per 1M tokens)
--       - required capability
-- ────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_search_models;

DELIMITER //
CREATE PROCEDURE sp_search_models(
    IN p_query        VARCHAR(200),
    IN p_free_only    BOOLEAN,
    IN p_min_context  INT,
    IN p_max_price    DECIMAL(12,4),
    IN p_capability   VARCHAR(100)
)
BEGIN
    SELECT
        mv.version_id,
        mv.version_name,
        mv.external_id,
        p.name                        AS provider_name,
        mf.name                       AS family_name,
        mv.release_date,
        mv.status,
        mv.context_length,
        mv.is_free,
        ph.input_price_per_1m_tokens  AS input_price,
        ph.output_price_per_1m_tokens AS output_price
    FROM model_versions mv
    JOIN model_families    mf ON mv.family_id   = mf.family_id
    JOIN providers         p  ON mf.provider_id = p.provider_id
    -- Latest pricing (left join so free models without pricing appear)
    LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
        AND ph.effective_date = (
            SELECT MAX(ph2.effective_date)
            FROM pricing_history ph2
            WHERE ph2.version_id = mv.version_id
        )
    WHERE
        -- Name search (match version name, family name, or external id)
        (p_query IS NULL OR p_query = ''
         OR mv.version_name LIKE CONCAT('%', p_query, '%')
         OR mf.name         LIKE CONCAT('%', p_query, '%')
         OR mv.external_id  LIKE CONCAT('%', p_query, '%'))
        -- Free only filter
        AND (p_free_only IS NULL OR p_free_only = FALSE
             OR mv.is_free = TRUE
             OR (ph.input_price_per_1m_tokens = 0 AND ph.output_price_per_1m_tokens = 0))
        -- Minimum context length filter
        AND (p_min_context IS NULL
             OR mv.context_length >= p_min_context)
        -- Max price filter (input price)
        AND (p_max_price IS NULL
             OR mv.is_free = TRUE
             OR ph.input_price_per_1m_tokens <= p_max_price)
        -- Capability filter
        AND (p_capability IS NULL OR p_capability = ''
             OR EXISTS (
                 SELECT 1
                 FROM model_capabilities mc
                 JOIN capabilities c ON mc.capability_id = c.capability_id
                 WHERE mc.version_id = mv.version_id
                   AND c.name = p_capability
             ))
    ORDER BY mv.version_name;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  2. sp_compare_models
--     Side-by-side comparison of two model versions.
--     Returns 2 result sets:
--       RS1 — basic info for both models
--       RS2 — benchmark scores for both models
-- ────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_compare_models;

DELIMITER //
CREATE PROCEDURE sp_compare_models(
    IN p_version_id_1 INT,
    IN p_version_id_2 INT
)
BEGIN
    -- Log the comparison
    INSERT INTO comparison_logs (version_id_1, version_id_2, comparison_criteria, created_at)
    VALUES (p_version_id_1, p_version_id_2, 'full_comparison', NOW());

    -- Result Set 1: Basic info for both models
    SELECT
        mv.version_id,
        mv.version_name,
        mv.external_id,
        p.name                        AS provider_name,
        mf.name                       AS family_name,
        mv.release_date,
        mv.status,
        mv.context_length,
        mv.max_output_tokens,
        mv.input_modalities,
        mv.output_modalities,
        mv.is_free,
        mv.supports_tool_use,
        mv.supports_reasoning,
        mv.supports_structured_output,
        ph.input_price_per_1m_tokens  AS input_price,
        ph.output_price_per_1m_tokens AS output_price,
        (SELECT ROUND(AVG(ur.rating), 2)
         FROM user_reviews ur
         WHERE ur.version_id = mv.version_id
           AND ur.is_approved = TRUE)  AS avg_rating,
        (SELECT GROUP_CONCAT(c.name ORDER BY c.name SEPARATOR ', ')
         FROM model_capabilities mc
         JOIN capabilities c ON mc.capability_id = c.capability_id
         WHERE mc.version_id = mv.version_id) AS capabilities_list
    FROM model_versions mv
    JOIN model_families    mf ON mv.family_id   = mf.family_id
    JOIN providers         p  ON mf.provider_id = p.provider_id
    LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
        AND ph.effective_date = (
            SELECT MAX(ph2.effective_date)
            FROM pricing_history ph2
            WHERE ph2.version_id = mv.version_id
        )
    WHERE mv.version_id IN (p_version_id_1, p_version_id_2);

    -- Result Set 2: Benchmark scores for both models
    SELECT
        mv.version_id,
        mv.version_name,
        b.name            AS benchmark_name,
        b.category        AS benchmark_category,
        bs.score,
        b.max_score,
        CASE
            WHEN b.max_score IS NOT NULL AND b.max_score > 0
            THEN ROUND((bs.score / b.max_score) * 100, 2)
            ELSE NULL
        END AS score_percentage
    FROM benchmark_scores bs
    JOIN model_versions mv ON bs.version_id   = mv.version_id
    JOIN benchmarks     b  ON bs.benchmark_id = b.benchmark_id
    WHERE mv.version_id IN (p_version_id_1, p_version_id_2)
    ORDER BY b.category, b.name, mv.version_id;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  3. sp_get_top_models
--     Get top N models by a chosen criteria:
--       'rating'         — highest average approved rating
--       'cheapest'       — lowest input price
--       'context_length' — largest context window
--       'newest'         — most recent release date
-- ────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_get_top_models;

DELIMITER //
CREATE PROCEDURE sp_get_top_models(
    IN p_criteria VARCHAR(50),
    IN p_limit    INT
)
BEGIN
    SET p_limit = IFNULL(p_limit, 10);

    SELECT
        mv.version_id,
        mv.version_name,
        p.name                        AS provider_name,
        mf.name                       AS family_name,
        mv.release_date,
        mv.context_length,
        mv.is_free,
        ph.input_price_per_1m_tokens  AS input_price,
        ph.output_price_per_1m_tokens AS output_price,
        ROUND(avg_r.avg_rating, 2)    AS avg_rating
    FROM model_versions mv
    JOIN model_families    mf ON mv.family_id   = mf.family_id
    JOIN providers         p  ON mf.provider_id = p.provider_id
    LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
        AND ph.effective_date = (
            SELECT MAX(ph2.effective_date)
            FROM pricing_history ph2
            WHERE ph2.version_id = mv.version_id
        )
    LEFT JOIN (
        SELECT version_id, AVG(rating) AS avg_rating
        FROM user_reviews
        WHERE is_approved = TRUE
        GROUP BY version_id
    ) avg_r ON avg_r.version_id = mv.version_id
    WHERE mv.status = 'active'
    ORDER BY
        CASE p_criteria
            WHEN 'rating'         THEN avg_r.avg_rating
            WHEN 'context_length' THEN mv.context_length
            ELSE NULL
        END DESC,
        CASE p_criteria
            WHEN 'cheapest' THEN ph.input_price_per_1m_tokens
            ELSE NULL
        END ASC,
        CASE p_criteria
            WHEN 'newest' THEN mv.release_date
            ELSE NULL
        END DESC
    LIMIT p_limit;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  4. sp_recommend_model
--     Recommend best models for a given use case within a
--     budget and minimum context length.
-- ────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_recommend_model;

DELIMITER //
CREATE PROCEDURE sp_recommend_model(
    IN p_use_case    VARCHAR(100),
    IN p_max_budget  DECIMAL(12,4),
    IN p_min_context INT
)
BEGIN
    SELECT
        mv.version_id,
        mv.version_name,
        p.name                         AS provider_name,
        uc.name                        AS use_case_name,
        muc.suitability_score,
        muc.notes                      AS suitability_notes,
        mv.context_length,
        mv.is_free,
        ph.input_price_per_1m_tokens   AS input_price,
        ph.output_price_per_1m_tokens  AS output_price,
        (SELECT ROUND(AVG(ur.rating), 2)
         FROM user_reviews ur
         WHERE ur.version_id = mv.version_id
           AND ur.is_approved = TRUE)  AS avg_rating
    FROM model_use_cases muc
    JOIN use_cases      uc ON muc.use_case_id = uc.use_case_id
    JOIN model_versions mv ON muc.version_id  = mv.version_id
    JOIN model_families mf ON mv.family_id    = mf.family_id
    JOIN providers      p  ON mf.provider_id  = p.provider_id
    LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
        AND ph.effective_date = (
            SELECT MAX(ph2.effective_date)
            FROM pricing_history ph2
            WHERE ph2.version_id = mv.version_id
        )
    WHERE
        mv.status = 'active'
        AND uc.name = p_use_case
        -- Budget filter
        AND (p_max_budget IS NULL
             OR mv.is_free = TRUE
             OR ph.input_price_per_1m_tokens <= p_max_budget)
        -- Context length filter
        AND (p_min_context IS NULL
             OR mv.context_length >= p_min_context)
    ORDER BY muc.suitability_score DESC, ph.input_price_per_1m_tokens ASC
    LIMIT 10;
END //
DELIMITER ;

-- ────────────────────────────────────────────────────────────
--  5. sp_provider_report
--     Full report for a provider: all models, versions,
--     pricing, average ratings, capability counts.
--     Returns 3 result sets.
-- ────────────────────────────────────────────────────────────
DROP PROCEDURE IF EXISTS sp_provider_report;

DELIMITER //
CREATE PROCEDURE sp_provider_report(
    IN p_provider_name VARCHAR(100)
)
BEGIN
    DECLARE v_provider_id INT;

    -- Resolve provider
    SELECT provider_id INTO v_provider_id
    FROM providers
    WHERE name = p_provider_name
    LIMIT 1;

    IF v_provider_id IS NULL THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Provider not found.';
    END IF;

    -- Result Set 1: Provider overview
    SELECT
        p.provider_id,
        p.name,
        p.headquarters_country,
        p.founded_year,
        p.website,
        p.description,
        COUNT(DISTINCT mf.family_id) AS family_count,
        COUNT(DISTINCT mv.version_id) AS version_count
    FROM providers p
    LEFT JOIN model_families mf ON mf.provider_id = p.provider_id
    LEFT JOIN model_versions mv ON mv.family_id   = mf.family_id
    WHERE p.provider_id = v_provider_id
    GROUP BY p.provider_id, p.name, p.headquarters_country,
             p.founded_year, p.website, p.description;

    -- Result Set 2: All model versions with pricing & ratings
    SELECT
        mf.name                       AS family_name,
        mv.version_id,
        mv.version_name,
        mv.external_id,
        mv.release_date,
        mv.status,
        mv.context_length,
        mv.is_free,
        ph.input_price_per_1m_tokens  AS input_price,
        ph.output_price_per_1m_tokens AS output_price,
        ROUND(avg_r.avg_rating, 2)    AS avg_rating,
        IFNULL(avg_r.review_count, 0) AS review_count,
        IFNULL(cap_cnt.capability_count, 0) AS capability_count
    FROM model_families mf
    JOIN model_versions mv ON mv.family_id = mf.family_id
    LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
        AND ph.effective_date = (
            SELECT MAX(ph2.effective_date)
            FROM pricing_history ph2
            WHERE ph2.version_id = mv.version_id
        )
    LEFT JOIN (
        SELECT version_id, AVG(rating) AS avg_rating, COUNT(*) AS review_count
        FROM user_reviews
        WHERE is_approved = TRUE
        GROUP BY version_id
    ) avg_r ON avg_r.version_id = mv.version_id
    LEFT JOIN (
        SELECT version_id, COUNT(*) AS capability_count
        FROM model_capabilities
        GROUP BY version_id
    ) cap_cnt ON cap_cnt.version_id = mv.version_id
    WHERE mf.provider_id = v_provider_id
    ORDER BY mf.name, mv.release_date DESC;

    -- Result Set 3: Capabilities summary across all provider models
    SELECT
        c.name            AS capability_name,
        c.category,
        COUNT(mc.version_id) AS model_count
    FROM model_capabilities mc
    JOIN capabilities c ON mc.capability_id = c.capability_id
    JOIN model_versions mv ON mc.version_id = mv.version_id
    JOIN model_families mf ON mv.family_id  = mf.family_id
    WHERE mf.provider_id = v_provider_id
    GROUP BY c.capability_id, c.name, c.category
    ORDER BY model_count DESC, c.name;
END //
DELIMITER ;

-- ============================================================
--  End of Procedures — 5 stored procedures created
-- ============================================================
