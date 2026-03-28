# mtg-deck-profile-api
API for site for managing mtg decks and performance tracking

## Local Development Setup

### Prerequisites
- Python 3.9+
- [Homebrew](https://brew.sh)

### 1. Install and start PostgreSQL

```bash
brew install postgresql@16
brew services start postgresql@16
```

### 2. Create the database and user

```bash
psql postgres
```

```sql
CREATE USER mtg_user WITH PASSWORD 'yourpassword';
CREATE DATABASE mtg_deck_profile OWNER mtg_user;
\q
```

### 3. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` with your values:

```
SECRET_KEY=any-random-string-here
DEBUG=True
DB_NAME=mtg_deck_profile
DB_USER=mtg_user
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432
```

### 4. Install dependencies and run migrations

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### 5. Start the server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000/api/v1/`.

## API Endpoints

| Method | URL | Description |
|--------|-----|-------------|
| GET/POST | `/api/v1/decks/` | List / create decks |
| GET/PUT/DELETE | `/api/v1/decks/{id}/` | Retrieve / update / delete a deck |
| GET | `/api/v1/decks/{id}/stats/` | Win/loss/draw stats |
| GET/POST | `/api/v1/decks/{id}/cards/` | List / add cards |
| GET/POST | `/api/v1/decks/{id}/matches/` | List / record match results |
