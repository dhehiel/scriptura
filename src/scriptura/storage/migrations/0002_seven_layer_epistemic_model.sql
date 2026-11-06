-- 0002_seven_layer_epistemic_model.sql
--
-- Normative source: ADR-0011 (supersedes ADR-0008); BKB-DATA-001 v1.1.0.
--
-- FORWARD-ONLY. Migration 0001 is never edited (BKB-DATA-001 rule M2).
--
-- What this migration does:
--   1. Widens the layer CHECK constraints on claims, nodes, and edges from the
--      M0 five-value set to the seven-value set (adds textual_observation and
--      scholarly_interpretation).
--   2. Adds nullable, layer-specific columns for the two new layers on claims
--      (conditional validation: each is enforced ONLY for its own layer via
--      CHECK guards; unrelated layers never require them -- ADR-0011 refinement 2).
--   3. Adds verification_status and supporting_evidence to edges (independent
--      dimensions; relationships retain evidence and verification state).
--   4. Adds the derivations table (BKB-DATA-001 section 2.5, ADR-0011 refinement 1).
--   5. Preserves ALL existing rows and identifiers: claims/nodes/edges are rebuilt
--      by INSERT INTO ... SELECT, which copies ids verbatim. No record is
--      reclassified: the layer column is copied unchanged. (At M0 there are zero
--      corpus/claim/node/edge rows; the preservation path is tested on synthetic
--      rows in tests/test_storage.py.)
--   6. Does NOT touch provenance_events, ingestion_runs, or any audit history.
--   7. No universal layer-strength assumption exists in SQL (ADR-0011 removed
--      ranking from the API); nothing in this migration orders layers.
--
-- SQLite cannot ALTER a CHECK constraint. Each affected table is rebuilt via the
-- standard create-copy-drop-rename sequence. Indexes travel with the rename; the
-- layer index is re-created explicitly afterwards for clarity.
--
-- Recovery / rollback limitations (documented, not hidden):
--   * This migration has NO down-migration (rule M8). Reversal would require a
--     new forward migration that narrows the CHECKs -- which would FAIL if any
--     row uses textual_observation or scholarly_interpretation. Before any
--     reversal attempt, inventory those rows; reversal is impossible while they
--     exist.
--   * If this file is edited after being applied, the ledger hash check
--     (verify_ledger) raises a Critical integrity incident (rule M7). Never edit
--     an applied migration; add a new one.
--   * If a rebuild fails mid-script, the ledger is not updated and re-running is
--     safe: DROP TABLE IF EXISTS x_new guards clear partial state. Take a file
--     copy of the database before applying to a database that holds real data.

-- -------------------------------------------------------- derivations ----
-- BKB-DATA-001 section 2.5; ADR-0011 refinement 1. Multiple outputs from
-- multiple inputs, with method, actor, timestamps, tool identity, verification,
-- evidence, and preserved disagreements. Output layers are EXPLICIT: this table
-- never computes a layer from its inputs.

CREATE TABLE IF NOT EXISTS derivations (
    id                  TEXT PRIMARY KEY,
    output_ids          TEXT NOT NULL,   -- JSON array of output record ids
    output_layers       TEXT NOT NULL,   -- JSON array, aligned with output_ids
    input_ids           TEXT NOT NULL,   -- JSON array of input record ids
    input_layers        TEXT NOT NULL,   -- JSON array, aligned with input_ids
    method              TEXT NOT NULL,
    parameters_json     TEXT,
    actor               TEXT NOT NULL,
    tool_identity       TEXT,
    tool_version        TEXT,
    created_at          TEXT NOT NULL,
    verification_state  TEXT,
    reviewer            TEXT,
    decision_authority  TEXT,
    evidence_json       TEXT,            -- supporting evidence + provenance
    disagreements_json  TEXT,            -- competing interpretations preserved
    source_uri          TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    CHECK (COALESCE(output_ids,'') <> ''),
    CHECK (COALESCE(output_layers,'') <> ''),
    CHECK (COALESCE(input_ids,'') <> ''),
    CHECK (COALESCE(input_layers,'') <> ''),
    CHECK (COALESCE(method,'') <> ''),
    CHECK (COALESCE(actor,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    -- A verified/refuted/contested derivation names its reviewer and authority.
    CHECK (verification_state IS NULL OR verification_state IN (
            'unverified','weakly_supported','supported','contested','refuted',
            'unknown','out_of_scope')),
    CHECK (verification_state NOT IN ('supported','refuted','contested')
           OR (COALESCE(reviewer,'') <> '' AND COALESCE(decision_authority,'') <> ''))
);

CREATE INDEX IF NOT EXISTS idx_derivation_actor ON derivations(actor);

-- FK window: table rebuilds DROP parents while children still reference them
-- (edges -> nodes), which foreign_keys=ON rejects via the implicit DELETE.
-- executescript() runs outside a transaction, so these pragmas take effect
-- immediately. Rows are copied from tables that already satisfied the FKs, so
-- no validation is lost. The runner re-asserts foreign_keys=ON afterwards.
PRAGMA foreign_keys=OFF;

-- ------------------------------------------------------------ claims ----

DROP TABLE IF EXISTS claims_new;

CREATE TABLE claims_new (
    id                  TEXT PRIMARY KEY,

    -- SEVEN-value closed set (ADR-0011). Adding a layer requires an accepted ADR.
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture',
                            'textual_observation',
                            'linguistic_observation',
                            'historical_evidence',
                            'scholarly_interpretation',
                            'theological_interpretation',
                            'ai_hypothesis')),

    non_authoritative   INTEGER NOT NULL DEFAULT 0,
    statement           TEXT NOT NULL,
    reference_id        TEXT REFERENCES canonical_references(id),
    confidence          REAL,
    verification_state  TEXT CHECK (verification_state IS NULL OR verification_state IN (
                            'unverified','weakly_supported','supported','contested',
                            'refuted','unknown','out_of_scope')),

    -- scripture
    edition_id          TEXT REFERENCES editions(id),
    witness_id          TEXT REFERENCES witnesses(id),

    -- historical_evidence
    evidence_type       TEXT,
    evidence_identifier TEXT,
    dating              TEXT,
    dating_basis        TEXT,

    -- linguistic_observation
    observation_type    TEXT,
    linguistic_form     TEXT,
    analysis            TEXT,
    source_dataset      TEXT,
    analyst             TEXT,

    -- textual_observation (new columns, nullable: only required for that layer)
    compared_witnesses  TEXT,
    readings_compared   TEXT,
    observation_method  TEXT,

    -- scholarly_interpretation (new columns, nullable: only required for that layer)
    scholar             TEXT,
    publication_meta    TEXT,
    supporting_refs     TEXT,

    -- theological_interpretation / scholarly shared
    tradition           TEXT,
    author              TEXT,
    work                TEXT,
    period              TEXT,
    interpretive_context TEXT,

    -- ai_hypothesis
    model               TEXT,
    method              TEXT,
    inputs_json         TEXT,
    generated_at        TEXT,

    -- provenance (no orphan records)
    source_uri          TEXT NOT NULL,
    source_kind         TEXT NOT NULL CHECK (source_kind IN
                            ('primary','secondary','derived','generated')),
    content_hash        TEXT NOT NULL,
    dataset_id          TEXT REFERENCES datasets(id),
    licence_id          TEXT REFERENCES licences(id),
    actor               TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    supersedes          TEXT REFERENCES claims(id),

    -- L3: theological_interpretation requires a named tradition or author.
    -- Parentheses make the guard apply to the WHOLE requirement (conditional
    -- validation: other layers never require tradition/author).
    CHECK (layer <> 'theological_interpretation'
           OR ((COALESCE(tradition,'') <> '' OR COALESCE(author,'') <> '')
               AND COALESCE(statement,'') <> '')),

    -- L3b: scholarly_interpretation requires (scholar OR author) AND work AND
    -- publication metadata AND supporting references. NEVER applies to other
    -- layers (conditional validation, ADR-0011 refinement 2).
    CHECK (layer <> 'scholarly_interpretation'
           OR ((COALESCE(scholar,'') <> '' OR COALESCE(author,'') <> '')
               AND COALESCE(work,'') <> ''
               AND COALESCE(publication_meta,'') <> ''
               AND COALESCE(supporting_refs,'') <> ''
               AND COALESCE(statement,'') <> '')),

    -- L3c: textual_observation requires a reference, compared witnesses,
    -- readings, an attributed observer, and a method. NEVER applies elsewhere.
    CHECK (layer <> 'textual_observation'
           OR (reference_id IS NOT NULL
               AND COALESCE(compared_witnesses,'') <> ''
               AND COALESCE(readings_compared,'') <> ''
               AND (COALESCE(source_dataset,'') <> '' OR COALESCE(analyst,'') <> '')
               AND (COALESCE(observation_method,'') <> ''
                    OR COALESCE(observation_type,'') <> ''))),

    -- L4: scripture requires a named edition and a valid reference.
    CHECK (layer <> 'scripture'
           OR (edition_id IS NOT NULL AND reference_id IS NOT NULL)),

    -- L5: ai_hypothesis requires generation provenance. confidence is IF SUPPLIED
    -- (ADR-0011): optional, and never a determinant of layer (L11).
    CHECK (layer <> 'ai_hypothesis'
           OR (model IS NOT NULL AND method IS NOT NULL
               AND inputs_json IS NOT NULL
               AND generated_at IS NOT NULL)),

    -- L6: ai_hypothesis is ALWAYS flagged non-authoritative.
    CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),

    -- linguistic_observation requires an attributed source.
    CHECK (layer <> 'linguistic_observation'
           OR (COALESCE(source_dataset,'') <> '' OR COALESCE(analyst,'') <> '')),

    -- historical_evidence requires a type.
    CHECK (layer <> 'historical_evidence' OR evidence_type IS NOT NULL),

    -- A date without a basis is an assertion (conditional requirement).
    CHECK (COALESCE(dating,'') = '' OR COALESCE(dating_basis,'') <> ''),

    -- Confidence, where present, is a probability. It NEVER determines layer.
    CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),

    CHECK (COALESCE(statement,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

-- Preserve ALL existing rows and identifiers, verbatim. layer is copied
-- UNCHANGED: no record is silently reclassified (directive section 7).
-- EXPLICIT column list is mandatory here: the new nullable columns sit in the
-- MIDDLE of claims_new, so a bare SELECT * would misalign every column from
-- `analyst` onward and silently corrupt data.
INSERT INTO claims_new
    (id, layer, non_authoritative, statement, reference_id, confidence,
     verification_state, edition_id, witness_id, evidence_type,
     evidence_identifier, dating, dating_basis, observation_type,
     linguistic_form, analysis, source_dataset, analyst, tradition, author,
     work, period, model, method, inputs_json, generated_at, source_uri,
     source_kind, content_hash, dataset_id, licence_id, actor, created_at,
     supersedes)
SELECT id, layer, non_authoritative, statement, reference_id, confidence,
       verification_state, edition_id, witness_id, evidence_type,
       evidence_identifier, dating, dating_basis, observation_type,
       linguistic_form, analysis, source_dataset, analyst, tradition, author,
       work, period, model, method, inputs_json, generated_at, source_uri,
       source_kind, content_hash, dataset_id, licence_id, actor, created_at,
       supersedes
FROM claims;

DROP TABLE claims;
ALTER TABLE claims_new RENAME TO claims;

CREATE INDEX IF NOT EXISTS idx_claims_layer ON claims(layer);
CREATE INDEX IF NOT EXISTS idx_claims_verification ON claims(verification_state);

-- ------------------------------------------------------------- nodes ----

DROP TABLE IF EXISTS nodes_new;

CREATE TABLE nodes_new (
    id                  TEXT PRIMARY KEY,
    kind                TEXT NOT NULL,
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture','textual_observation','linguistic_observation',
                            'historical_evidence','scholarly_interpretation',
                            'theological_interpretation','ai_hypothesis')),
    label               TEXT NOT NULL,
    reference_id        TEXT REFERENCES canonical_references(id),
    payload_json        TEXT,
    non_authoritative   INTEGER NOT NULL DEFAULT 0,
    source_uri          TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    actor               TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),
    CHECK (COALESCE(kind,'') <> ''),
    CHECK (COALESCE(label,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

-- Explicit column list (identical order to 0001, written out so a future
-- column addition cannot silently misalign the copy).
INSERT INTO nodes_new
    (id, kind, layer, label, reference_id, payload_json, non_authoritative,
     source_uri, content_hash, actor, created_at)
SELECT id, kind, layer, label, reference_id, payload_json, non_authoritative,
       source_uri, content_hash, actor, created_at
FROM nodes;

DROP TABLE nodes;
ALTER TABLE nodes_new RENAME TO nodes;

CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer);

-- ------------------------------------------------------------- edges ----

DROP TABLE IF EXISTS edges_new;

CREATE TABLE edges_new (
    id                  TEXT PRIMARY KEY,
    source_node_id      TEXT NOT NULL REFERENCES nodes(id),
    target_node_id      TEXT NOT NULL REFERENCES nodes(id),
    relation            TEXT NOT NULL,
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture','textual_observation','linguistic_observation',
                            'historical_evidence','scholarly_interpretation',
                            'theological_interpretation','ai_hypothesis')),
    non_authoritative   INTEGER NOT NULL DEFAULT 0,
    confidence          REAL,
    payload_json        TEXT,
    source_uri          TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    actor               TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    -- Independent dimensions retained on every relationship (BKB-DATA-001 6.5).
    verification_status TEXT,
    supporting_evidence TEXT,
    -- A non-ai_hypothesis edge must trace to an authorised derivation record
    -- (DKF-ARCH-001 XL2; no agent writes authoritative edges directly).
    derivation_id       TEXT REFERENCES derivations(id),
    CHECK (source_node_id <> target_node_id),
    CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),
    CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0))
);

-- New columns verification_status/supporting_evidence/derivation_id have no
-- counterpart in the old table: insert by explicit column list.
INSERT INTO edges_new
    (id, source_node_id, target_node_id, relation, layer, non_authoritative,
     confidence, payload_json, source_uri, content_hash, actor, created_at)
SELECT id, source_node_id, target_node_id, relation, layer, non_authoritative,
       confidence, payload_json, source_uri, content_hash, actor, created_at
FROM edges;

DROP TABLE edges;
ALTER TABLE edges_new RENAME TO edges;

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation);
CREATE INDEX IF NOT EXISTS idx_edges_layer ON edges(layer);

-- Note: the migration runner records this file in schema_migrations with its
-- SHA-256. Provenance history (provenance_events), ingestion_runs, datasets,
-- licences, and all identifiers are untouched.

-- End of rebuild window: restore FK enforcement for this connection.
PRAGMA foreign_keys=ON;
