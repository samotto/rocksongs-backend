# rocksongs-backend
A Python CRUD service to a Postgres DB storing rock songs

## Overview

REST API built with **FastAPI** and **SQLAlchemy** that performs full CRUD operations on a PostgreSQL database of rock songs.

## Tech Stack

- **FastAPI** — web framework
- **SQLAlchemy 2** — ORM
- **Alembic** — database migrations
- **psycopg2** — PostgreSQL driver
- **Pydantic v2** — data validation

## Song Fields

| Field | Type | Required |
|---|---|---|
| `id` | integer | auto |
| `title` | string | ✅ |
| `artist` | string | ✅ |
| `album` | string | optional |
| `year` | integer (1900–2100) | optional |
| `genre` | string | optional |
| `duration_seconds` | integer | optional |
| `created_at` | timestamp | auto |
| `updated_at` | timestamp | auto |

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/songs/` | List all songs (supports `?artist=`, `?genre=`, `?skip=`, `?limit=`) |
| `POST` | `/songs/` | Create a new song |
| `GET` | `/songs/{id}` | Get a song by ID |
| `PUT` | `/songs/{id}` | Update a song |
| `DELETE` | `/songs/{id}` | Delete a song |
| `GET` | `/health` | Health check |

## Running Locally

### With Docker Compose

```bash
docker compose up
```

The API will be available at http://localhost:8000. Interactive docs at http://localhost:8000/docs.

### Without Docker

1. Copy and configure environment:
   ```bash
   cp .env.example .env
   # edit .env with your Postgres credentials
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## Running Tests

```bash
pip install -r requirements.txt
pytest
```

Tests use an in-memory SQLite database — no Postgres instance required.
