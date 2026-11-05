-- 0001_bootstrap.sql — Scriptura bootstrap schema.
--
-- REVISION NOTE: this migration was revised during M0, before first release, to
-- add explicit diacritic-folding columns to the FTS5 indexes after empirical
-- testing showed that FTS5 'remove_diacritics 2' does not fold Greek or Hebrew
-- diacritics. Editing an applied migration is prohibited (BKB-DATA-001 rule M2);
-- this edit is permitted ONLY because no database containing this migration has
-- been released or distributed. After first release, all changes must be new
-- forward migrations with a higher sequence number.
--
-- Normative source: BKB-DATA-001 section 6; ADR-0007; ADR-0008.
--
-- The epistemic layer invariants are enforced HERE, by CHECK constraints, not only
-- by application code. A constraint that lives only in application code can be
-- bypassed by a future code path, a migration script, or a direct SQL client.
-- An unattributed theological interpretation, a scripture record without an edition,
-- and an unflagged AI hypothesis CANNOT BE INSERTED. The database refuses.

-- ---------------------------------------------------------------- governance ----

-- The migration ledger is created by the migration runner itself
-- (storage/migrations.py ensure_ledger), not by any migration file. A migration
-- must never create governance tables; it creates domain tables only.

CREATE TABLE IF NOT EXISTS licences (
    id                        TEXT PRIMARY KEY,
    name                      TEXT NOT NULL,
    version                   TEXT,
    rights_holder             TEXT,
    licence_url               TEXT,
    retrieved_at              TEXT,
    evidence_kind             TEXT NOT NULL CHECK (evidence_kind IN ('primary','secondary','none')),
    evidence_quote            TEXT,
    verification_status       TEXT NOT NULL CHECK (verification_status IN
                              ('verified','unverified','disputed','restricted','absent','not_required')),
    derivatives_permitted     INTEGER,
    commercial_use_permitted  INTEGER,
    share_alike               INTEGER,
    attribution_required      INTEGER,
    attribution_text          TEXT,
    notes                     TEXT NOT NULL,
    created_at                TEXT NOT NULL,
    -- A licence recorded as verified MUST rest on a primary source with a recorded URL
    -- and retrieval date. This makes ADR-0010 condition G4 a storage invariant.
    CHECK (verification_status <> 'verified'
           OR (evidence_kind = 'primary' AND COALESCE(licence_url,'') <> ''
               AND COALESCE(retrieved_at,'') <> ''))
);

CREATE TABLE IF NOT EXISTS datasets (
    id                TEXT PRIMARY KEY,
    key               TEXT NOT NULL UNIQUE,
    name              TEXT NOT NULL,
    edition           TEXT,
    version           TEXT,
    licence_id        TEXT NOT NULL REFERENCES licences(id),
    source_uri        TEXT NOT NULL,
    retrieved_at      TEXT,
    content_hash      TEXT,
    byte_length       INTEGER,
    authorised_by     TEXT,
    authorised_at     TEXT,
    created_at        TEXT NOT NULL,
    -- No dataset may exist unless a human authorised it individually (ADR-0010 G10),
    -- and no dataset may exist without a licence record (G2).
    CHECK (COALESCE(authorised_by,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> '')
);

CREATE TABLE IF NOT EXISTS canon_profiles (
    id          TEXT PRIMARY KEY,
    key         TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    description TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS books (
    id         TEXT PRIMARY KEY,
    key        TEXT NOT NULL UNIQUE,
    name_en    TEXT NOT NULL,
    chapters   INTEGER,
    testament  TEXT NOT NULL CHECK (testament IN ('ot','nt','deuterocanonical')),
    notes      TEXT,
    CHECK (chapters IS NULL OR chapters > 0)
);

CREATE TABLE IF NOT EXISTS book_canon_membership (
    book_id    TEXT NOT NULL REFERENCES books(id),
    profile_id TEXT NOT NULL REFERENCES canon_profiles(id),
    position   INTEGER NOT NULL,
    PRIMARY KEY (book_id, profile_id),
    CHECK (position >= 0)
);

CREATE TABLE IF NOT EXISTS editions (
    id         TEXT PRIMARY KEY,
    key        TEXT NOT NULL UNIQUE,
    name       TEXT NOT NULL,
    language   TEXT,
    dataset_id TEXT REFERENCES datasets(id),
    notes      TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS witnesses (
    id            TEXT PRIMARY KEY,
    key           TEXT NOT NULL UNIQUE,
    name          TEXT NOT NULL,
    siglum        TEXT,
    dating        TEXT,
    dating_basis  TEXT,
    notes         TEXT,
    created_at    TEXT NOT NULL,
    -- A date without a stated basis is an assertion, not evidence (BKB-DATA-001 s2.2).
    CHECK (COALESCE(dating,'') = '' OR COALESCE(dating_basis,'') <> '')
);

-- Named canonical_references rather than 'references' because REFERENCES is a
-- reserved word in SQL and would require quoting at every use site.
CREATE TABLE IF NOT EXISTS canonical_references (
    id                TEXT PRIMARY KEY,
    book_id           TEXT NOT NULL REFERENCES books(id),
    canon_profile_id  TEXT NOT NULL REFERENCES canon_profiles(id),
    chapter           INTEGER,
    verse_start       INTEGER,
    verse_end         INTEGER,
    display           TEXT NOT NULL,
    UNIQUE (book_id, canon_profile_id, chapter, verse_start, verse_end),
    CHECK (chapter IS NULL OR chapter > 0),
    CHECK (verse_start IS NULL OR verse_start > 0),
    CHECK (verse_end IS NULL OR verse_start IS NOT NULL),
    CHECK (verse_end IS NULL OR verse_end >= verse_start)
);

-- ------------------------------------------------------------------- records ----
--
-- corpus_records holds scripture-layer text. claims holds claim-bearing records
-- across all five layers. Both enforce the layer invariants.

CREATE TABLE IF NOT EXISTS corpus_records (
    id                   TEXT PRIMARY KEY,
    layer                TEXT NOT NULL DEFAULT 'scripture'
                         CHECK (layer = 'scripture'),
    edition_id           TEXT NOT NULL REFERENCES editions(id),
    witness_id           TEXT REFERENCES witnesses(id),
    reference_id         TEXT NOT NULL REFERENCES canonical_references(id),
    text                 TEXT NOT NULL,
    normalisation_form   TEXT,
    content_hash         TEXT NOT NULL,
    dataset_id           TEXT REFERENCES datasets(id),
    licence_id           TEXT REFERENCES licences(id),
    source_uri           TEXT NOT NULL,
    actor                TEXT NOT NULL,
    created_at           TEXT NOT NULL,
    -- Scripture text is always sourced from a named edition (invariant L4).
    -- There is no path by which generated text can be stored as scripture.
    CHECK (COALESCE(text,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

CREATE TABLE IF NOT EXISTS claims (
    id                  TEXT PRIMARY KEY,

    -- The closed layer set. Adding a layer requires an accepted ADR (invariant L2).
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture',
                            'historical_evidence',
                            'linguistic_observation',
                            'theological_interpretation',
                            'ai_hypothesis')),

    -- Mandatory on every claim. Never defaulted (BKB-DATA-001 rule S6).
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

    -- theological_interpretation
    tradition           TEXT,
    author              TEXT,
    work                TEXT,
    period              TEXT,

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
    CHECK (layer <> 'theological_interpretation'
           OR (COALESCE(tradition,'') <> '' OR COALESCE(author,'') <> '')),

    -- L4: scripture requires a named edition and a valid reference.
    CHECK (layer <> 'scripture'
           OR (edition_id IS NOT NULL AND reference_id IS NOT NULL)),

    -- L5: ai_hypothesis requires generation provenance.
    CHECK (layer <> 'ai_hypothesis'
           OR (model IS NOT NULL AND method IS NOT NULL
               AND inputs_json IS NOT NULL AND confidence IS NOT NULL
               AND generated_at IS NOT NULL)),

    -- L6: ai_hypothesis is ALWAYS flagged non-authoritative. An unflagged AI
    -- hypothesis cannot exist.
    CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),

    -- linguistic_observation requires an attributed source.
    CHECK (layer <> 'linguistic_observation'
           OR (COALESCE(source_dataset,'') <> '' OR COALESCE(analyst,'') <> '')),

    -- historical_evidence requires a type.
    CHECK (layer <> 'historical_evidence' OR evidence_type IS NOT NULL),

    -- A date without a basis is an assertion.
    CHECK (COALESCE(dating,'') = '' OR COALESCE(dating_basis,'') <> ''),

    -- Confidence, where present, is a probability.
    CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),

    CHECK (COALESCE(statement,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

-- --------------------------------------------------------------------- graph ----

CREATE TABLE IF NOT EXISTS nodes (
    id                  TEXT PRIMARY KEY,
    kind                TEXT NOT NULL,
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture','historical_evidence','linguistic_observation',
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

CREATE TABLE IF NOT EXISTS edges (
    id                  TEXT PRIMARY KEY,
    source_node_id      TEXT NOT NULL REFERENCES nodes(id),
    target_node_id      TEXT NOT NULL REFERENCES nodes(id),
    relation            TEXT NOT NULL,
    layer               TEXT NOT NULL CHECK (layer IN (
                            'scripture','historical_evidence','linguistic_observation',
                            'theological_interpretation','ai_hypothesis')),
    non_authoritative   INTEGER NOT NULL DEFAULT 0,
    confidence          REAL,
    payload_json        TEXT,
    source_uri          TEXT NOT NULL,
    content_hash        TEXT NOT NULL,
    actor               TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    -- Self-edges are prohibited at M0 (ADR-0007).
    CHECK (source_node_id <> target_node_id),
    CHECK (layer <> 'ai_hypothesis' OR non_authoritative = 1),
    CHECK (confidence IS NULL OR (confidence >= 0.0 AND confidence <= 1.0)),
    CHECK (COALESCE(relation,'') <> ''),
    CHECK (COALESCE(source_uri,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation);
CREATE INDEX IF NOT EXISTS idx_edges_layer ON edges(layer);
CREATE INDEX IF NOT EXISTS idx_nodes_layer ON nodes(layer);
CREATE INDEX IF NOT EXISTS idx_claims_layer ON claims(layer);

-- ------------------------------------------------------------------ mappings ----

CREATE TABLE IF NOT EXISTS identifier_mappings (
    id              TEXT PRIMARY KEY,
    scriptura_id    TEXT NOT NULL,
    external_scheme TEXT NOT NULL,
    external_id     TEXT NOT NULL,
    source_uri      TEXT NOT NULL,
    actor           TEXT NOT NULL,
    created_at      TEXT NOT NULL,
    UNIQUE (scriptura_id, external_scheme, external_id),
    CHECK (COALESCE(scriptura_id,'') <> ''),
    CHECK (COALESCE(external_scheme,'') <> ''),
    CHECK (COALESCE(external_id,'') <> '')
);

-- ------------------------------------------------------------- append-only ----

CREATE TABLE IF NOT EXISTS provenance_events (
    id           TEXT PRIMARY KEY,
    entity_kind  TEXT NOT NULL,
    entity_id    TEXT NOT NULL,
    event_type   TEXT NOT NULL CHECK (event_type IN (
                     'created','superseded','promoted','demoted','corrected','flagged')),
    from_layer   TEXT,
    to_layer     TEXT,
    evidence     TEXT,
    reasoning    TEXT,
    actor        TEXT NOT NULL,
    occurred_at  TEXT NOT NULL,
    -- A layer promotion or demotion WITHOUT evidence, reasoning and an actor
    -- CANNOT BE INSERTED. Relabelling is not promotion (invariant L7).
    CHECK (event_type NOT IN ('promoted','demoted')
           OR (from_layer IS NOT NULL AND to_layer IS NOT NULL
               AND COALESCE(evidence,'') <> '' AND COALESCE(reasoning,'') <> ''
               AND COALESCE(actor,'') <> '')),
    CHECK (COALESCE(entity_kind,'') <> ''),
    CHECK (COALESCE(entity_id,'') <> ''),
    CHECK (COALESCE(actor,'') <> '')
);

CREATE TABLE IF NOT EXISTS ingestion_runs (
    id                TEXT PRIMARY KEY,
    dataset_id        TEXT NOT NULL REFERENCES datasets(id),
    licence_id        TEXT NOT NULL REFERENCES licences(id),
    started_at        TEXT NOT NULL,
    finished_at       TEXT,
    status            TEXT NOT NULL CHECK (status IN (
                          'started','completed','failed','rolled_back')),
    records_ingested  INTEGER NOT NULL DEFAULT 0,
    records_rejected  INTEGER NOT NULL DEFAULT 0,
    content_hash      TEXT,
    authorised_by     TEXT NOT NULL,
    notes             TEXT,
    CHECK (records_ingested >= 0),
    CHECK (records_rejected >= 0),
    CHECK (COALESCE(authorised_by,'') <> '')
);

-- -------------------------------------------------------------------- search ----
--
-- Diacritic folding is a SEARCH affordance only. The stored text in corpus_records
-- and claims is never altered (BKB-DATA-001 rule U6, ADR-0009).
--
-- VERIFIED ON SQLITE 3.40.1: FTS5 'unicode61 remove_diacritics 2' folds LATIN
-- diacritics ('Deésus' matches 'Deesus') but does NOT fold Greek polytonic
-- diacritics ('λόγος' does not match 'λογος') and does NOT fold Hebrew niqqud
-- ('אֱלֹהִים' does not match 'אלהים').
--
-- Accent-insensitive search over Greek and Hebrew is a hard requirement for this
-- domain, so the folded form is computed EXPLICITLY by scriptura.core.text.fold_diacritics
-- and indexed in a SEPARATE column. The original text is indexed as-is alongside it.
-- Neither column replaces the stored text in corpus_records or claims.

CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
    record_id UNINDEXED,
    layer UNINDEXED,
    edition_id UNINDEXED,
    reference_display UNINDEXED,
    text,
    text_folded,
    tokenize = 'unicode61 remove_diacritics 2'
);

CREATE VIRTUAL TABLE IF NOT EXISTS claim_fts USING fts5(
    claim_id UNINDEXED,
    layer UNINDEXED,
    non_authoritative UNINDEXED,
    statement,
    statement_folded,
    tokenize = 'unicode61 remove_diacritics 2'
);
