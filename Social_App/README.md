# Simple Social — FastAPI Social App

A lightweight social media backend built with **FastAPI**, backed by **PostgreSQL on Supabase**, with media uploads handled by **ImageKit** and a **Streamlit** frontend for quick interaction.

---

## Table of Contents

1. [What the App Does](#what-the-app-does)
2. [Overall Architecture](#overall-architecture)
3. [Layer Summary](#layer-summary)
4. [Local Setup](#local-setup)
5. [Environment Variables (.env)](#environment-variables-env)
6. [Supabase Database Connection & PgBouncer Fix](#supabase-database-connection--pgbouncer-fix)
7. [Running the App](#running-the-app)

---

## What the App Does

Simple Social is a minimal social-media API and UI that lets users:

- **Register and log in** using email/password (JWT-based via fastapi-users)
- **Create posts** — upload images or videos that are stored on ImageKit CDN
- **Browse a feed** of all posts with author info
- **Delete** their own posts
- **View and update** their profile (bio, full name, location, website, profile picture URL)

The Streamlit frontend provides a ready-to-use browser UI for all of the above without a separate SPA build step.

---

## Overall Architecture

```
Browser / Streamlit UI
        │  HTTP (REST + JWT Bearer)
        ▼
┌─────────────────────────────────┐
│         FastAPI Backend         │
│  ┌──────────┐  ┌─────────────┐  │
│  │  Routes  │→ │  Services   │  │
│  │ (api/v1) │  │(business    │  │
│  └──────────┘  │  logic)     │  │
│                └──────┬──────┘  │
│                       │         │
│  ┌────────────────────▼──────┐  │
│  │  SQLAlchemy (async ORM)   │  │
│  └────────────────────┬──────┘  │
└───────────────────────┼─────────┘
                        │ asyncpg (TCP)
                        ▼
            Supabase PostgreSQL
          (via PgBouncer pooler)

                + ImageKit CDN
          (file uploads via SDK)
```

---

## Layer Summary

### `app/models/` — ORM Models

SQLAlchemy `DeclarativeBase` models that map directly to database tables.

| Model  | Table  | Key Columns                                                                                                                                     |
| ------ | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `User` | `user` | `id` (UUID), `email`, `username`, `full_name`, `bio`, `profile_image_url`, `cover_image_url`, `website`, `location`, `is_active`, `is_verified` |
| `Post` | `post` | `id` (UUID), `user_id` (FK → user.id), `caption`, `url`, `file_type`, `file_name`, `created_at`                                                 |

### `app/schemas/` — Pydantic Schemas

Request/response validation and serialisation.

| Schema              | Purpose                                                   |
| ------------------- | --------------------------------------------------------- |
| `UserRead`          | Returned after login / GET `/users/me`                    |
| `UserCreate`        | Registration payload — `username` is required             |
| `UserUpdate`        | Partial user updates used internally by fastapi-users     |
| `UserProfileRead`   | Full profile response including `post_count`              |
| `UserProfileUpdate` | PATCH `/users/profile` request body (all fields optional) |

### `app/services/` — Business Logic

Pure async functions, no FastAPI dependencies. Imported by routes.

| File                       | Functions                                              |
| -------------------------- | ------------------------------------------------------ |
| `services/user.py`         | `get_profile_payload()`, `update_profile_payload()`    |
| `services/post.py`         | `upload_post()`, `get_feed()`, `delete_post()`         |
| `services/images.py`       | ImageKit client singleton                              |
| `services/user_manager.py` | fastapi-users `UserManager` (password hashing, events) |

### `app/api/v1/` — Route Handlers

Thin HTTP layer — validates auth, calls services, raises `HTTPException` on failure.

| File             | Prefix   | Endpoints                                                              |
| ---------------- | -------- | ---------------------------------------------------------------------- |
| `auth_routes.py` | `/api`   | `POST /auth/register`, `POST /auth/jwt/login`, `POST /auth/jwt/logout` |
| `user.py`        | `/users` | `GET /me`, `GET /profile`, `PATCH /profile`                            |
| `post.py`        | `/posts` | `POST /upload`, `GET /feed`, `DELETE /post/{id}`                       |

### `app/core/` — Infrastructure

| File              | Responsibility                                                     |
| ----------------- | ------------------------------------------------------------------ |
| `db.py`           | Async SQLAlchemy engine, session factory, `get_user_db` dependency |
| `auth_backend.py` | JWT strategy, bearer transport, `current_active_user` dependency   |

### `frontend/frontend.py` — Streamlit UI

Single-file browser app. Pages: **Login / Sign-up → Feed → Upload → Profile**.
Communicates with the backend exclusively via HTTP using the `requests` library and the JWT token stored in `st.session_state`.

---

## Local Setup

### Prerequisites

| Tool                | Minimum version     |
| ------------------- | ------------------- |
| Python              | 3.11+               |
| pip                 | latest              |
| A Supabase project  | (free tier is fine) |
| An ImageKit account | (free tier is fine) |

### 1 — Clone and create a virtual environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS / Linux
python3 -m venv env
source env/bin/activate
```

### 2 — Install dependencies

```bash
pip install -r requirement.txt
```

### 3 — Create the `.env` file

Create a file called `.env` in the `Social_App/` root (next to `app/`):

```env
DATABASE_URL=postgresql+asyncpg://<user>:<password>@<host>:<port>/<dbname>?ssl=require&prepared_statement_cache_size=0
SECRET=<your-jwt-secret-at-least-32-chars>
IMAGEKIT_PRIVATE_KEY=<your-imagekit-private-key>
```

See the next section for where to get each value.

---

## Environment Variables (.env)

### `DATABASE_URL`

Full async-compatible PostgreSQL connection string.

**Format:**

```
postgresql+asyncpg://USER:PASSWORD@HOST:PORT/DBNAME?ssl=require&prepared_statement_cache_size=0
```

> **Get it from Supabase:** Project → Settings → Database → "Connection string" tab → select **URI**. Then:
>
> - Change the scheme from `postgresql://` to `postgresql+asyncpg://`
> - Append `?ssl=require&prepared_statement_cache_size=0` to the end
> - Use the **Supabase pooler** host (see [Supabase section](#supabase-database-connection--pgbouncer-fix) below)

> **Special characters in passwords:** If your password contains `@`, `[`, `]`, `/`, or other reserved URL characters, percent-encode them. For example `@` → `%40`, `[` → `%5B`, `]` → `%5D`.

---

### `SECRET`

A random string used to sign and verify JWT tokens. **Must be at least 32 characters.**

Generate one securely:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

> Never commit this value to version control.

---

### `IMAGEKIT_PRIVATE_KEY`

Used to authenticate server-side upload requests to ImageKit CDN (v5 SDK — only the private key is required).

> **Get it from ImageKit:** Dashboard → Developer Options → API Keys → copy the **Private key**.

---

## Supabase Database Connection & PgBouncer Fix

### Why use the pooler?

Supabase runs **PgBouncer** as a connection pooler in front of PostgreSQL. Direct connections (port 5432) are limited in number on the free tier, so Supabase recommends using the **Transaction Mode pooler** (port 6543) for serverless / async workloads.

### Pooler connection string

In your Supabase dashboard, go to:
**Project → Settings → Database → Connection pooling**

Select **Transaction mode** and copy the URI. It will look like:

```
postgres://postgres.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:6543/postgres
```

Change the scheme and append the required query parameters:

```
postgresql+asyncpg://postgres.<project-ref>:<password>@aws-1-eu-west-1.pooler.supabase.com:6543/postgres?ssl=require&prepared_statement_cache_size=0
```

---

### The `DuplicatePreparedStatementError` — What it is and how we fix it

#### What causes it?

```
asyncpg.exceptions.DuplicatePreparedStatementError:
    prepared statement "__asyncpg_stmt_1__" already exists
```

`asyncpg` prepares SQL statements on the database server and caches them by **name** (e.g. `__asyncpg_stmt_1__`). PgBouncer in **Transaction Mode** does not preserve server-side session state between queries — each transaction may be routed to a different PostgreSQL backend. When two requests prepare a statement with the **same name** on different backends, PostgreSQL rejects the second one as a duplicate.

#### The three-part fix applied in `app/core/db.py`

**1. `NullPool` — disable SQLAlchemy's own connection pool**

```python
from sqlalchemy.pool import NullPool

engine = create_async_engine(DATABASE_URL, poolclass=NullPool)
```

Without a local pool, a fresh connection is opened and closed for each request. PgBouncer then manages pooling transparently, eliminating stale server-side state leaking across requests.

**2. `prepared_statement_cache_size=0` — disable asyncpg's client-side cache**

Add to the `DATABASE_URL` query string:

```
?ssl=require&prepared_statement_cache_size=0
```

This tells `asyncpg` not to cache prepared statements at all, so it never tries to reuse a previously prepared statement name.

**3. `prepared_statement_name_func` — unique names per statement**

```python
from uuid import uuid4

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,
    pool_pre_ping=True,
    connect_args={
        "timeout": 10,
        "prepared_statement_name_func": lambda: f"__asyncpg_{uuid4()}__",
    },
)
```

Even if a prepared statement does get sent (e.g. through a third-party library path), generating a UUID-based name guarantees each one is globally unique and will never collide with a statement from a different connection or request.

All three changes together ensure the app works reliably with PgBouncer's Transaction Mode pooling.

---

## Running the App

### Start the FastAPI backend

```bash
cd Social_App/app
uvicorn main:app --reload
```

API will be available at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### Start the Streamlit frontend

Open a second terminal:

```bash
cd Social_App
streamlit run frontend/frontend.py
```

UI will open at `http://localhost:8501` in your browser.
