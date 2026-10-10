-- Mini-ELN schema for gold nanoparticle synthesis records
-- Normalized just enough to demonstrate real schema design, not over-engineered.

CREATE TABLE IF NOT EXISTS articles (
    doi TEXT PRIMARY KEY,
    year INTEGER,
    citations INTEGER
);

CREATE TABLE IF NOT EXISTS recipes (
    paragraph_id TEXT PRIMARY KEY,
    doi TEXT NOT NULL,
    seed_mediated BOOLEAN,
    target TEXT,
    conditions TEXT,
    text_snippet TEXT,
    FOREIGN KEY (doi) REFERENCES articles(doi)
);

-- One row per (recipe, precursor) pair instead of one big semicolon-joined string.
-- This is what actually makes it queryable like a real ELN.
CREATE TABLE IF NOT EXISTS precursors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    paragraph_id TEXT NOT NULL,
    material TEXT NOT NULL,
    amount TEXT,
    FOREIGN KEY (paragraph_id) REFERENCES recipes(paragraph_id)
);

CREATE TABLE IF NOT EXISTS characterization (
    paragraph_id TEXT PRIMARY KEY,
    doi TEXT NOT NULL,
    morphologies TEXT,
    sizes TEXT,
    units TEXT,
    text_snippet TEXT,
    FOREIGN KEY (doi) REFERENCES articles(doi)
);

CREATE INDEX IF NOT EXISTS idx_precursors_material ON precursors(material);
CREATE INDEX IF NOT EXISTS idx_recipes_doi ON recipes(doi);

-- Records imported from a laboratory CSV or instrument-export workflow.
-- source_file and imported_at retain basic provenance for every record.
CREATE TABLE IF NOT EXISTS lab_experiments (
    experiment_id TEXT PRIMARY KEY,
    experiment_date TEXT NOT NULL,
    operator TEXT NOT NULL,
    sample_id TEXT NOT NULL,
    procedure TEXT NOT NULL,
    conditions TEXT,
    outcome TEXT NOT NULL,
    instrument TEXT,
    source_file TEXT NOT NULL,
    imported_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lab_experiments_sample_id ON lab_experiments(sample_id);
