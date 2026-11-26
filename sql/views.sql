-- ============================================================
-- AI MODEL REGISTRY — Database Views
-- Project : AI Model Registry
-- Engine  : MySQL 8.x (InnoDB) on Aiven Cloud
-- Contents: 6 Views for reporting, search, and comparison
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  1. v_model_full_details
--     Joins model_versions + model_families + providers +
--     latest pricing row for each model.
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_model_full_details;

CREATE VIEW v_model_full_details AS
SELECT
    mv.version_id,
    mv.version_name,
    mv.external_id,
    mf.name                      AS family_name,
    p.name                       AS provider_name,
    p.headquarters_country,
    p.headquarters_country       AS country,
    mv.release_date,
    mv.status,
    mv.context_length,
    mv.max_output_tokens,
    mv.input_modalities,
    mv.output_modalities,
    mv.is_free,
    mv.has_free_tier,
    mv.supports_tool_use,
    mv.supports_reasoning,
    mv.supports_structured_output,
    ph.input_price_per_1m_tokens  AS input_price,
    ph.output_price_per_1m_tokens AS output_price,
    ph.effective_date             AS price_effective_date,
    ph.currency
FROM model_versions mv
JOIN model_families mf ON mv.family_id   = mf.family_id
JOIN providers      p  ON mf.provider_id = p.provider_id
LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
    AND ph.effective_date = (
        SELECT MAX(ph2.effective_date)
        FROM pricing_history ph2
        WHERE ph2.version_id = mv.version_id
    );

-- ────────────────────────────────────────────────────────────
--  2. v_top_rated_models
--     Models ranked by average approved-review rating.
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_top_rated_models;

CREATE VIEW v_top_rated_models AS
SELECT
    mv.version_id,
    mv.version_name,
    p.name                   AS provider_name,
    ROUND(AVG(ur.rating), 2) AS avg_rating,
    COUNT(ur.review_id)      AS review_count
FROM user_reviews ur
JOIN model_versions mv ON ur.version_id = mv.version_id
JOIN model_families mf ON mv.family_id  = mf.family_id
JOIN providers      p  ON mf.provider_id = p.provider_id
WHERE ur.is_approved = TRUE
GROUP BY mv.version_id, mv.version_name, p.name
ORDER BY avg_rating DESC, review_count DESC;

-- ────────────────────────────────────────────────────────────
--  3. v_free_models
--     All free models (is_free = TRUE or latest price = 0).
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_free_models;

CREATE VIEW v_free_models AS
SELECT
    vfd.*
FROM v_model_full_details vfd
WHERE vfd.is_free = TRUE
   OR (vfd.input_price = 0.0000 AND vfd.output_price = 0.0000);

-- ────────────────────────────────────────────────────────────
--  4. v_model_benchmark_summary
--     Pivot benchmark scores by category for each model.
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_model_benchmark_summary;

CREATE VIEW v_model_benchmark_summary AS
SELECT
    mv.version_id,
    mv.version_name,
    p.name AS provider_name,
    MAX(CASE WHEN b.category = 'general'     THEN bs.score END) AS general_score,
    MAX(CASE WHEN b.category = 'coding'      THEN bs.score END) AS coding_score,
    MAX(CASE WHEN b.category = 'math'        THEN bs.score END) AS math_score,
    MAX(CASE WHEN b.category = 'reasoning'   THEN bs.score END) AS reasoning_score,
    MAX(CASE WHEN b.category = 'creative'    THEN bs.score END) AS creative_score,
    MAX(CASE WHEN b.category = 'instruction' THEN bs.score END) AS instruction_score
FROM model_versions mv
JOIN model_families    mf ON mv.family_id    = mf.family_id
JOIN providers         p  ON mf.provider_id  = p.provider_id
LEFT JOIN benchmark_scores bs ON bs.version_id   = mv.version_id
LEFT JOIN benchmarks       b  ON bs.benchmark_id = b.benchmark_id
GROUP BY mv.version_id, mv.version_name, p.name;

-- ────────────────────────────────────────────────────────────
--  5. v_provider_statistics
--     Aggregate stats per provider.
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_provider_statistics;

CREATE VIEW v_provider_statistics AS
SELECT
    p.provider_id,
    p.name                                       AS provider_name,
    COUNT(DISTINCT mf.family_id)                 AS family_count,
    COUNT(DISTINCT mv.version_id)                AS version_count,
    SUM(mv.is_free = TRUE)                       AS free_version_count,
    ROUND(AVG(ph.input_price_per_1m_tokens), 4)  AS avg_input_price,
    ROUND(MIN(ph.input_price_per_1m_tokens), 4)  AS min_input_price,
    ROUND(MAX(ph.input_price_per_1m_tokens), 4)  AS max_input_price,
    ROUND(AVG(ph.output_price_per_1m_tokens), 4) AS avg_output_price,
    ROUND(AVG(ur.rating), 2)                     AS avg_rating
FROM providers p
LEFT JOIN model_families  mf ON mf.provider_id = p.provider_id
LEFT JOIN model_versions  mv ON mv.family_id   = mf.family_id
LEFT JOIN pricing_history ph ON ph.version_id  = mv.version_id
    AND ph.effective_date = (
        SELECT MAX(ph2.effective_date)
        FROM pricing_history ph2
        WHERE ph2.version_id = mv.version_id
    )
LEFT JOIN user_reviews ur ON ur.version_id = mv.version_id AND ur.is_approved = TRUE
GROUP BY p.provider_id, p.name;

-- ────────────────────────────────────────────────────────────
--  6. v_model_comparison_ready
--     All info needed for side-by-side model comparison.
-- ────────────────────────────────────────────────────────────
DROP VIEW IF EXISTS v_model_comparison_ready;

CREATE VIEW v_model_comparison_ready AS
SELECT
    mv.version_id,
    mv.version_name,
    mv.external_id,
    p.name                       AS provider_name,
    mf.name                      AS family_name,
    mv.context_length,
    mv.max_output_tokens,
    mv.is_free,
    mv.supports_tool_use,
    mv.supports_reasoning,
    -- Latest pricing
    ph.input_price_per_1m_tokens  AS input_price,
    ph.output_price_per_1m_tokens AS output_price,
    -- Average approved rating
    (SELECT ROUND(AVG(ur.rating), 2)
     FROM user_reviews ur
     WHERE ur.version_id = mv.version_id
       AND ur.is_approved = TRUE)                  AS avg_rating,
    -- Capabilities list
    (SELECT GROUP_CONCAT(c.name ORDER BY c.name SEPARATOR ', ')
     FROM model_capabilities mc
     JOIN capabilities c ON mc.capability_id = c.capability_id
     WHERE mc.version_id = mv.version_id)          AS capabilities_list,
    -- Benchmark scores list
    (SELECT GROUP_CONCAT(
                CONCAT(b.name, ':', bs.score)
                ORDER BY b.name SEPARATOR ', '
            )
     FROM benchmark_scores bs
     JOIN benchmarks b ON bs.benchmark_id = b.benchmark_id
     WHERE bs.version_id = mv.version_id)          AS benchmark_scores_list
FROM model_versions mv
JOIN model_families    mf ON mv.family_id   = mf.family_id
JOIN providers         p  ON mf.provider_id = p.provider_id
LEFT JOIN pricing_history ph ON ph.version_id = mv.version_id
    AND ph.effective_date = (
        SELECT MAX(ph2.effective_date)
        FROM pricing_history ph2
        WHERE ph2.version_id = mv.version_id
    );

-- ============================================================
--  End of Views — 6 views created
-- ============================================================
