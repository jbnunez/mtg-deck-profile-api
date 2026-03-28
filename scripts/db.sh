#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
ENV_FILE="$ROOT_DIR/.env"

# Load .env
if [[ -f "$ENV_FILE" ]]; then
  export $(grep -v '^#' "$ENV_FILE" | xargs)
fi

DB_NAME="${DB_NAME:-mtg_deck_profile}"
DB_USER="${DB_USER:-mtg_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

MANAGE="$ROOT_DIR/.venv/bin/python $ROOT_DIR/manage.py"

usage() {
  echo "Usage: $0 <command>"
  echo ""
  echo "Commands:"
  echo "  create    Create the database and user"
  echo "  drop      Drop the database"
  echo "  reset     Drop, recreate, and migrate"
  echo "  migrate   Run pending migrations"
  echo "  seed      Load fixture data"
  echo "  backup    Dump database to a timestamped SQL file"
  echo "  restore   Restore database from a SQL file: $0 restore <file>"
  echo "  shell     Open a psql shell"
}

create() {
  echo "Creating database '$DB_NAME' and user '$DB_USER'..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U postgres <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$DB_USER') THEN
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
  WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec
SQL
  echo "Done."
}

drop() {
  echo "Dropping database '$DB_NAME'..."
  psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;"
  echo "Done."
}

migrate() {
  echo "Running migrations..."
  $MANAGE migrate
}

seed() {
  FIXTURE="$ROOT_DIR/apps/decks/fixtures/sample_data.json"
  if [[ ! -f "$FIXTURE" ]]; then
    echo "No fixture found at $FIXTURE"
    exit 1
  fi
  echo "Loading fixture data..."
  $MANAGE loaddata "$FIXTURE"
}

backup() {
  BACKUP_DIR="$ROOT_DIR/backups"
  mkdir -p "$BACKUP_DIR"
  TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
  OUTPUT="$BACKUP_DIR/${DB_NAME}_${TIMESTAMP}.sql"
  echo "Backing up '$DB_NAME' to $OUTPUT..."
  PGPASSWORD="$DB_PASSWORD" pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" > "$OUTPUT"
  echo "Backup saved to $OUTPUT"
}

restore() {
  FILE="${1:-}"
  if [[ -z "$FILE" ]]; then
    echo "Error: provide a SQL file to restore. Usage: $0 restore <file>"
    exit 1
  fi
  if [[ ! -f "$FILE" ]]; then
    echo "Error: file not found: $FILE"
    exit 1
  fi
  echo "Restoring '$DB_NAME' from $FILE..."
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME" < "$FILE"
  echo "Done."
}

shell() {
  PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" "$DB_NAME"
}

case "${1:-}" in
  create)  create ;;
  drop)    drop ;;
  reset)   drop && create && migrate ;;
  migrate) migrate ;;
  seed)    seed ;;
  backup)  backup ;;
  restore) restore "${2:-}" ;;
  shell)   shell ;;
  *)       usage; exit 1 ;;
esac
