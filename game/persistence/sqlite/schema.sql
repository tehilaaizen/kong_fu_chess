-- User accounts. username is the identity (unique); password_hash stores a
-- salted scrypt hash, never plaintext; rating is the ELO baseline (the
-- application supplies its default). created_at is a bookkeeping timestamp.
CREATE TABLE IF NOT EXISTS users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    rating        INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
