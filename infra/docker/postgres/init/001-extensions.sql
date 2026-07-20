-- Enable pgvector on first cluster init (M0-T14).
-- Real schema/migrations arrive in later milestones; this only makes the
-- extension available in the default database.
CREATE EXTENSION IF NOT EXISTS vector;
