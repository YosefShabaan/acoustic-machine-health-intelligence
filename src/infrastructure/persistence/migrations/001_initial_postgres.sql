-- Fan Production MVP persistence schema.
-- Target database: PostgreSQL.
-- Raw audio bytes, NumPy arrays, embeddings, model weights, and generated
-- scientific artifacts are intentionally not stored in relational rows.

CREATE TABLE IF NOT EXISTS events (
  event_id TEXT PRIMARY KEY,
  machine_type TEXT NOT NULL,
  machine_id TEXT NOT NULL,
  snr_tag TEXT NOT NULL,
  audio_reference TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('queued', 'processing', 'completed', 'failed')),
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL,
  error_code TEXT,
  error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_events_status_created
  ON events(status, created_at);

CREATE INDEX IF NOT EXISTS idx_events_machine_created
  ON events(machine_type, machine_id, created_at);

CREATE TABLE IF NOT EXISTS analysis_runs (
  analysis_run_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
  pipeline_version TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('processing', 'completed', 'failed')),
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  total_duration DOUBLE PRECISION,
  artifact_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_code TEXT,
  error_summary TEXT
);

CREATE INDEX IF NOT EXISTS idx_analysis_runs_event
  ON analysis_runs(event_id, started_at);

CREATE TABLE IF NOT EXISTS analysis_results (
  analysis_run_id TEXT PRIMARY KEY REFERENCES analysis_runs(analysis_run_id) ON DELETE CASCADE,
  expert_a_result JSONB NOT NULL,
  expert_b_evidence JSONB,
  structured_context JSONB,
  retrieval_metadata JSONB,
  explanation_output JSONB,
  maintenance_output JSONB,
  timing_metadata JSONB NOT NULL
);
