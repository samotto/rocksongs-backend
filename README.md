# RockSongs Backend

RockSongs Backend is a beginner-friendly FastAPI service for managing a shared rock song list.

It provides:
- JWT cookie authentication (`/auth/login`, `/auth/logout`, `/auth/me`)
- Authenticated read access to all songs (`GET /songs`)
- Admin-only create/update/delete for songs
- PostgreSQL + SQLAlchemy models
- Alembic migrations
- Seed utilities
- Railway deployment support

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Pydantic
- JWT (cookie-based auth)
- passlib/bcrypt password hashing

## Project Structure

```text
rocksongs-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── auth.py
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth_routes.py
│   │   └── song_routes.py
│   └── seed.py
├── alembic/
│   └── versions/
├── scripts/
│   ├── backup_db.sh
│   ├── restore_db.sh
│   └── seed_db.sh
├── data/
│   └── seed_songs.json
├── alembic.ini
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md
```

## Environment Variables

Copy `.env.example` to `.env` and fill values:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/rocksongs
JWT_SECRET_KEY=change-me-now
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=120
FRONTEND_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
SEED_ADMIN_EMAIL=sam@overturegroup.com
SEED_ADMIN_PASSWORD=abc
RESEND_API_KEY=
EMAIL_FROM=Rock Songs <onboarding@resend.dev>
FRONTEND_URL=http://localhost:5173
EMAIL_VERIFICATION_MINUTES=60
```

Production (Railway) example values:

```env
FRONTEND_ORIGINS=https://rocksongs.example.com,http://localhost:5173,http://127.0.0.1:5173
FRONTEND_URL=https://rocksongs.example.com
COOKIE_SECURE=true
COOKIE_SAMESITE=lax
```

For Safari-compatible cookie authentication, host the frontend and API beneath
the same registrable domain, for example `rocksongs.example.com` and
`api-rocksongs.example.com`. When reusing this backend, the production hostname,
CORS allowlist, verification-link URL, and cookie behavior are configured only
through these environment variables; application code does not need to change.

## API Endpoints

### Health

- `GET /health`

Returns:

```json
{"status": "ok"}
```

The health check selects one `id` from the `users` table before returning. If
PostgreSQL or the table is unavailable, the endpoint returns a server error.

### Authentication

- `POST /auth/login`
- `POST /auth/register`
- `POST /auth/verify-email`
- `POST /auth/resend-verification`
- `POST /auth/logout`
- `GET /auth/me`

Notes:
- Login sets an HttpOnly JWT cookie named `access_token`.
- Registration creates the user with role `Pending` and sends a signed, expiring email-verification link through Resend.
- Email verification changes the role from `Pending` to `Basic`, records the login time, and automatically logs the user in.
- Users with the `Pending` role cannot log in until their email address is verified.
- Supported roles are `Admin`, `Basic`, and `Pending`.
- Logout clears that cookie.
- `GET /auth/me` returns 401 when not authenticated.

### Songs

- `GET /songs` (authenticated)
- `POST /songs` (Admin)
- `PUT /songs/{song_id}` (Admin)
- `DELETE /songs/{song_id}` (Admin)

Important:
- There is currently no `GET /songs/{id}` endpoint.
- Songs are returned ordered by artist, then song.

## Local Development

### macOS / Linux

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

### Windows PowerShell

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

Open API docs at:
- `http://127.0.0.1:8000/docs`

## Database Migrations

Run migrations:

```bash
alembic upgrade head
```

## Seed Data

Run seed script:

```bash
python -m app.seed
```

Or:

```bash
./scripts/seed_db.sh
```

Seed behavior:
- Creates the default Admin if missing; if that email has another role, promotes it and establishes the seed password (`SEED_ADMIN_EMAIL`, `SEED_ADMIN_PASSWORD`)
- Loads songs from `data/seed_songs.json`
- Skips duplicate songs by `artist + song`

## Manual User Management

Generate a password hash:

```bash
python -c "from app.auth import hash_password; print(hash_password('your-password'))"
```

Insert user with SQL (example):

```sql
INSERT INTO users (name, email, role, password_hash, create_time)
VALUES ('Example User', 'user@example.com', 'Basic', 'PASTE_HASH_HERE', now());
```

## CORS and Frontend Integration

CORS allows the comma-separated origins defined by `FRONTEND_ORIGINS` and supports credentials.

Frontend requests must include credentials so browser sends auth cookie.

Example in frontend fetch:

```js
fetch('https://your-backend-url/songs', {
  method: 'GET',
  credentials: 'include'
})
```

For `rocksongs-frontend` on GitHub Pages:
- Set `FRONTEND_ORIGINS` to the exact GitHub Pages URL (plus any additional allowed origins)
- Keep `allow_credentials=true` (already configured)

## Backup and Restore

### Backup

```bash
./scripts/backup_db.sh
```

Creates:

- `backups/rocksongs-backup-YYYYMMDD-HHMMSS.sql`

### Restore

```bash
./scripts/restore_db.sh backups/rocksongs-backup-file.sql
```

Notes:
- Both scripts require `DATABASE_URL`.
- `backups/` is ignored by git.

## Railway Deployment

### 1) Push code to GitHub

```bash
git add .
git commit -m "Initial FastAPI backend with Postgres models and auth"
git push origin main
```

### 2) Create Railway service from GitHub repo

- In Railway, create a new project (or open existing project).
- Add service from GitHub.
- Select repository `rocksongs-backend`.

### 3) Add PostgreSQL service

- In the same Railway project, add PostgreSQL database service.
- Copy the generated `DATABASE_URL` to backend service environment variables.

### 4) Set backend environment variables in Railway

Set at least:

- `DATABASE_URL`
- `JWT_SECRET_KEY`
- `JWT_ALGORITHM=HS256`
- `JWT_EXPIRE_MINUTES=120`
- `FRONTEND_ORIGINS=https://samotto.github.io`
- `COOKIE_SECURE=true`
- `COOKIE_SAMESITE=none`
- `SEED_ADMIN_EMAIL`
- `SEED_ADMIN_PASSWORD`
- `RESEND_API_KEY`
- `EMAIL_FROM=Rock Songs <noreply@mail.overturegroup.com>`
- `FRONTEND_URL=http://localhost:5173` (use the public frontend URL in production)
- `EMAIL_VERIFICATION_MINUTES=60`

### 5) Railway run command

`Procfile` is included:

```text
web: alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

The start command applies pending migrations and idempotent seed data automatically on every deployment.

### 6) Seed after first deploy

From Railway service shell (or one-off command):

```bash
python -m app.seed
```

## Notes for Future Google Login

The `users` table already includes `google_id`.

Current auth is email/password only. You can add Google OAuth later without changing song endpoints.
