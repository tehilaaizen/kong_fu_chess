-- User accounts. username is the identity (unique); password_hash stores a
-- salted scrypt hash, never plaintext; rating is the ELO baseline (the
-- application supplies its default). created_at is a bookkeeping timestamp.
CREATE TABLE IF NOT EXISTS users (
    username      TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    rating        INTEGER NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Per-game rating changes. One row per player per finished game; the
-- (game_id, username) primary key makes applying a game's result idempotent
-- - a second attempt to record the same game hits the constraint and is
-- rejected, so a rating never moves twice for one game.
CREATE TABLE IF NOT EXISTS rating_changes (
    game_id    TEXT NOT NULL,
    username   TEXT NOT NULL,
    old_rating INTEGER NOT NULL,
    new_rating INTEGER NOT NULL,
    changed_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (game_id, username)
);
