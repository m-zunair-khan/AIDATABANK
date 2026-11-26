-- ============================================================
-- AI MODEL REGISTRY — Performance Indexes
-- Project : AI Model Registry
-- Engine  : MySQL 8.x (InnoDB) on Aiven Cloud
-- Contents: 16 Indexes (B-Tree + FULLTEXT) for query
--           performance on frequently accessed columns
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  model_versions indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_mv_family_id    ON model_versions(family_id);
CREATE INDEX idx_mv_release_date ON model_versions(release_date);
CREATE INDEX idx_mv_status       ON model_versions(status);
CREATE INDEX idx_mv_external_id  ON model_versions(external_id);

-- Full-text index for search across name and description
CREATE FULLTEXT INDEX idx_mv_fulltext ON model_versions(version_name, description);

-- ────────────────────────────────────────────────────────────
--  pricing_history indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_ph_version_id    ON pricing_history(version_id);
CREATE INDEX idx_ph_effective_date ON pricing_history(effective_date);

-- ────────────────────────────────────────────────────────────
--  benchmark_scores indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_bs_version_id   ON benchmark_scores(version_id);
CREATE INDEX idx_bs_benchmark_id ON benchmark_scores(benchmark_id);

-- ────────────────────────────────────────────────────────────
--  user_reviews indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_ur_version_id ON user_reviews(version_id);
CREATE INDEX idx_ur_rating     ON user_reviews(rating);

-- ────────────────────────────────────────────────────────────
--  error_reports indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_er_version_id ON error_reports(version_id);
CREATE INDEX idx_er_status     ON error_reports(status);

-- ────────────────────────────────────────────────────────────
--  search_logs indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_sl_session ON search_logs(session_id);
CREATE INDEX idx_sl_created ON search_logs(created_at);

-- ────────────────────────────────────────────────────────────
--  comparison_logs indexes
-- ────────────────────────────────────────────────────────────
CREATE INDEX idx_cl_session ON comparison_logs(session_id);

-- ============================================================
--  End of Indexes — 16 indexes created
-- ============================================================
