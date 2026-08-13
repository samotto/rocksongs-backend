# RockSongs Application Guide and Reusable Template

This file applies to both repositories beneath this directory. It documents the current RockSongs application and the rules for adapting it into a new application.

The parent directory is an organizational folder, not a Git repository. `frontend/` and `backend/` are independent Git repositories with separate histories, remotes, commits, and deployments.

## Start Here

Current directory layout:

```text
rocksongs/
├── AGENTS.md                    # Shared architecture and template instructions
├── frontend/                    # Git repo: samotto/rocksongs-frontend
└── backend/                     # Git repo: samotto/rocksongs-backend
```

Current production services:

| Component | Location |
|---|---|
| Frontend | `https://rocksongs.overturegroup.com` |
| Backend API | `https://api-rocksongs.overturegroup.com` |
| API health | `https://api-rocksongs.overturegroup.com/health` |
| Frontend GitHub | `https://github.com/samotto/rocksongs-frontend` |
| Backend GitHub | `https://github.com/samotto/rocksongs-backend` |
| Backend hosting | Railway project `rocksongs` |
| Database | Railway PostgreSQL |
| Transactional email | Resend |
| DNS | GoDaddy, under `overturegroup.com` |

## Template Boundary: Reusable vs. Application-Specific

Treat the system as two layers:

1. **Reusable application foundation**: users, roles, login/logout, signup, email verification, password changes, user administration, configuration, health checking, cookie authentication, CORS, database migrations, and deployment patterns.
2. **Application-specific feature**: the Rock Songs catalog, including the `songs` table, song endpoints, seed songs, search/results page, song modal, and song labels.

The marker below is used throughout this document:

```text
APPLICATION-SPECIFIC: Replace or redesign this part for a new application.
```

When building a new app, preserve the reusable foundation first. Then replace every section and file identified as **APPLICATION-SPECIFIC**. Do not mechanically rename `Song` if the new domain needs different columns or behavior; model the new domain deliberately.

## Architecture

```text
Browser (static HTML/CSS/JS)
    │ fetch(..., credentials: "include")
    ▼
FastAPI service on Railway
    ├── JWT in an HttpOnly cookie
    ├── SQLAlchemy + Alembic
    ├── PostgreSQL
    └── Resend verification email
```

The frontend is a static single-page application written without a framework or build system. The backend is a Python FastAPI service. Authentication state is carried in an HttpOnly `access_token` cookie, not browser local storage.

## Repository Responsibilities

### `frontend/`

- `index.html`: all page markup, tables, forms, overlays, and modals.
- `css/styles.css`: all desktop and responsive styles.
- `js/config.js`: public runtime configuration and automatic local/remote selection.
- `js/api.js`: the only frontend module that should communicate with the backend; also contains optional mock data.
- `js/app.js`: application state, rendering, event handlers, access-aware UI, search, sorting, pagination, and modal behavior.
- `CNAME`: GitHub Pages custom hostname.

### `backend/`

- `app/main.py`: FastAPI application, CORS, health check, and router registration.
- `app/config.py`: environment-backed settings.
- `app/database.py`: SQLAlchemy engine, session factory, and dependency.
- `app/models.py`: SQLAlchemy database models.
- `app/schemas.py`: Pydantic request and response contracts.
- `app/auth.py`: password hashing, JWT creation/validation, and current-user dependency.
- `app/email_service.py`: Resend verification email and frontend verification URL.
- `app/routers/auth_routes.py`: signup, verification, login, logout, and current user.
- `app/routers/user_routes.py`: user administration and profile/password changes.
- `app/routers/song_routes.py`: **APPLICATION-SPECIFIC** song API.
- `app/seed.py`: reusable admin seed plus **APPLICATION-SPECIFIC** song seed.
- `data/seed_songs.json`: **APPLICATION-SPECIFIC** initial catalog data.
- `alembic/versions/`: ordered database migrations.
- `Procfile`: Railway startup command.

## Reusable User and Authentication Foundation

### Roles

The only valid user roles are:

| Role | Meaning |
|---|---|
| `Admin` | Full user administration and application-specific write access |
| `Basic` | Verified normal user with read access |
| `Pending` | Registered but email not yet verified; cannot log in or use protected endpoints |

Role names are case-sensitive and constrained by both Pydantic types and the PostgreSQL check constraint. `Pending` is verification state. `last_logon_time` is audit data and must not be used to decide whether an account is verified.

Authorization must always be enforced by the backend. Hiding an icon or button in the frontend is helpful UX, but is never the security boundary.

### Signup and email verification flow

1. The browser posts email and password to `POST /auth/register`.
2. The backend performs case-insensitive duplicate checks for both email and name.
3. The password is hashed with bcrypt; plaintext passwords are never stored.
4. The backend creates a user with role `Pending` and `last_logon_time = NULL`.
5. The backend creates a signed JWT with purpose `verify_email`, user id, email, and expiration.
6. Resend sends a button linking to `FRONTEND_URL/?verify_token=...`.
7. The frontend reads the token from the URL and posts it to `POST /auth/verify-email`.
8. The backend verifies the signature, purpose, expiry, user id, email, and current `Pending` role.
9. The backend changes the role to `Basic`, records `last_logon_time`, sets the authentication cookie, and returns the user.
10. The frontend removes the verification token from the visible URL and opens the authenticated application automatically.

Verification tokens are stateless and are not stored in PostgreSQL. Changing `JWT_SECRET_KEY` invalidates outstanding verification links and login cookies.

### Authentication cookie

- Cookie name: `access_token`
- Token format: JWT with `sub=<user id>`, `purpose=access`, and expiration.
- Cookie flags: `HttpOnly`, configurable `Secure` and `SameSite`, path `/`.
- Frontend requests must use `credentials: "include"`.
- The backend CORS middleware must use exact allowed origins and `allow_credentials=True`.
- Production should use `COOKIE_SECURE=true` and HTTPS.
- The production frontend and API intentionally share the registrable domain `overturegroup.com`; this avoids cross-site cookie problems, especially in iPhone Safari.

### Password rules

- API validation currently requires 8–72 characters for signup, admin-created users, and resets.
- The bootstrap password is configured separately and currently defaults to `abc` for the initial admin.
- User-entered passwords are confirmed in the frontend before submission.
- Password fields have show/hide controls.
- Only the user or an Admin can reset that user's password.

### Bootstrap Admin

`python -m app.seed` always ensures the configured seed account exists and has role `Admin`.

Current defaults:

```env
SEED_ADMIN_EMAIL=sam@overturegroup.com
SEED_ADMIN_PASSWORD=abc
SEED_ADMIN_FORCE_PASSWORD_RESET=false
```

If the email already exists as `Basic` or `Pending`, seeding promotes it to `Admin` and establishes the seed password. Once it is already an Admin, normal password changes survive deployments unless `SEED_ADMIN_FORCE_PASSWORD_RESET=true`.

For a new application, change the seed email and password through environment variables. Never commit real production secrets. The `abc` value is bootstrap convenience, not an appropriate long-term production password.

## Database Schema

### `users` — reusable foundation

| Column | Type | Null? | Notes |
|---|---|---:|---|
| `id` | integer | No | Primary key; indexed |
| `name` | text | No | Case-insensitively unique via migration index |
| `email` | string/text | No | Unique and indexed; normalized to lowercase by API |
| `role` | text | No | `Admin`, `Basic`, or `Pending`; default `Basic` |
| `password_hash` | text | Yes | bcrypt hash; nullable for a future external-login account |
| `google_id` | text | Yes | Reserved for future Google OAuth; OAuth is not implemented |
| `create_time` | timestamp with timezone | No | UTC account creation time |
| `last_logon_time` | timestamp with timezone | Yes | UTC audit timestamp; not verification state |

### `songs` — APPLICATION-SPECIFIC

> **APPLICATION-SPECIFIC:** This entire table represents the Rock Songs catalog. Replace it with the new application's domain table or tables. Keep the audit-column pattern if it is useful.

| Column | Type | Null? | Notes |
|---|---|---:|---|
| `id` | integer | No | Primary key; indexed |
| `artist` | text | No | Search/sort field; indexed |
| `album` | text | Yes | Optional display field |
| `song` | text | No | Search/sort field; indexed |
| `overplayed` | boolean | No | Default `false` |
| `create_time` | timestamp with timezone | No | UTC creation timestamp |
| `update_time` | timestamp with timezone | No | UTC last update timestamp |
| `create_id` | integer | No | Foreign key to `users.id` |
| `update_id` | integer | No | Foreign key to `users.id` |

If a user is deleted, song audit references owned by that user are reassigned to the Admin performing the deletion before the user row is removed. Recreate or generalize this behavior for any new domain tables with user audit foreign keys.

### Migration rules

- Never change a migration that has already run in a shared or production database.
- Add a new Alembic revision for every schema change.
- Update SQLAlchemy models and Pydantic schemas with the migration.
- Test both a clean database upgrade and an upgrade from the current revision.
- Current migration chain is `0001_create_users_and_songs` → `0002_add_user_name` → `0003_user_roles`.
- For a genuinely new product with a new database, it is acceptable to replace the history with a clean initial migration before the first deployment. Do not do that to the existing RockSongs database.

## API Contract

All endpoints return JSON. Protected endpoints authenticate through the cookie.

### Reusable health and authentication endpoints

| Method | Path | Access | Behavior |
|---|---|---|---|
| `GET` | `/health` | Public | Selects one `users.id` to verify the API, database connection, and reusable user table; returns `{"status":"ok"}` |
| `POST` | `/auth/login` | Public | Validates email/password, rejects `Pending`, records login time, sets cookie |
| `POST` | `/auth/register` | Public | Creates `Pending` user and sends verification email |
| `POST` | `/auth/verify-email` | Public with token | Changes `Pending` to `Basic`, logs user in |
| `POST` | `/auth/resend-verification` | Public | Resends only for a pending account; response avoids account enumeration |
| `POST` | `/auth/logout` | Public | Clears cookie |
| `GET` | `/auth/me` | Authenticated | Returns id, name, email, and role |

### Reusable user endpoints

| Method | Path | Access | Behavior |
|---|---|---|---|
| `GET` | `/users` | Admin | Lists users ordered by email |
| `POST` | `/users` | Admin | Creates an `Admin` or `Basic` user with a password |
| `PUT` | `/users/me` | Authenticated | Changes current user's name/email |
| `PUT` | `/users/{user_id}` | Admin | Changes name, email, and role |
| `DELETE` | `/users/{user_id}` | Admin | Deletes another user; self-delete is blocked |
| `POST` | `/users/{user_id}/reset-password` | Same user or Admin | Replaces password hash |

Name and email updates must continue to reject case-insensitive duplicates belonging to any other user with HTTP 409.

### Song endpoints — APPLICATION-SPECIFIC

> **APPLICATION-SPECIFIC:** Replace `song_routes.py`, the Song schemas, and these endpoints with the new product's resource API. Keep the authorization pattern unless the new product explicitly needs different permissions.

| Method | Path | Access | Behavior |
|---|---|---|---|
| `GET` | `/songs` | Authenticated Admin or Basic | Lists all songs ordered by artist then song |
| `POST` | `/songs` | Admin | Creates a song and records audit user/time |
| `PUT` | `/songs/{song_id}` | Admin | Replaces editable song fields and update audit data |
| `DELETE` | `/songs/{song_id}` | Admin | Deletes a song |

Legacy singular aliases `/song` and `/song/{song_id}` exist for write operations but are hidden from generated API docs. New applications should use one consistent plural resource path and omit aliases unless backward compatibility is required.

## Frontend Behavior

### Reusable pages and modals

- A blocking login/signup overlay is shown when no user is authenticated.
- Signup confirms both email and password and offers resend verification.
- Successful verification logs the user in automatically.
- Header controls are User Administration, User Settings, and Login/Logout.
- User Administration is visible only to an `Admin`.
- User Administration columns are Name, Email, Role, and Last login.
- Clicking a user opens a modal titled with the primary key, such as `[1] User Information`.
- The modal edits name/email/role, resets password, and deletes another user.
- User Settings edits the signed-in user's name/email and optionally resets password.
- Search/filter state is reset at login and logout so it does not leak between users.

### Catalog page and song modal — APPLICATION-SPECIFIC

> **APPLICATION-SPECIFIC:** The catalog page is the principal Rock Songs feature. Replace the following markup and logic for a new product rather than leaving song terminology in a supposedly generic application.

RockSongs catalog behavior:

- Search matches artist, song, or album.
- Results sort by Artist, Song, or Album.
- Pagination uses 25 results per page.
- Columns are Artist, Song, Album, and Overplayed.
- All authenticated users can browse/search.
- Only Admins can add, view song details, edit, or delete.
- Basic users cannot click a result to open the song modal.
- The Admin edit title contains the primary key and artist, for example `[12] Edit Led Zeppelin Song`.
- Create/update/delete reloads the collection from the backend instead of manually patching local state.

Files and code to replace for a new catalog/domain:

| Location | APPLICATION-SPECIFIC responsibility |
|---|---|
| `frontend/index.html` `#catalogView` | Search controls, result headings, table columns, empty state, pagination labels |
| `frontend/index.html` `#modalOverlay` | Create/view/edit form fields and song-specific wording |
| `frontend/js/api.js` | `MOCK_SONGS`, `getSongs`, `createSong`, `updateSong`, `deleteSong`, and field mapping |
| `frontend/js/app.js` | `state.songs`, filtering, sorting, rendering, pagination, song modal, CRUD handlers |
| `frontend/css/styles.css` | `.song-table`, song modal, overplayed badge/column, and domain-specific responsive rules |
| `backend/app/models.py` | `Song` model |
| `backend/app/schemas.py` | `SongBase`, `SongCreate`, `SongUpdate`, `SongResponse` |
| `backend/app/routers/song_routes.py` | Domain CRUD endpoints and authorization |
| `backend/app/main.py` | Song router import/registration and application title |
| `backend/app/seed.py` | `load_seed_data`, `seed_songs`, and Song import |
| `backend/data/seed_songs.json` | Initial application-specific records |
| `backend/alembic/versions/` | New domain schema migration |

Also search both repositories case-insensitively for `rocksongs`, `rock songs`, `song`, `songs`, `artist`, `album`, `overplayed`, the guitar emoji, and the current domains before calling a new app complete.

### Role-driven UI rules

Mirror backend permissions in `frontend/js/app.js`:

- `Admin`: show user administration and application write/detail actions.
- `Basic`: show application read-only behavior.
- `Pending`: should never reach the protected app because the backend rejects it.

When introducing a new role or changing permissions, update all of these together:

1. Database constraint/migration.
2. Pydantic role types.
3. Backend authorization dependencies/checks.
4. Authentication responses.
5. Frontend role checks and controls.
6. Tests for allowed and forbidden requests.

### Responsive design requirements

- Preserve the `max-width: 600px` mobile breakpoint unless a redesigned UI uses a tested alternative.
- Keep tap targets large enough for a phone.
- Avoid fixed heights that create large gaps on iPhone Safari.
- Tables must remain usable at narrow widths; currently Album and user Last Login are hidden on small screens.
- Modals must fit within the viewport and scroll internally when needed.
- Verify login, catalog/results, user administration, settings, and all modals at phone width.
- Test on real iPhone Safari when cookies, scrolling, or viewport layout change.

## Configuration

### Frontend configuration

All public frontend deployment values belong at the top of `frontend/js/config.js` in `DEPLOYMENT_CONFIG`:

```js
const DEPLOYMENT_CONFIG = {
  ENVIRONMENT_OVERRIDE: null,
  LOCAL_API_BASE_URL: "http://localhost:8000",
  REMOTE_API_BASE_URL: "https://api-rocksongs.overturegroup.com",
  USE_MOCK_API: false,
  LOCAL_REQUEST_TIMEOUT_MS: 10000,
  REMOTE_REQUEST_TIMEOUT_MS: 15000,
};
```

With a null override, `localhost` and `127.0.0.1` select the local API; all other frontend hosts select the remote API. Temporary integration testing may use `"local"` or `"remote"`, but restore `null` before commit.

Never put passwords, API keys, JWT secrets, database URLs, or other secrets in frontend files. Everything published by GitHub Pages is public.

### Backend configuration

Backend settings are environment variables defined by `app/config.py` and illustrated in `.env.example`:

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | PostgreSQL connection URL |
| `JWT_SECRET_KEY` | Signs access and verification tokens; must be strong in production |
| `JWT_ALGORITHM` | Currently `HS256` |
| `JWT_EXPIRE_MINUTES` | Login cookie/token lifetime |
| `FRONTEND_ORIGINS` | Comma-separated exact CORS origins, without path |
| `COOKIE_SECURE` | `false` locally; `true` in HTTPS production |
| `COOKIE_SAMESITE` | Currently `lax` for same-site subdomains |
| `SEED_ADMIN_EMAIL` | Initial Admin email |
| `SEED_ADMIN_PASSWORD` | Initial/promotion password |
| `SEED_ADMIN_FORCE_PASSWORD_RESET` | Reapply seed password to existing Admin when true |
| `RESEND_API_KEY` | Secret Resend API key |
| `EMAIL_FROM` | Verified sender name/address |
| `FRONTEND_URL` | Base used in verification links |
| `EMAIL_VERIFICATION_MINUTES` | Verification token lifetime |

Settings are cached per process. Restart the backend after changing environment values.

### Production coupling that must be updated together

For every new app/domain, update these as one deployment change:

- `frontend/CNAME`
- `REMOTE_API_BASE_URL` in `frontend/js/config.js`
- Railway custom API domain
- Railway `FRONTEND_ORIGINS`
- Railway `FRONTEND_URL`
- Railway cookie settings
- Resend verified sending domain and `EMAIL_FROM`
- DNS records for frontend, API, Railway ownership verification, and email authentication
- Branding in verification email subject/body

Exact origins matter: scheme, hostname, and port must match. Do not include paths in CORS origins.

## Local Development

### PostgreSQL and backend

From `backend/`:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The local database named in `.env` must exist and PostgreSQL must be running. API documentation is at `http://127.0.0.1:8000/docs`; health is at `http://127.0.0.1:8000/health`.

### Frontend

From `frontend/`:

```bash
python3 -m http.server 5173
```

Open `http://localhost:5173`. Do not open `index.html` directly from disk; serve it over HTTP. With the default automatic config it calls `http://localhost:8000`.

### Mock frontend option

Set `USE_MOCK_API: true` in `frontend/js/config.js` to exercise frontend behavior without PostgreSQL or FastAPI. Mock mode is useful for layout work but cannot validate CORS, cookies, authorization enforcement, migrations, Resend, or the real API contract. Restore it to `false` before committing.

## Deployment

### Frontend: GitHub Pages

- Repository: `samotto/rocksongs-frontend`, branch `main`, site published from repository root.
- `frontend/CNAME` contains the custom frontend hostname.
- GoDaddy frontend CNAME points the subdomain to `samotto.github.io`.
- Pushing `main` publishes the static site through GitHub Pages.
- When browser caching matters, increment the query-string version on CSS/JS asset references in `index.html`.

### Backend: Railway

- Railway project: `rocksongs`.
- PostgreSQL and FastAPI service live in the same project.
- The service start command comes from `Procfile`:

```text
web: alembic upgrade head && python -m app.seed && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Every deployment therefore migrates first, performs idempotent bootstrap/domain seeding, and then starts the server. Keep seed operations idempotent.

Before deploying, verify the Railway project/service link and production variables. After deploying, wait for success and test `/health`, authentication, `/auth/me`, and the application-specific read endpoint.

### DNS and Safari cookie arrangement

Current public hostnames:

- Frontend: `rocksongs.overturegroup.com`
- API: `api-rocksongs.overturegroup.com`

The frontend DNS CNAME targets GitHub Pages. The API DNS CNAME targets the Railway-provided custom-domain target, and Railway also supplies a DNS verification record. Resend supplies its own sending-domain DNS records. Use the exact current values displayed by GitHub, Railway, and Resend rather than copying stale targets from documentation.

Keeping the frontend and API beneath the same registrable domain is an intentional authentication design decision. If the new app uses unrelated domains, reevaluate `SameSite`, third-party-cookie restrictions, CSRF protection, and Safari behavior rather than copying the present cookie settings blindly.

## Verification and Quality Checklist

Run checks proportionate to every change. At minimum:

### Backend

- Apply `alembic upgrade head` against a disposable/local PostgreSQL database.
- Confirm `GET /health` succeeds and fails when database access is unavailable.
- Verify signup creates `Pending` and unverified login returns 403.
- Verify email token promotes exactly once and logs in automatically.
- Verify Admin can manage users; Basic receives 403.
- Verify duplicate name/email updates return 409 and do not partially update.
- Verify the current user cannot delete their own account.
- **APPLICATION-SPECIFIC:** verify Basic can read songs but cannot create/update/delete; Admin can perform all song operations.
- Compile/import the Python application and inspect `/docs` after contract changes.

### Frontend

- Test login, logout, signup, resend, verification-link auto-login, and settings.
- Test Admin and Basic accounts separately.
- Confirm authentication failures show the login overlay rather than an empty catalog.
- Confirm backend/network errors are shown as errors, not as “no results.”
- Confirm user search/filter state resets between accounts.
- **APPLICATION-SPECIFIC:** test catalog filtering, each sort column, pagination, CRUD refresh, empty results, and permission-aware row clicks.
- Test desktop Chrome and phone-width layout; test real iPhone Safari for production auth/layout changes.

### Git hygiene

- Run Git status independently inside `frontend/` and `backend/`.
- Do not stage or commit `.env`, database dumps, credentials, or unrelated user changes.
- Commit and push each repository separately to its own `main` branch when explicitly requested.
- The parent `rocksongs/AGENTS.md` is outside both existing repositories and is not pushed by either child repo.

## Building a New Application from This Template

Use this order so authentication remains functional while the domain changes:

1. Copy the parent folder, preserving independent `frontend/` and `backend/` repos only if separate deployment histories are desired.
2. Rename GitHub repositories and replace their remotes.
3. Choose frontend and API hostnames under the same registrable domain when possible.
4. Replace product names, titles, icons, email text, README content, FastAPI title, domains, and CNAME.
5. Configure new Railway services, PostgreSQL, secrets, cookie/CORS values, and Resend sender.
6. Keep the `User` model and auth/user routes unless requirements differ.
7. **APPLICATION-SPECIFIC:** design the new domain schema; do not merely rename song fields.
8. **APPLICATION-SPECIFIC:** add a migration for the new domain tables and decide what to do with existing `songs` data.
9. **APPLICATION-SPECIFIC:** replace Song Pydantic schemas and routes; register the new router in `main.py`.
10. **APPLICATION-SPECIFIC:** replace song seed loading with optional, idempotent new-domain seed data.
11. **APPLICATION-SPECIFIC:** replace the catalog view, result columns, filtering/sorting, pagination labels, modal form, mock records, and API methods.
12. Map new permissions explicitly. Keep server-side enforcement and mirror it in the UI.
13. Update `/health` only if the reusable `users` table is removed; otherwise keep its simple `users.id` database check.
14. Run the complete verification checklist locally with real PostgreSQL.
15. Deploy the backend, validate health/auth/API, then deploy the frontend and validate production cookies on desktop and iPhone Safari.

## Completion Definition for a New App

A new app is not complete until:

- No unintended RockSongs branding, fields, seed data, domains, or route names remain.
- All **APPLICATION-SPECIFIC** locations listed above have been reviewed.
- Authentication, email verification, roles, user administration, settings, and password reset still work.
- The backend—not just the frontend—enforces every permission.
- Production secrets live only in the hosting environment.
- Database migrations work on both clean and upgrade paths.
- CORS, cookie settings, frontend API URL, verification URL, DNS, and HTTPS agree.
- The application works on desktop Chrome and iPhone Safari.
- Both child repositories are clean, committed, and deployed from the intended branches.

## Reusable Lookup Lists

Static dropdown choices are part of the reusable foundation, not the Rock Songs-specific catalog.

- lookup_lists stores id, unique list_name, optional description, Alphabetical or Sequence sort_mode, optional default_item_value, active, and audit columns. The default uses a composite foreign key to an item belonging to the same list.
- lookup_list_items has the composite primary key (list_id, list_item_value), plus list_item_text, optional non-negative sequence, active, and audit columns. It has no separate item id.
- Migration 0004_lookup_lists creates both tables. Migration 0005_lookup_defaults adds default_item_value and permits sequence zero.
- The idempotent seed creates the Alphabetical Role list with Admin, Basic, and Pending, sets Basic as its default, and sets every Role sequence to 0. Stored values and visible text use the full capitalized names.
- Primary-key item values are immutable. Edit changes text, sequence, or active status.
- DELETE operations soft-deactivate lists and values so historical references remain valid. PUT can reactivate them. A default value cannot be deactivated until the list default is changed or cleared.
- GET /lookup-lists/{list_name} is authenticated and returns the list default plus only active values in backend-defined order.
- Admin CRUD is under /admin/lookup-lists, including nested /{list_id}/items endpoints.
- The Admin-only header icon opens an Administration hub with Users and Lists.
- Lists and list values have separate administration pages. Lists are defined by application code: the frontend intentionally does not expose New List or Deactivate List controls, although the backend endpoints remain available. The List edit modal provides an active-value dropdown for selecting or clearing the default. List values retain create/edit/deactivate controls.
- populateLookupSelect in frontend/js/app.js is the generic dropdown loader. It uses backend ordering, caches values, applies the list default when there is no explicit selection, and retains an existing inactive selection.
- Local frontend testing against Railway uses python3 dev_server.py --port 5173 and http://localhost:5173/?api=proxy. This frontend-only proxy preserves secure production cookie settings; FastAPI and PostgreSQL remain on Railway.
