-- AEGIS OMEGA X — MEGA LAYER 3
-- GLOBAL SECURITY KNOWLEDGE UNIVERSE — DATABASE SCHEMA
-- PostgreSQL + TimescaleDB + pg_trgm + btree_gin

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";
CREATE EXTENSION IF NOT EXISTS "timescaledb";
CREATE EXTENSION IF NOT EXISTS "vector";     -- pgvector for embeddings

CREATE SCHEMA IF NOT EXISTS knowledge;
SET search_path TO knowledge, public;

-- ──────────────────────────────────────────────
-- KNOWLEDGE NODES (Relational mirror)
-- ──────────────────────────────────────────────
CREATE TABLE knowledge_nodes (
    node_id          TEXT PRIMARY KEY,
    node_type        TEXT NOT NULL,
    name             TEXT NOT NULL,
    description      TEXT,
    aliases          TEXT[],
    confidence       TEXT DEFAULT 'high',
    tlp_marking      TEXT DEFAULT 'WHITE',
    sources          TEXT[],
    stix_id          TEXT,
    external_refs    JSONB DEFAULT '{}',
    embedding        vector(1536),      -- pgvector column
    deprecated       BOOLEAN DEFAULT FALSE,
    tags             TEXT[],
    properties       JSONB DEFAULT '{}',
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_kn_type        ON knowledge_nodes(node_type);
CREATE INDEX idx_kn_name_trgm   ON knowledge_nodes USING gin(name gin_trgm_ops);
CREATE INDEX idx_kn_desc_trgm   ON knowledge_nodes USING gin(description gin_trgm_ops);
CREATE INDEX idx_kn_tags        ON knowledge_nodes USING gin(tags);
CREATE INDEX idx_kn_sources     ON knowledge_nodes USING gin(sources);
CREATE INDEX idx_kn_stix        ON knowledge_nodes(stix_id) WHERE stix_id IS NOT NULL;
CREATE INDEX idx_kn_embedding   ON knowledge_nodes USING hnsw (embedding vector_cosine_ops);

-- ──────────────────────────────────────────────
-- CVE TABLE (Specialized)
-- ──────────────────────────────────────────────
CREATE TABLE cves (
    cve_id           TEXT PRIMARY KEY,
    node_id          TEXT REFERENCES knowledge_nodes(node_id),
    cvss_v3_score    FLOAT,
    cvss_v3_vector   TEXT,
    cvss_v2_score    FLOAT,
    severity         TEXT,
    epss_score       FLOAT,
    epss_percentile  FLOAT,
    published        TIMESTAMPTZ,
    last_modified    TIMESTAMPTZ,
    cwe_ids          TEXT[],
    affected_software TEXT[],
    patch_available  BOOLEAN DEFAULT FALSE,
    exploited_wild   BOOLEAN DEFAULT FALSE,
    kev_listed       BOOLEAN DEFAULT FALSE,
    exploit_code     BOOLEAN DEFAULT FALSE,
    exploit_maturity TEXT DEFAULT 'unproven',
    attack_vector    TEXT,
    attack_complexity TEXT,
    privileges_req   TEXT,
    user_interaction TEXT,
    techniques_map   TEXT[]
);

CREATE INDEX idx_cve_score    ON cves(cvss_v3_score DESC);
CREATE INDEX idx_cve_epss     ON cves(epss_score DESC NULLS LAST);
CREATE INDEX idx_cve_kev      ON cves(kev_listed) WHERE kev_listed = TRUE;
CREATE INDEX idx_cve_wild     ON cves(exploited_wild) WHERE exploited_wild = TRUE;
CREATE INDEX idx_cve_severity ON cves(severity);
CREATE INDEX idx_cve_published ON cves(published DESC NULLS LAST);
CREATE INDEX idx_cve_software  ON cves USING gin(affected_software);
CREATE INDEX idx_cve_cwes      ON cves USING gin(cwe_ids);

-- ──────────────────────────────────────────────
-- THREAT ACTORS
-- ──────────────────────────────────────────────
CREATE TABLE threat_actors (
    node_id          TEXT PRIMARY KEY REFERENCES knowledge_nodes(node_id),
    actor_type       TEXT,
    nation_state     TEXT,
    motivation       TEXT[],
    sophistication   TEXT,
    active_since     TIMESTAMPTZ,
    last_seen        TIMESTAMPTZ,
    target_sectors   TEXT[],
    target_countries TEXT[],
    threat_score     FLOAT,
    ioc_count        INTEGER DEFAULT 0,
    technique_count  INTEGER DEFAULT 0,
    incident_count   INTEGER DEFAULT 0,
    mitre_groups     TEXT[]
);

CREATE INDEX idx_actor_nation  ON threat_actors(nation_state);
CREATE INDEX idx_actor_type    ON threat_actors(actor_type);
CREATE INDEX idx_actor_score   ON threat_actors(threat_score DESC NULLS LAST);
CREATE INDEX idx_actor_sectors ON threat_actors USING gin(target_sectors);

-- ──────────────────────────────────────────────
-- MITRE ATT&CK TECHNIQUES
-- ──────────────────────────────────────────────
CREATE TABLE techniques (
    node_id          TEXT PRIMARY KEY REFERENCES knowledge_nodes(node_id),
    technique_id     TEXT UNIQUE NOT NULL,
    tactic_ids       TEXT[],
    platforms        TEXT[],
    permissions_req  TEXT[],
    data_sources     TEXT[],
    defenses_bypassed TEXT[],
    is_sub_technique BOOLEAN DEFAULT FALSE,
    parent_technique TEXT,
    usage_in_wild    BOOLEAN DEFAULT FALSE,
    prevalence_score FLOAT DEFAULT 0
);

CREATE INDEX idx_tech_id        ON techniques(technique_id);
CREATE INDEX idx_tech_platforms ON techniques USING gin(platforms);
CREATE INDEX idx_tech_tactics   ON techniques USING gin(tactic_ids);
CREATE INDEX idx_tech_prevalence ON techniques(prevalence_score DESC);

-- ──────────────────────────────────────────────
-- DETECTION RULES
-- ──────────────────────────────────────────────
CREATE TABLE detection_rules (
    node_id          TEXT PRIMARY KEY REFERENCES knowledge_nodes(node_id),
    rule_id          TEXT UNIQUE,
    rule_type        TEXT,
    rule_content     TEXT,
    techniques_covered TEXT[],
    platforms        TEXT[],
    log_sources      TEXT[],
    false_positive_rate FLOAT DEFAULT 0,
    true_positive_rate  FLOAT DEFAULT 0,
    severity_level   TEXT DEFAULT 'medium',
    status           TEXT DEFAULT 'stable',
    author           TEXT,
    license          TEXT
);

CREATE INDEX idx_rule_type      ON detection_rules(rule_type);
CREATE INDEX idx_rule_status    ON detection_rules(status);
CREATE INDEX idx_rule_techniques ON detection_rules USING gin(techniques_covered);
CREATE INDEX idx_rule_platforms  ON detection_rules USING gin(platforms);

-- ──────────────────────────────────────────────
-- KNOWLEDGE EDGES (Relational)
-- ──────────────────────────────────────────────
CREATE TABLE knowledge_edges (
    edge_id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_id        TEXT NOT NULL,
    target_id        TEXT NOT NULL,
    edge_type        TEXT NOT NULL,
    confidence       TEXT DEFAULT 'high',
    weight           FLOAT DEFAULT 1.0,
    inferred         BOOLEAN DEFAULT FALSE,
    inference_rule   TEXT,
    sources          TEXT[],
    stix_rel_id      TEXT,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    metadata         JSONB DEFAULT '{}'
);

CREATE INDEX idx_edge_source ON knowledge_edges(source_id);
CREATE INDEX idx_edge_target ON knowledge_edges(target_id);
CREATE INDEX idx_edge_type   ON knowledge_edges(edge_type);
CREATE INDEX idx_edge_infer  ON knowledge_edges(inferred) WHERE inferred = TRUE;
CREATE UNIQUE INDEX idx_edge_unique ON knowledge_edges(source_id, target_id, edge_type);

-- ──────────────────────────────────────────────
-- INCIDENTS
-- ──────────────────────────────────────────────
CREATE TABLE incidents (
    node_id            TEXT PRIMARY KEY REFERENCES knowledge_nodes(node_id),
    incident_type      TEXT,
    victim_sector      TEXT,
    victim_country     TEXT,
    attack_vector      TEXT,
    techniques_used    TEXT[],
    impact_type        TEXT[],
    economic_loss_usd  NUMERIC(20,2),
    records_exposed    BIGINT,
    attributed_actor   TEXT,
    occurred_at        TIMESTAMPTZ,
    disclosed_at       TIMESTAMPTZ,
    contained_at       TIMESTAMPTZ,
    dwell_time_days    INTEGER,
    source_url         TEXT
);

SELECT create_hypertable('incidents', 'occurred_at',
    if_not_exists => TRUE, migrate_data => TRUE);
CREATE INDEX idx_incident_sector   ON incidents(victim_sector);
CREATE INDEX idx_incident_country  ON incidents(victim_country);
CREATE INDEX idx_incident_occurred ON incidents(occurred_at DESC NULLS LAST);
CREATE INDEX idx_incident_actor    ON incidents(attributed_actor);

-- ──────────────────────────────────────────────
-- IOCs (Time-series)
-- ──────────────────────────────────────────────
CREATE TABLE iocs (
    ioc_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    node_id          TEXT,
    ioc_type         TEXT NOT NULL,
    value            TEXT NOT NULL,
    confidence       TEXT DEFAULT 'medium',
    first_seen       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen        TIMESTAMPTZ,
    active           BOOLEAN DEFAULT TRUE,
    malware_family   TEXT,
    campaign         TEXT,
    threat_actor     TEXT,
    tlp              TEXT DEFAULT 'AMBER',
    sources          TEXT[],
    kill_chain_phases TEXT[]
);

SELECT create_hypertable('iocs', 'first_seen',
    if_not_exists => TRUE, migrate_data => TRUE);
CREATE INDEX idx_ioc_type     ON iocs(ioc_type, first_seen DESC);
CREATE INDEX idx_ioc_value    ON iocs(value);
CREATE INDEX idx_ioc_actor    ON iocs(threat_actor);
CREATE INDEX idx_ioc_campaign ON iocs(campaign);
CREATE INDEX idx_ioc_active   ON iocs(active, first_seen DESC);

-- ──────────────────────────────────────────────
-- KNOWLEDGE INGESTION LOG (Time-series)
-- ──────────────────────────────────────────────
CREATE TABLE ingestion_log (
    log_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    source_name      TEXT NOT NULL,
    ingestion_type   TEXT,
    nodes_ingested   INTEGER DEFAULT 0,
    edges_ingested   INTEGER DEFAULT 0,
    errors           INTEGER DEFAULT 0,
    duration_seconds FLOAT,
    started_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at     TIMESTAMPTZ,
    status           TEXT DEFAULT 'running',
    metadata         JSONB DEFAULT '{}'
);

SELECT create_hypertable('ingestion_log', 'started_at',
    if_not_exists => TRUE, migrate_data => TRUE);

-- ──────────────────────────────────────────────
-- INFERENCE LOG (Time-series)
-- ──────────────────────────────────────────────
CREATE TABLE inference_log (
    log_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    run_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    rule_id          TEXT NOT NULL,
    inferences_created INTEGER DEFAULT 0,
    duration_ms      FLOAT,
    ran_at           TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('inference_log', 'ran_at',
    if_not_exists => TRUE, migrate_data => TRUE);

-- ──────────────────────────────────────────────
-- SEMANTIC SEARCH LOG (Time-series, for analytics)
-- ──────────────────────────────────────────────
CREATE TABLE search_log (
    log_id           UUID NOT NULL DEFAULT uuid_generate_v4(),
    query_text       TEXT,
    query_embedding_hash TEXT,
    node_types_filter TEXT[],
    result_count     INTEGER,
    top_result_id    TEXT,
    top_result_score FLOAT,
    duration_ms      FLOAT,
    user_id          TEXT,
    searched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

SELECT create_hypertable('search_log', 'searched_at',
    if_not_exists => TRUE, migrate_data => TRUE);

-- ──────────────────────────────────────────────
-- COMPLIANCE FRAMEWORK CONTROLS
-- ──────────────────────────────────────────────
CREATE TABLE compliance_controls (
    control_id       TEXT PRIMARY KEY,
    framework_id     TEXT NOT NULL,
    framework_version TEXT,
    name             TEXT NOT NULL,
    description      TEXT,
    category         TEXT,
    sub_category     TEXT,
    implementation_groups TEXT[],
    techniques_mitigated TEXT[],
    implementation_cost TEXT,
    effectiveness    FLOAT,
    automation_level TEXT,
    cross_mappings   JSONB DEFAULT '{}'      -- {ISO27001: 'A.9.1', NIST: 'AC-1', ...}
);

CREATE INDEX idx_ctrl_framework ON compliance_controls(framework_id);
CREATE INDEX idx_ctrl_category  ON compliance_controls(category);
CREATE INDEX idx_ctrl_techniques ON compliance_controls USING gin(techniques_mitigated);

-- ──────────────────────────────────────────────
-- VECTOR SIMILARITY SEARCH FUNCTION
-- ──────────────────────────────────────────────
CREATE OR REPLACE FUNCTION semantic_search_nodes(
    query_embedding vector(1536),
    top_k INTEGER DEFAULT 20,
    node_type_filter TEXT DEFAULT NULL
)
RETURNS TABLE (
    node_id    TEXT,
    node_type  TEXT,
    name       TEXT,
    description TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        n.node_id,
        n.node_type,
        n.name,
        n.description,
        (1 - (n.embedding <=> query_embedding)) AS similarity
    FROM knowledge_nodes n
    WHERE n.embedding IS NOT NULL
      AND (node_type_filter IS NULL OR n.node_type = node_type_filter)
    ORDER BY n.embedding <=> query_embedding
    LIMIT top_k;
END;
$$ LANGUAGE plpgsql;

-- ──────────────────────────────────────────────
-- MATERIALIZED VIEWS (Refreshed periodically)
-- ──────────────────────────────────────────────

-- Top CVEs by composite risk (CVSS × EPSS)
CREATE MATERIALIZED VIEW top_risk_cves AS
SELECT
    c.cve_id,
    n.name,
    n.description,
    c.cvss_v3_score,
    c.epss_score,
    c.kev_listed,
    c.exploited_wild,
    c.severity,
    (c.cvss_v3_score * COALESCE(c.epss_score, 0.01)) AS composite_risk,
    array_length(c.affected_software, 1) AS affected_product_count
FROM cves c
JOIN knowledge_nodes n ON c.node_id = n.node_id
WHERE NOT n.deprecated
ORDER BY composite_risk DESC;

CREATE UNIQUE INDEX ON top_risk_cves(cve_id);

-- Threat actor technique coverage
CREATE MATERIALIZED VIEW actor_technique_coverage AS
SELECT
    ke.source_id AS actor_id,
    ta.nation_state,
    count(DISTINCT ke.target_id) AS technique_count,
    array_agg(DISTINCT t.technique_id) AS technique_ids
FROM knowledge_edges ke
JOIN threat_actors ta ON ke.source_id = ta.node_id
JOIN techniques t ON ke.target_id = t.node_id
WHERE ke.edge_type = 'USES'
GROUP BY ke.source_id, ta.nation_state;

CREATE UNIQUE INDEX ON actor_technique_coverage(actor_id);

-- Detection coverage per technique
CREATE MATERIALIZED VIEW technique_detection_coverage AS
SELECT
    t.technique_id,
    n.name AS technique_name,
    count(DISTINCT ke.source_id) AS rule_count,
    array_agg(DISTINCT dr.rule_type) AS rule_types
FROM techniques t
JOIN knowledge_nodes n ON t.node_id = n.node_id
LEFT JOIN knowledge_edges ke ON ke.target_id = t.node_id AND ke.edge_type = 'DETECTS'
LEFT JOIN detection_rules dr ON ke.source_id = dr.node_id
GROUP BY t.technique_id, n.name;

CREATE UNIQUE INDEX ON technique_detection_coverage(technique_id);
