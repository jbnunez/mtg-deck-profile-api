import os
import psycopg2
from decouple import config


def get_connection():
    return psycopg2.connect(
        dbname=config("DB_NAME", default="mtg_deck_profile"),
        user=config("DB_USER", default="postgres"),
        password=config("DB_PASSWORD", default=""),
        host=config("DB_HOST", default="localhost"),
        port=config("DB_PORT", default="5432"),
    )


def create_user_logins_table():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_logins (
                    id       BIGSERIAL    PRIMARY KEY,
                    email    VARCHAR(255) NOT NULL UNIQUE,
                    name     VARCHAR(255) NOT NULL,
                    password VARCHAR(255) NOT NULL
                );
            """)
        print("Table 'user_logins' created (or already exists).")
    finally:
        conn.close()


def create_deck_archetypes_table():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS deck_archetypes (
                    id     BIGSERIAL    PRIMARY KEY,
                    name   VARCHAR(255) NOT NULL,
                    format VARCHAR(50)  NOT NULL,
                    colors VARCHAR(10)  NOT NULL,
                    active BOOLEAN      NOT NULL DEFAULT TRUE
                );
            """)
        print("Table 'deck_archetypes' created (or already exists).")
    finally:
        conn.close()


def create_match_results_table():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS match_results (
                    id               BIGSERIAL   PRIMARY KEY,
                    player           BIGINT               REFERENCES user_logins(id) ON DELETE SET NULL,
                    opponent         BIGINT               REFERENCES user_logins(id) ON DELETE SET NULL,
                    archetype_id     BIGINT      NOT NULL REFERENCES deck_archetypes(id) ON DELETE RESTRICT,
                    opp_archetype_id BIGINT     NOT NULL REFERENCES deck_archetypes(id) ON DELETE RESTRICT,
                    play             BOOLEAN     NOT NULL,
                    match_result     VARCHAR(10) NOT NULL,
                    g1_result        VARCHAR(10) NOT NULL,
                    g2_result        VARCHAR(10),
                    g3_result        VARCHAR(10),
                    deck_id          BIGINT      REFERENCES user_decks(id) ON DELETE SET NULL,
                    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                ALTER TABLE match_results
                    ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT NOW();
            """)
        print("Table 'match_results' created (or already exists).")
    finally:
        conn.close()


def create_user_decks_table():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS user_decks (
                    id              BIGSERIAL   PRIMARY KEY,
                    user_id         BIGINT      NOT NULL REFERENCES user_logins(id) ON DELETE CASCADE,
                    archetype_id    BIGINT      NOT NULL REFERENCES deck_archetypes(id) ON DELETE RESTRICT,
                    decklist        TEXT,
                    decklist_link   TEXT,
                    num_matches     INTEGER     NOT NULL DEFAULT 0,
                    last_played     TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                ALTER TABLE user_decks
                    ADD COLUMN IF NOT EXISTS last_played TIMESTAMPTZ NOT NULL DEFAULT NOW();

                CREATE OR REPLACE FUNCTION set_last_played()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.last_played = NOW();
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;

                DROP TRIGGER IF EXISTS trg_user_decks_last_played ON user_decks;
                CREATE TRIGGER trg_user_decks_last_played
                    BEFORE UPDATE ON user_decks
                    FOR EACH ROW EXECUTE FUNCTION set_last_played();
            """)
        print("Table 'user_decks' created (or already exists).")
    finally:
        conn.close()


def create_profile_fields_table():
    conn = get_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS profile_fields (
                    id          BIGSERIAL    PRIMARY KEY,
                    user_id     BIGINT       NOT NULL REFERENCES user_logins(id) ON DELETE CASCADE,
                    field_name  VARCHAR(255) NOT NULL,
                    field_value VARCHAR(255) NOT NULL
                );
            """)
        print("Table 'profile_fields' created (or already exists).")
    finally:
        conn.close()


if __name__ == "__main__":
    create_user_logins_table()
    create_deck_archetypes_table()
    create_match_results_table()
    create_user_decks_table()
    create_profile_fields_table()
