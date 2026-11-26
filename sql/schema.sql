-- ============================================================
-- AI MODEL REGISTRY — Complete Database Schema
-- Project : AI Model Registry
-- Engine  : MySQL 8.x (InnoDB) on Aiven Cloud
-- Database: defaultdb (configured via .env)
-- Contents: 17 Tables with full constraints, foreign keys,
--           CHECK constraints, CASCADE / SET NULL rules
-- ============================================================

-- ────────────────────────────────────────────────────────────
--  Drop tables in reverse-dependency order
-- ────────────────────────────────────────────────────────────
DROP TABLE IF EXISTS search_logs;
DROP TABLE IF EXISTS comparison_logs;
DROP TABLE IF EXISTS error_reports;
DROP TABLE IF EXISTS user_reviews;
DROP TABLE IF EXISTS model_tags;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS model_use_cases;
DROP TABLE IF EXISTS use_cases;
DROP TABLE IF EXISTS benchmark_scores;
DROP TABLE IF EXISTS benchmarks;
DROP TABLE IF EXISTS model_capabilities;
DROP TABLE IF EXISTS capabilities;
DROP TABLE IF EXISTS pricing_history;
DROP TABLE IF EXISTS api_endpoints;
DROP TABLE IF EXISTS model_versions;
DROP TABLE IF EXISTS model_families;
DROP TABLE IF EXISTS providers;

-- ────────────────────────────────────────────────────────────
--  1. providers — AI companies / organisations
-- ────────────────────────────────────────────────────────────
CREATE TABLE providers (
    provider_id          INT            AUTO_INCREMENT PRIMARY KEY,
    name                 VARCHAR(100)   NOT NULL UNIQUE,
    headquarters_country VARCHAR(60),
    founded_year         INT,
    website              VARCHAR(255),
    description          TEXT,
    created_at           TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_providers_year CHECK (founded_year IS NULL OR founded_year BETWEEN 1900 AND 2100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  2. model_families — Model family (GPT, Claude, Gemini …)
-- ────────────────────────────────────────────────────────────
CREATE TABLE model_families (
    family_id    INT            AUTO_INCREMENT PRIMARY KEY,
    provider_id  INT            NOT NULL,
    name         VARCHAR(100)   NOT NULL,
    description  TEXT,
    is_open_source BOOLEAN      DEFAULT FALSE,
    github_url   VARCHAR(500),
    created_at   TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    UNIQUE KEY uq_family_provider_name (provider_id, name),

    CONSTRAINT fk_mf_provider
        FOREIGN KEY (provider_id) REFERENCES providers(provider_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  3. model_versions — Specific model releases
-- ────────────────────────────────────────────────────────────
CREATE TABLE model_versions (
    version_id               INT            AUTO_INCREMENT PRIMARY KEY,
    family_id                INT            NOT NULL,
    parent_version_id        INT            NULL,
    version_name             VARCHAR(200)   NOT NULL,
    external_id              VARCHAR(200)   UNIQUE,
    release_date             DATE,
    status                   ENUM('active','deprecated','beta','discontinued') DEFAULT 'active',
    context_length           INT,
    max_output_tokens        INT,
    input_modalities         VARCHAR(200),
    output_modalities        VARCHAR(200),
    tokenizer                VARCHAR(100),
    is_free                  BOOLEAN        DEFAULT FALSE,
    has_free_tier            BOOLEAN        DEFAULT FALSE,
    supports_tool_use        BOOLEAN        DEFAULT FALSE,
    supports_reasoning       BOOLEAN        DEFAULT FALSE,
    supports_structured_output BOOLEAN      DEFAULT FALSE,
    description              TEXT,
    created_at               TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT chk_mv_context    CHECK (context_length IS NULL OR context_length > 0),
    CONSTRAINT chk_mv_max_output CHECK (max_output_tokens IS NULL OR max_output_tokens > 0),

    CONSTRAINT fk_mv_family
        FOREIGN KEY (family_id) REFERENCES model_families(family_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_mv_parent
        FOREIGN KEY (parent_version_id) REFERENCES model_versions(version_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  4. pricing_history — Historical pricing per model version
-- ────────────────────────────────────────────────────────────
CREATE TABLE pricing_history (
    pricing_id               INT            AUTO_INCREMENT PRIMARY KEY,
    version_id               INT            NOT NULL,
    input_price_per_1m_tokens  DECIMAL(12,4) NOT NULL,
    output_price_per_1m_tokens DECIMAL(12,4) NOT NULL,
    effective_date           DATE           NOT NULL,
    currency                 VARCHAR(3)     DEFAULT 'USD',

    UNIQUE KEY uq_ph_version_date (version_id, effective_date),

    CONSTRAINT chk_ph_input_price  CHECK (input_price_per_1m_tokens  >= 0),
    CONSTRAINT chk_ph_output_price CHECK (output_price_per_1m_tokens >= 0),

    CONSTRAINT fk_ph_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  5. api_endpoints — API access info per model
-- ────────────────────────────────────────────────────────────
CREATE TABLE api_endpoints (
    endpoint_id       INT            AUTO_INCREMENT PRIMARY KEY,
    version_id        INT            NOT NULL,
    base_url          VARCHAR(500)   NOT NULL,
    auth_type         ENUM('api_key','oauth','none') DEFAULT 'api_key',
    documentation_url VARCHAR(500),
    rate_limit_rpm    INT,

    UNIQUE KEY uq_ae_version (version_id),

    CONSTRAINT chk_ae_rate_limit CHECK (rate_limit_rpm IS NULL OR rate_limit_rpm > 0),

    CONSTRAINT fk_ae_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  6. capabilities — Capability type catalogue
-- ────────────────────────────────────────────────────────────
CREATE TABLE capabilities (
    capability_id INT            AUTO_INCREMENT PRIMARY KEY,
    name          VARCHAR(100)   NOT NULL UNIQUE,
    category      VARCHAR(50),
    description   TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  7. model_capabilities — M:N junction (versions ↔ caps)
-- ────────────────────────────────────────────────────────────
CREATE TABLE model_capabilities (
    version_id    INT,
    capability_id INT,
    proficiency   ENUM('basic','good','excellent') DEFAULT 'good',

    PRIMARY KEY (version_id, capability_id),

    CONSTRAINT fk_mc_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_mc_capability
        FOREIGN KEY (capability_id) REFERENCES capabilities(capability_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  8. benchmarks — Benchmark definitions
-- ────────────────────────────────────────────────────────────
CREATE TABLE benchmarks (
    benchmark_id INT            AUTO_INCREMENT PRIMARY KEY,
    name         VARCHAR(100)   NOT NULL UNIQUE,
    full_name    VARCHAR(255),
    category     VARCHAR(50),
    max_score    DECIMAL(10,2),
    description  TEXT,
    source_url   VARCHAR(500),

    CONSTRAINT chk_bm_max_score CHECK (max_score IS NULL OR max_score > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  9. benchmark_scores — Scores per model per benchmark
-- ────────────────────────────────────────────────────────────
CREATE TABLE benchmark_scores (
    score_id      INT            AUTO_INCREMENT PRIMARY KEY,
    version_id    INT            NOT NULL,
    benchmark_id  INT            NOT NULL,
    score         DECIMAL(10,4)  NOT NULL,
    evaluated_date DATE,
    source        VARCHAR(255),

    UNIQUE KEY uq_bs_version_benchmark (version_id, benchmark_id),

    CONSTRAINT fk_bs_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_bs_benchmark
        FOREIGN KEY (benchmark_id) REFERENCES benchmarks(benchmark_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  10. use_cases — Use-case categories
-- ────────────────────────────────────────────────────────────
CREATE TABLE use_cases (
    use_case_id INT            AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100)   NOT NULL UNIQUE,
    description TEXT,
    category    VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  11. model_use_cases — M:N with suitability rating
-- ────────────────────────────────────────────────────────────
CREATE TABLE model_use_cases (
    version_id       INT,
    use_case_id      INT,
    suitability_score DECIMAL(3,2),
    notes            TEXT,

    PRIMARY KEY (version_id, use_case_id),

    CONSTRAINT chk_muc_suitability CHECK (suitability_score IS NULL OR (suitability_score BETWEEN 0.00 AND 1.00)),

    CONSTRAINT fk_muc_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_muc_use_case
        FOREIGN KEY (use_case_id) REFERENCES use_cases(use_case_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  12. tags — Flexible tag system
-- ────────────────────────────────────────────────────────────
CREATE TABLE tags (
    tag_id INT            AUTO_INCREMENT PRIMARY KEY,
    name   VARCHAR(50)    NOT NULL UNIQUE,
    color  VARCHAR(7)     DEFAULT '#3B82F6'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  13. model_tags — M:N junction (versions ↔ tags)
-- ────────────────────────────────────────────────────────────
CREATE TABLE model_tags (
    version_id INT,
    tag_id     INT,

    PRIMARY KEY (version_id, tag_id),

    CONSTRAINT fk_mt_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_mt_tag
        FOREIGN KEY (tag_id) REFERENCES tags(tag_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  14. user_reviews — User ratings and reviews
-- ────────────────────────────────────────────────────────────
CREATE TABLE user_reviews (
    review_id     INT            AUTO_INCREMENT PRIMARY KEY,
    version_id    INT            NOT NULL,
    reviewer_name VARCHAR(100)   NOT NULL,
    rating        INT            NOT NULL,
    title         VARCHAR(200),
    review_text   TEXT,
    is_verified   BOOLEAN        DEFAULT FALSE,
    is_approved   BOOLEAN        DEFAULT FALSE,
    created_at    TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_ur_rating CHECK (rating BETWEEN 1 AND 5),

    CONSTRAINT fk_ur_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  15. error_reports — Reported issues / bugs
-- ────────────────────────────────────────────────────────────
CREATE TABLE error_reports (
    report_id         INT            AUTO_INCREMENT PRIMARY KEY,
    version_id        INT            NOT NULL,
    reporter_name     VARCHAR(100),
    error_type        ENUM('hallucination','refusal','incorrect','timeout','formatting','safety','other') NOT NULL,
    severity          ENUM('low','medium','high','critical') DEFAULT 'medium',
    description       TEXT           NOT NULL,
    steps_to_reproduce TEXT,
    status            ENUM('open','investigating','confirmed','resolved','wont_fix') DEFAULT 'open',
    created_at        TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,
    resolved_at       TIMESTAMP      NULL,

    CONSTRAINT fk_er_version
        FOREIGN KEY (version_id) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  16. comparison_logs — Audit trail of model comparisons
-- ────────────────────────────────────────────────────────────
CREATE TABLE comparison_logs (
    comparison_id       INT            AUTO_INCREMENT PRIMARY KEY,
    session_id          VARCHAR(100),
    version_id_1        INT            NOT NULL,
    version_id_2        INT            NOT NULL,
    winner_version_id   INT,
    comparison_criteria VARCHAR(100),
    created_at          TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_cl_version1
        FOREIGN KEY (version_id_1) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_cl_version2
        FOREIGN KEY (version_id_2) REFERENCES model_versions(version_id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_cl_winner
        FOREIGN KEY (winner_version_id) REFERENCES model_versions(version_id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ────────────────────────────────────────────────────────────
--  17. search_logs — Search query audit trail
-- ────────────────────────────────────────────────────────────
CREATE TABLE search_logs (
    search_id       INT            AUTO_INCREMENT PRIMARY KEY,
    session_id      VARCHAR(100),
    query_text      VARCHAR(500),
    filters_applied JSON,
    results_count   INT,
    created_at      TIMESTAMP      DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_sl_results CHECK (results_count IS NULL OR results_count >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
--  End of Schema — 17 tables created
-- ============================================================
