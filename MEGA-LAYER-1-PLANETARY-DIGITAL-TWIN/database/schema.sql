-- AEGIS OMEGA X — MEGA LAYER 1
-- PLANETARY DIGITAL TWIN — POSTGRESQL SCHEMA
-- database/schema.sql

-- ──────────────────────────────────────────────
-- EXTENSIONS
-- ──────────────────────────────────────────────
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "timescaledb";    -- TimescaleDB for time-series

-- ──────────────────────────────────────────────
-- SCHEMA
-- ──────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS pdt;
SET search_path TO pdt, public;

-- ──────────────────────────────────────────────
-- CIVILIZATIONAL ENTITIES
-- ──────────────────────────────────────────────
CREATE TABLE civilizational_entities (
    entity_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name                TEXT NOT NULL,
    domain              TEXT NOT NULL CHECK (domain IN (
                            'enterprise','government','healthcare','financial',
                            'telecom','transport','energy','manufacturing',
                            'smart_city','university','supply_chain',
                            'cloud_provider','ai_ecosystem'
                        )),
    country             TEXT,
    region              TEXT,
    sector              TEXT,
    employee_count      INTEGER DEFAULT 0,
    revenue_usd         NUMERIC(20,2) DEFAULT 0,
    criticality_score   FLOAT CHECK (criticality_score BETWEEN 0 AND 1),
    interconnectedness  FLOAT CHECK (interconnectedness BETWEEN 0 AND 1),
    security_maturity   FLOAT CHECK (security_maturity BETWEEN 0 AND 1),
    digital_surface     INTEGER DEFAULT 0,
    simulation_status   TEXT DEFAULT 'nominal',
    last_sync           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX idx_entity_domain   ON civilizational_entities(domain);
CREATE INDEX idx_entity_country  ON civilizational_entities(country);
CREATE INDEX idx_entity_crit     ON civilizational_entities(criticality_score DESC);
CREATE INDEX idx_entity_meta     ON civilizational_entities USING gin(metadata);

-- ──────────────────────────────────────────────
-- DIGITAL ASSETS
-- ──────────────────────────────────────────────
CREATE TABLE digital_assets (
    asset_id            UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id           UUID NOT NULL REFERENCES civilizational_entities(entity_id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    asset_type          TEXT NOT NULL,
    hostname            TEXT,
    ip_addresses        INET[],
    cloud_provider      TEXT,
    cloud_region        TEXT,
    cloud_account       TEXT,
    os                  TEXT,
    os_version          TEXT,
    software_stack      TEXT[],
    cve_ids             TEXT[],
    risk_score          FLOAT DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 1),
    risk_level          TEXT DEFAULT 'low',
    exposure_score      FLOAT DEFAULT 0,
    criticality         FLOAT DEFAULT 0,
    is_internet_facing  BOOLEAN DEFAULT FALSE,
    is_in_dmz           BOOLEAN DEFAULT FALSE,
    is_air_gapped       BOOLEAN DEFAULT FALSE,
    contains_pii        BOOLEAN DEFAULT FALSE,
    contains_phi        BOOLEAN DEFAULT FALSE,
    contains_pci        BOOLEAN DEFAULT FALSE,
    security_controls   TEXT[],
    simulation_status   TEXT DEFAULT 'nominal',
    last_seen           TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),
    tags                JSONB DEFAULT '{}',
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX idx_asset_entity      ON digital_assets(entity_id);
CREATE INDEX idx_asset_type        ON digital_assets(asset_type);
CREATE INDEX idx_asset_risk        ON digital_assets(risk_score DESC);
CREATE INDEX idx_asset_internet    ON digital_assets(is_internet_facing) WHERE is_internet_facing = TRUE;
CREATE INDEX idx_asset_cve         ON digital_assets USING gin(cve_ids);
CREATE INDEX idx_asset_meta        ON digital_assets USING gin(metadata);
CREATE INDEX idx_asset_ip          ON digital_assets USING gin(ip_addresses);

-- ──────────────────────────────────────────────
-- IDENTITIES
-- ──────────────────────────────────────────────
CREATE TABLE identities (
    identity_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id           UUID NOT NULL REFERENCES civilizational_entities(entity_id) ON DELETE CASCADE,
    name                TEXT NOT NULL,
    email               TEXT,
    identity_type       TEXT DEFAULT 'human',
    department          TEXT,
    role                TEXT,
    privilege_level     TEXT DEFAULT 'standard',
    mfa_enabled         BOOLEAN DEFAULT FALSE,
    federated           BOOLEAN DEFAULT FALSE,
    active              BOOLEAN DEFAULT TRUE,
    last_activity       TIMESTAMPTZ,
    risk_score          FLOAT DEFAULT 0,
    behavioral_baseline JSONB DEFAULT '{}',
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_identity_entity   ON identities(entity_id);
CREATE INDEX idx_identity_type     ON identities(identity_type);
CREATE INDEX idx_identity_priv     ON identities(privilege_level);
CREATE INDEX idx_identity_risk     ON identities(risk_score DESC);

-- ──────────────────────────────────────────────
-- ASSET RELATIONSHIPS
-- ──────────────────────────────────────────────
CREATE TABLE asset_relationships (
    relationship_id     UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id           UUID NOT NULL,
    target_id           UUID NOT NULL,
    relationship_type   TEXT NOT NULL,
    protocol            TEXT,
    port                INTEGER,
    encrypted           BOOLEAN DEFAULT FALSE,
    authenticated       BOOLEAN DEFAULT FALSE,
    data_sensitivity    TEXT DEFAULT 'low',
    bandwidth_mbps      FLOAT,
    latency_ms          FLOAT,
    risk_score          FLOAT DEFAULT 0,
    discovered_at       TIMESTAMPTZ DEFAULT NOW(),
    last_observed       TIMESTAMPTZ,
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX idx_rel_source ON asset_relationships(source_id);
CREATE INDEX idx_rel_target ON asset_relationships(target_id);
CREATE INDEX idx_rel_type   ON asset_relationships(relationship_type);

-- ──────────────────────────────────────────────
-- CASCADE EVENTS (TIME-SERIES via TimescaleDB)
-- ──────────────────────────────────────────────
CREATE TABLE cascade_events (
    event_id            UUID NOT NULL DEFAULT uuid_generate_v4(),
    origin_asset_id     UUID NOT NULL,
    origin_entity_id    UUID NOT NULL,
    event_type          TEXT NOT NULL,
    blast_radius        TEXT[],   -- affected asset IDs
    affected_entities   TEXT[],
    propagation_path    TEXT[],
    severity            TEXT DEFAULT 'high',
    economic_impact_usd NUMERIC(20,2),
    started_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    contained_at        TIMESTAMPTZ,
    recovered_at        TIMESTAMPTZ,
    simulated           BOOLEAN DEFAULT TRUE,
    metadata            JSONB DEFAULT '{}'
);

-- Convert to hypertable for time-series
SELECT create_hypertable('cascade_events', 'started_at');
CREATE INDEX idx_cascade_origin  ON cascade_events(origin_asset_id, started_at DESC);
CREATE INDEX idx_cascade_entity  ON cascade_events(origin_entity_id, started_at DESC);
CREATE INDEX idx_cascade_type    ON cascade_events(event_type, started_at DESC);

-- ──────────────────────────────────────────────
-- SIMULATION TICKS (TIME-SERIES)
-- ──────────────────────────────────────────────
CREATE TABLE simulation_ticks (
    tick_id             UUID NOT NULL DEFAULT uuid_generate_v4(),
    tick_number         BIGINT NOT NULL,
    tick_timestamp      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    global_risk_score   FLOAT,
    active_threats      INTEGER DEFAULT 0,
    compromised_assets  INTEGER DEFAULT 0,
    degraded_entities   INTEGER DEFAULT 0,
    cascade_events_active INTEGER DEFAULT 0,
    simulation_lag_ms   FLOAT,
    state_delta         JSONB DEFAULT '{}'
);

SELECT create_hypertable('simulation_ticks', 'tick_timestamp');
CREATE INDEX idx_tick_number ON simulation_ticks(tick_number DESC);

-- ──────────────────────────────────────────────
-- CLOUD REGION MODELS
-- ──────────────────────────────────────────────
CREATE TABLE cloud_region_models (
    region_id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider            TEXT NOT NULL,
    region_code         TEXT NOT NULL UNIQUE,
    geography           TEXT,
    availability_zones  TEXT[],
    services_hosted     TEXT[],
    tenant_count        INTEGER DEFAULT 0,
    data_sovereignty_laws TEXT[],
    interconnects       TEXT[],
    status              TEXT DEFAULT 'nominal',
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX idx_cloud_provider ON cloud_region_models(provider);
CREATE INDEX idx_cloud_region   ON cloud_region_models(region_code);

-- ──────────────────────────────────────────────
-- AI ECOSYSTEM NODES
-- ──────────────────────────────────────────────
CREATE TABLE ai_ecosystem_nodes (
    ai_node_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id           UUID REFERENCES civilizational_entities(entity_id),
    name                TEXT NOT NULL,
    model_type          TEXT,
    provider            TEXT,
    version             TEXT,
    hosting             TEXT DEFAULT 'cloud',
    training_data       TEXT[],
    inference_endpoints TEXT[],
    access_controls     TEXT[],
    data_processed      TEXT[],
    risk_score          FLOAT DEFAULT 0,
    alignment_score     FLOAT,
    audit_trail         BOOLEAN DEFAULT FALSE,
    metadata            JSONB DEFAULT '{}'
);

CREATE INDEX idx_ai_entity    ON ai_ecosystem_nodes(entity_id);
CREATE INDEX idx_ai_type      ON ai_ecosystem_nodes(model_type);
CREATE INDEX idx_ai_risk      ON ai_ecosystem_nodes(risk_score DESC);

-- ──────────────────────────────────────────────
-- RISK FORECAST CACHE
-- ──────────────────────────────────────────────
CREATE TABLE risk_forecasts (
    forecast_id         UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id           UUID NOT NULL,
    current_risk        FLOAT,
    forecast_data       JSONB NOT NULL,
    horizon_days        INTEGER,
    model_version       TEXT,
    generated_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at          TIMESTAMPTZ
);

CREATE INDEX idx_forecast_entity ON risk_forecasts(entity_id);
CREATE INDEX idx_forecast_time   ON risk_forecasts(generated_at DESC);

-- ──────────────────────────────────────────────
-- UPDATED_AT TRIGGER
-- ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_entities_updated
    BEFORE UPDATE ON civilizational_entities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_assets_updated
    BEFORE UPDATE ON digital_assets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trg_identities_updated
    BEFORE UPDATE ON identities
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ──────────────────────────────────────────────
-- VIEWS
-- ──────────────────────────────────────────────

-- Global risk summary per entity
CREATE VIEW entity_risk_summary AS
SELECT
    e.entity_id,
    e.name,
    e.domain,
    e.country,
    e.criticality_score,
    COUNT(a.asset_id)                               AS total_assets,
    AVG(a.risk_score)                               AS avg_asset_risk,
    SUM(CASE WHEN a.is_internet_facing THEN 1 ELSE 0 END) AS internet_facing_count,
    SUM(CASE WHEN a.risk_score >= 0.7 THEN 1 ELSE 0 END)  AS high_risk_count,
    COUNT(DISTINCT i.identity_id)                   AS total_identities,
    SUM(CASE WHEN i.privilege_level IN ('admin','superadmin') THEN 1 ELSE 0 END) AS privileged_identities
FROM civilizational_entities e
LEFT JOIN digital_assets a ON e.entity_id = a.entity_id
LEFT JOIN identities i ON e.entity_id = i.entity_id
GROUP BY e.entity_id, e.name, e.domain, e.country, e.criticality_score;

-- Top 50 riskiest assets globally
CREATE VIEW global_top_risk_assets AS
SELECT
    a.asset_id,
    a.name,
    a.asset_type,
    a.risk_score,
    a.risk_level,
    a.is_internet_facing,
    e.name AS entity_name,
    e.domain AS entity_domain
FROM digital_assets a
JOIN civilizational_entities e ON a.entity_id = e.entity_id
ORDER BY a.risk_score DESC
LIMIT 50;
