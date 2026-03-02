# AGENTS.md

## Cursor Cloud specific instructions

### Overview

This is **arch-fastapi**, a FastAPI-based RBAC authentication microservice. It provides JWT auth, user/role/permission CRUD, and scope-based authorization. See `README.md` for basic commands (`uv sync`, `fastapi dev`).

### Required Services

| Service | Default Port | Notes |
|---------|-------------|-------|
| FastAPI app | 8000 | `source .venv/bin/activate && fastapi dev --host 0.0.0.0 --port 8000` |
| MySQL | 3306 | Must have a database named `auth` created. Root password configured in `.env`. |
| Redis | 6379 | Password configured in `.env` via `REDIS_PASSWORD`. Start with `--requirepass`. |

### Starting Services

```bash
# Start MySQL
sudo mkdir -p /var/run/mysqld && sudo chown mysql:mysql /var/run/mysqld
sudo mysqld --user=mysql --datadir=/var/lib/mysql --socket=/var/run/mysqld/mysqld.sock --pid-file=/var/run/mysqld/mysqld.pid &
sleep 5
sudo chmod 755 /var/run/mysqld

# Start Redis (password from .env)
sudo redis-server --daemonize yes --requirepass 939228

# Create auth database if not exists
mysql -u root -p939228 -e "CREATE DATABASE IF NOT EXISTS auth;"

# Start FastAPI dev server
source .venv/bin/activate
fastapi dev --host 0.0.0.0 --port 8000
```

### Gotchas

- `.env` has `ENVIRONMENT` field: the `Settings` class only accepts `"test"` or `"prod"` (not `"local"`). Use `ENVIRONMENT=test` for development.
- The `.env` uses `REDIS_DB=0` but the Settings class field is `REDIS_AUTH_DB`. The `REDIS_DB` value is silently ignored (defaults to 0 anyway via `extra="ignore"`).
- On startup the app auto-seeds an admin user (`admin`/`admin`), admin role, and admin permission with scope `admin`. The admin scope grants access to all protected endpoints.
- No automated test suite exists in this repository.
- MySQL socket permissions: after starting `mysqld`, run `sudo chmod 755 /var/run/mysqld` so non-root users can connect via socket.
- `passlib` logs a harmless warning about bcrypt version (`module 'bcrypt' has no attribute '__about__'`). This does not affect functionality.
