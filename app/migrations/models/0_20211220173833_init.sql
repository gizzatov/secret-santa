-- upgrade --
CREATE TABLE IF NOT EXISTS "users" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "chat_id" VARCHAR(100)  UNIQUE,
    "username" VARCHAR(100),
    "full_name" VARCHAR(150) NOT NULL,
    "is_active" BOOL NOT NULL  DEFAULT True,
    "is_moderator" BOOL NOT NULL  DEFAULT False,
    "is_tg_user" BOOL NOT NULL  DEFAULT True,
    "preferences" TEXT NOT NULL,
    "description" TEXT NOT NULL,
    "extra" JSONB NOT NULL
);
CREATE TABLE IF NOT EXISTS "games" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "code" VARCHAR(100) NOT NULL UNIQUE,
    "group_chat_id" VARCHAR(100)  UNIQUE,
    "description" TEXT NOT NULL,
    "started_at" DATE NOT NULL,
    "submitting_finished_at" DATE NOT NULL,
    "finished_at" DATE NOT NULL,
    "status" VARCHAR(20) NOT NULL  DEFAULT 'new',
    "extra" JSONB NOT NULL,
    "admin_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
COMMENT ON COLUMN "games"."status" IS 'NEW: new\nSANTAS_SELECTED: santas_selected\nSANTAS_REVEALED: santas_revealed';
CREATE TABLE IF NOT EXISTS "pairs" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "code" VARCHAR(100) NOT NULL UNIQUE,
    "is_revealed" BOOL NOT NULL  DEFAULT False,
    "is_notified" BOOL NOT NULL  DEFAULT False,
    "extra" JSONB NOT NULL,
    "game_id" INT NOT NULL REFERENCES "games" ("id") ON DELETE CASCADE,
    "santa_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    "target_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE,
    CONSTRAINT "uid_pairs_game_id_d96d3a" UNIQUE ("game_id", "santa_id", "target_id")
);
CREATE TABLE IF NOT EXISTS "players" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMPTZ NOT NULL  DEFAULT CURRENT_TIMESTAMP,
    "extra" JSONB NOT NULL,
    "game_id" INT NOT NULL REFERENCES "games" ("id") ON DELETE CASCADE,
    "user_id" INT NOT NULL REFERENCES "users" ("id") ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS "aerich" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "version" VARCHAR(255) NOT NULL,
    "app" VARCHAR(20) NOT NULL,
    "content" JSONB NOT NULL
);
