# AGENTS.md

## Cursor Cloud specific instructions

### Overview

**arch-fastapi** is a DDD-structured FastAPI authentication/RBAC template.
See `README.md` for project structure, conventions, and standard commands (`uv sync`, `fastapi dev`, `ruff check`, etc.).

### Required Services

| Service     | Port  | Purpose                           |
|-------------|-------|-----------------------------------|
| PostgreSQL  | 5432  | Primary relational store (asyncpg)|
| MongoDB     | 27017 | Document store (motor)            |
| Redis       | 6379  | Token allow-list & scope cache    |
| FastAPI app | 8000  | `fastapi dev --host 0.0.0.0`     |

### Starting Services (non-Docker)

```bash
# PostgreSQL (Ubuntu 24.04)
sudo pg_ctlcluster 16 main start
PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE IF NOT EXISTS auth;"

# MongoDB
sudo mongod --dbpath /var/lib/mongodb --logpath /var/log/mongodb/mongod.log --fork

# Redis (no password by default in .env)
sudo redis-server --daemonize yes

# FastAPI
source .venv/bin/activate
fastapi dev --host 0.0.0.0 --port 8000
```

### Gotchas

- **asyncpg + timestamps**: Entity `_utcnow()` returns naive UTC datetimes (no tzinfo). asyncpg is strict: `TIMESTAMP WITHOUT TIME ZONE` columns reject timezone-aware datetimes.
- **PostgreSQL auth**: `pg_hba.conf` must allow `md5` (not just `peer`) for TCP connections from localhost. Default Ubuntu install uses `peer` for local socket only.
- **Admin seed**: On startup the app auto-creates admin user (`admin`/`admin`), role, and permission with scope `admin`. The `admin` scope bypasses all permission checks.
- **No automated test suite yet**: The `tests/` directory is empty; tests can be added with `pytest` + `pytest-asyncio` + `httpx`.
- **ruff bans `json` module**: Use `orjson` instead. The `TID253` rule triggers on `import json`.
- **Pre-commit hooks**: Run `uv run pre-commit install` once to enable ruff lint + format on every commit.
