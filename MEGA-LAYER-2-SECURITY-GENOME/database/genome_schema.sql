-- AEGIS OMEGA X — MEGA LAYER 2
-- ENTERPRISE SECURITY GENOME — DATABASE SCHEMA
-- PostgreSQL + TimescaleDB

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "timescaledb";

CREATE SCHEMA IF NOT EXISTS genome;
SET search_path TO genome, public;

-- ──────────────────────────────────────────────
-- GENOME NODES (Relational mirror of Neo4j)
-- Used for analytics, reporting, time-travel queries
-- ──────────────────────────────────────────────
CREATE TABLE genome_nodes (
    node_id          UUID NOT NULL DEFAULT uuid_generate_v4(),
    entity_id        UUID NOT NULL,
    node_type        TEXT NOT NULL,
    name             TEXT NOT NULL,
    label            TEXT,
    risk_score       FLOAT DEFAULT 0 CHECK (risk_score BETWEEN 0 AND 1),
    inherited_risk   FLOAT DEFAULT 0,
    effective_risk   FLOAT DEFAULT 0,
    dna_fingerprint  TEXT,
    version          INTEGER DEFAULT 1,
    active           BOOLEAN DEFAULT TRUE,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW(),
    properties       JSONB DEFAULT '{}',
    tags             JSONB DEFAULT '{}'
);

-- Time-series hypertable for genome node snapshots
CREATE TABLE genome_node_snapshots (
    snapshot_id      UUID NOT NULL DEFAULT uuid_generate_v4(),
    node_id          UUID NOT NULL,
    entity_id        UUID NOT NULL,
    node_type        TEXT NOT NULL,
    risk_score       FLOAT,
    effective_risk   FLOAT,
    dna_fingerprint  TEXT,
    version          INTEGER,
    snapshotted_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    properties       JSONB DEFAULT '{}'
);
SELECT create_hypertable('genome_node_snapshots', 'snapshotted_at');

CREATE INDEX idx_snapshot_node ON genome_node_snapshots(node_id, snapshotted_at DESC);
CREATE INDEX idx_snapshot_entity ON genome_node_snapshots(entity_id, snapshotted_at DESC);

-- ──────────────────────────────────────────────
-- MUTATION EVENTS (Append-only audit log)
-- ──────────────────────────────────────────────
CREATE TABLE mutation_events (
    mutation_id      UUID NOT NULL DEFAULT uuid_generate_v4(),
    entity_id        UUID NOT NULL,
    node_id          UUID,
    node_type        TEXT,
    mutation_type    TEXT NOT NULL,
    previous_fp      TEXT,
    current_fp       TEXT,
    previous_state   JSONB DEFAULT '{}',
    current_state    JSONB DEFAULT '{}',
    delta            JSONB DEFAULT '{}',
    risk_delta       FLOAT DEFAULT 0,
    severity         TEXT DEFAULT 'low' CHECK (severity IN ('critical','high','medium','low','informational')),
    auto_detected    BOOLEAN DEFAULT TRUE,
    source           TEXT,
    actor            TEXT,
    occurred_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    detected_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata         JSONB DEFAULT '{}'
);

SELECT create_hypertable('mutation_events', 'occurred_at');

CREATE INDEX idx_mutation_entity   ON mutation_events(entity_id, occurred_at DESC);
CREATE INDEX idx_mutation_node     ON mutation_events(node_id, occurred_at DESC);
CREATE INDEX idx_mutation_type     ON mutation_events(mutation_type, occurred_at DESC);
CREATE INDEX idx_mutation_severity ON mutation_events(severity, occurred_at DESC);
CREATE INDEX idx_mutation_critical ON mutation_events(occurred_at DESC)
    WHERE severity IN ('critical', 'high');

-- ──────────────────────────────────────────────
-- SECURITY DNA SNAPSHOTS
-- ──────────────────────────────────────────────
CREATE TABLE security_dna_snapshots (
    dna_id               UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id            UUID NOT NULL,
    snapshot_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    genome_version       INTEGER NOT NULL,
    genome_hash          TEXT,

    -- Node counts
    total_nodes          INTEGER DEFAULT 0,
    asset_count          INTEGER DEFAULT 0,
    identity_count       INTEGER DEFAULT 0,
    application_count    INTEGER DEFAULT 0,
    control_count        INTEGER DEFAULT 0,
    dependency_count     INTEGER DEFAULT 0,
    cve_count            INTEGER DEFAULT 0,

    -- Risk profile
    overall_risk         FLOAT,
    asset_risk_avg       FLOAT,
    identity_risk_avg    FLOAT,
    critical_cve_count   INTEGER DEFAULT 0,
    unpatched_critical   INTEGER DEFAULT 0,
    overprivileged_ids   INTEGER DEFAULT 0,
    stale_identities     INTEGER DEFAULT 0,
    orphaned_assets      INTEGER DEFAULT 0,

    -- Coverage metrics
    control_coverage     FLOAT,
    mfa_coverage         FLOAT,
    encryption_coverage  FLOAT,
    patch_coverage       FLOAT,

    -- Complexity
    total_edges          INTEGER DEFAULT 0,
    avg_dependencies     FLOAT,
    max_blast_radius     INTEGER DEFAULT 0,

    -- Resilience
    resilience_scores    JSONB DEFAULT '{}'
);

SELECT create_hypertable('security_dna_snapshots', 'snapshot_at');
CREATE INDEX idx_dna_entity ON security_dna_snapshots(entity_id, snapshot_at DESC);

-- ──────────────────────────────────────────────
-- RESILIENCE SNAPSHOTS (Time-series)
-- ──────────────────────────────────────────────
CREATE TABLE resilience_snapshots (
    snapshot_id          UUID NOT NULL DEFAULT uuid_generate_v4(),
    entity_id            UUID NOT NULL,
    measured_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    redundancy           FLOAT CHECK (redundancy BETWEEN 0 AND 1),
    recovery_speed       FLOAT CHECK (recovery_speed BETWEEN 0 AND 1),
    blast_radius_score   FLOAT CHECK (blast_radius_score BETWEEN 0 AND 1),
    control_coverage     FLOAT CHECK (control_coverage BETWEEN 0 AND 1),
    patch_velocity       FLOAT CHECK (patch_velocity BETWEEN 0 AND 1),
    identity_hygiene     FLOAT CHECK (identity_hygiene BETWEEN 0 AND 1),
    encryption_coverage  FLOAT CHECK (encryption_coverage BETWEEN 0 AND 1),
    segmentation         FLOAT CHECK (segmentation BETWEEN 0 AND 1),
    overall_resilience   FLOAT CHECK (overall_resilience BETWEEN 0 AND 1)
);

SELECT create_hypertable('resilience_snapshots', 'measured_at');
CREATE INDEX idx_resilience_entity ON resilience_snapshots(entity_id, measured_at DESC);

-- ──────────────────────────────────────────────
-- GENOME EDGES (Relational)
-- ──────────────────────────────────────────────
CREATE TABLE genome_edges (
    edge_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id        UUID NOT NULL,
    source_id        UUID NOT NULL,
    target_id        UUID NOT NULL,
    edge_type        TEXT NOT NULL,
    risk_weight      FLOAT DEFAULT 1.0,
    bidirectional    BOOLEAN DEFAULT FALSE,
    encrypted        BOOLEAN DEFAULT FALSE,
    authenticated    BOOLEAN DEFAULT FALSE,
    authorized       BOOLEAN DEFAULT TRUE,
    data_flow        BOOLEAN DEFAULT FALSE,
    data_sensitivity TEXT DEFAULT 'low',
    discovered_at    TIMESTAMPTZ DEFAULT NOW(),
    last_observed    TIMESTAMPTZ,
    active           BOOLEAN DEFAULT TRUE,
    version          INTEGER DEFAULT 1,
    metadata         JSONB DEFAULT '{}'
);

CREATE INDEX idx_edge_entity  ON genome_edges(entity_id);
CREATE INDEX idx_edge_source  ON genome_edges(source_id);
CREATE INDEX idx_edge_target  ON genome_edges(target_id);
CREATE INDEX idx_edge_type    ON genome_edges(edge_type);
CREATE INDEX idx_edge_active  ON genome_edges(active) WHERE active = TRUE;

-- ──────────────────────────────────────────────
-- CVE CATALOG
-- ──────────────────────────────────────────────
CREATE TABLE cve_catalog (
    cve_id           TEXT PRIMARY KEY,
    cvss_score       FLOAT,
    cvss_vector      TEXT,
    severity         TEXT,
    description      TEXT,
    published        TIMESTAMPTZ,
    last_modified    TIMESTAMPTZ,
    exploited_wild   BOOLEAN DEFAULT FALSE,
    exploit_avail    BOOLEAN DEFAULT FALSE,
    epss_score       FLOAT,
    affected_software TEXT[],
    references       TEXT[],
    patched          BOOLEAN DEFAULT FALSE,
    patch_available  BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_cve_score   ON cve_catalog(cvss_score DESC);
CREATE INDEX idx_cve_epss    ON cve_catalog(epss_score DESC);
CREATE INDEX idx_cve_wild    ON cve_catalog(exploited_wild) WHERE exploited_wild = TRUE;

-- ──────────────────────────────────────────────
-- GENOME DIFF HISTORY
-- ──────────────────────────────────────────────
CREATE TABLE genome_diffs (
    diff_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id        UUID NOT NULL,
    from_version     INTEGER NOT NULL,
    to_version       INTEGER NOT NULL,
    from_snapshot_at TIMESTAMPTZ,
    to_snapshot_at   TIMESTAMPTZ,
    nodes_added      INTEGER DEFAULT 0,
    nodes_removed    INTEGER DEFAULT 0,
    nodes_modified   INTEGER DEFAULT 0,
    edges_added      INTEGER DEFAULT 0,
    edges_removed    INTEGER DEFAULT 0,
    risk_delta       FLOAT DEFAULT 0,
    risk_direction   TEXT DEFAULT 'stable',
    mutation_count   INTEGER DEFAULT 0,
    critical_mutations INTEGER DEFAULT 0,
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_diff_entity ON genome_diffs(entity_id, created_at DESC);

-- ──────────────────────────────────────────────
-- VIEWS
-- ──────────────────────────────────────────────

-- Mutation rate per entity (last 24h)
CREATE VIEW mutation_rate_24h AS
SELECT
    entity_id,
    count(*)                                             AS total_mutations,
    sum(CASE WHEN severity = 'critical' THEN 1 ELSE 0 END) AS critical,
    sum(CASE WHEN severity = 'high' THEN 1 ELSE 0 END)     AS high,
    sum(risk_delta)                                      AS total_risk_delta,
    avg(EXTRACT(EPOCH FROM (detected_at - occurred_at))) AS avg_detection_lag_sec
FROM mutation_events
WHERE occurred_at > NOW() - INTERVAL '24 hours'
GROUP BY entity_id
ORDER BY critical DESC, total_mutations DESC;

-- Top mutating nodes (last 7 days)
CREATE VIEW top_mutating_nodes AS
SELECT
    node_id,
    entity_id,
    node_type,
    count(*)     AS mutation_count,
    sum(risk_delta) AS total_risk_delta,
    max(severity)   AS max_severity
FROM mutation_events
WHERE occurred_at > NOW() - INTERVAL '7 days'
GROUP BY node_id, entity_id, node_type
ORDER BY mutation_count DESC
LIMIT 100;

-- Resilience trend (last 30 days, daily aggregate)
CREATE VIEW resilience_trend_30d AS
SELECT
    entity_id,
    time_bucket('1 day', measured_at) AS day,
    avg(overall_resilience)   AS avg_resilience,
    avg(control_coverage)     AS avg_control_coverage,
    avg(patch_velocity)       AS avg_patch_velocity,
    avg(identity_hygiene)     AS avg_identity_hygiene
FROM resilience_snapshots
WHERE measured_at > NOW() - INTERVAL '30 days'
GROUP BY entity_id, day
ORDER BY entity_id, day;
