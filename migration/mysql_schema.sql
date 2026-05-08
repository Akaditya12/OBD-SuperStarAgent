-- OBD SuperStar Agent — MySQL schema (ported from Supabase Postgres)
-- Run as root: mysql -u root -p < migration/mysql_schema.sql
--
-- Creates:
--   * database `obd_superstar`
--   * user `obd_app`@`localhost` with full privileges on that DB
--   * 11 tables matching the Supabase schema
--
-- Postgres → MySQL type decisions:
--   uuid          → CHAR(36)
--   text PK/FK    → VARCHAR(255) (TEXT can't be indexed without prefix)
--   text content  → TEXT
--   jsonb         → JSON
--   timestamptz   → DATETIME (stored as UTC; app handles timezone)
--   boolean       → TINYINT(1)

-- ── Database + user ──────────────────────────────────────────────────────
CREATE DATABASE IF NOT EXISTS obd_superstar
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'obd_app'@'localhost'
  IDENTIFIED BY 'obd_local_dev_2026';

GRANT ALL PRIVILEGES ON obd_superstar.* TO 'obd_app'@'localhost';
FLUSH PRIVILEGES;

USE obd_superstar;

-- ── Tables ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS users (
  id             CHAR(36)      NOT NULL,
  username       VARCHAR(255)  NOT NULL,
  email          VARCHAR(255)  NOT NULL,
  password_hash  TEXT          NOT NULL,
  role           VARCHAR(32)   NOT NULL,
  team           VARCHAR(128)  NOT NULL,
  is_active      TINYINT(1)    NOT NULL DEFAULT 1,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_users_username (username),
  UNIQUE KEY uq_users_email (email),
  CONSTRAINT chk_users_role CHECK (role IN ('admin', 'member'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS campaigns (
  id            VARCHAR(64)   NOT NULL,
  name          VARCHAR(512)  NOT NULL,
  created_by    VARCHAR(255)  NOT NULL,
  team          VARCHAR(128)  NOT NULL,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  country       VARCHAR(128)  NOT NULL,
  telco         VARCHAR(128)  NOT NULL,
  language      VARCHAR(64)   NOT NULL,
  result_json   JSON          NULL,
  script_count  INT           NOT NULL DEFAULT 0,
  has_audio     TINYINT(1)    NOT NULL DEFAULT 0,
  PRIMARY KEY (id),
  KEY idx_campaigns_created_by (created_by),
  KEY idx_campaigns_team (team),
  KEY idx_campaigns_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS campaign_comments (
  id            VARCHAR(64)   NOT NULL,
  campaign_id   VARCHAR(64)   NOT NULL,
  username      VARCHAR(255)  NOT NULL,
  text          TEXT          NOT NULL,
  created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_comments_campaign (campaign_id),
  CONSTRAINT fk_comments_campaign
    FOREIGN KEY (campaign_id) REFERENCES campaigns(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS app_config (
  `key`        VARCHAR(128)  NOT NULL,
  `value`      JSON          NOT NULL,
  updated_by   VARCHAR(255)  NOT NULL DEFAULT 'system',
  updated_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS audit_log (
  id               CHAR(36)      NOT NULL,
  admin_username   VARCHAR(255)  NOT NULL,
  action           VARCHAR(128)  NOT NULL,
  target_user      VARCHAR(255)  NULL,
  details          JSON          NULL,
  created_at       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_audit_admin (admin_username),
  KEY idx_audit_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS analysis_cache (
  cache_key        VARCHAR(64)  NOT NULL,
  country          VARCHAR(128) NOT NULL DEFAULT '',
  telco            VARCHAR(128) NOT NULL DEFAULT '',
  language         VARCHAR(64)  NOT NULL DEFAULT '',
  product_brief    JSON         NOT NULL,
  market_analysis  JSON         NOT NULL,
  created_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (cache_key),
  KEY idx_cache_country_telco (country, telco, language)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS flow_configs (
  id             CHAR(36)      NOT NULL,
  account_key    VARCHAR(128)  NOT NULL,
  service_key    VARCHAR(128)  NOT NULL,
  display_name   VARCHAR(255)  NOT NULL,
  steps          JSON          NOT NULL,
  is_default     TINYINT(1)    NOT NULL DEFAULT 0,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_flow_account_service (account_key, service_key),
  KEY idx_flow_account_service (account_key, service_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS market_countries (
  id             VARCHAR(64)   NOT NULL,
  name           VARCHAR(128)  NOT NULL,
  currency_code  VARCHAR(16)   NOT NULL DEFAULT '',
  display_order  INT           NOT NULL DEFAULT 0,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_countries_display_order (display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS market_languages (
  id             CHAR(36)      NOT NULL,
  country_id     VARCHAR(64)   NOT NULL,
  name           VARCHAR(128)  NOT NULL,
  display_order  INT           NOT NULL DEFAULT 0,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_languages_country (country_id),
  CONSTRAINT fk_languages_country
    FOREIGN KEY (country_id) REFERENCES market_countries(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS market_telcos (
  id             CHAR(36)      NOT NULL,
  country_id     VARCHAR(64)   NOT NULL,
  name           VARCHAR(128)  NOT NULL,
  display_order  INT           NOT NULL DEFAULT 0,
  created_at     DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_telcos_country (country_id),
  CONSTRAINT fk_telcos_country
    FOREIGN KEY (country_id) REFERENCES market_countries(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS product_presets (
  id                VARCHAR(128)  NOT NULL,
  name              VARCHAR(255)  NOT NULL,
  icon              VARCHAR(64)   NOT NULL DEFAULT 'Package',
  short_desc        VARCHAR(512)  NOT NULL DEFAULT '',
  full_description  TEXT          NOT NULL,
  category          VARCHAR(32)   NOT NULL,
  display_order     INT           NOT NULL DEFAULT 0,
  created_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_presets_display_order (display_order),
  CONSTRAINT chk_presets_category CHECK (
    category IN ('ai', 'voice', 'connectivity', 'enterprise', 'entertainment', 'education', 'lifestyle')
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
