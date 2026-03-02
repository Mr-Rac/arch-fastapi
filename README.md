# arch-fastapi

A scalable FastAPI quick-start template following **DDD** (Domain-Driven Design) architecture.

## Features

- **DDD project structure** – domain / infra / api layers with clear boundaries
- **PostgreSQL** (asyncpg) + **MongoDB** (motor) + **Redis** (hiredis) out of the box
- **JWT authentication** with token allow-list and scope-based RBAC
- **Unified error handling** – `BizError` + error codes + consistent JSON response
- **orjson** for high-performance JSON serialization (stdlib `json` is banned via ruff)
- **ruff** for linting & formatting, enforced by **pre-commit** hooks
- **uv** for fast, reproducible dependency management

## Quick Start

### Prerequisites

- Python ≥ 3.13
- [uv](https://docs.astral.sh/uv/)

### Setup

```bash
# Create venv & install dependencies
uv sync

# Install dev dependencies (ruff, pytest, pre-commit …)
uv sync --group dev

# Set up git hooks (ruff check + format on every commit)
uv run pre-commit install

# Copy & edit environment variables
cp .env.example .env   # or edit the existing .env
```

### Run (local)

Start PostgreSQL, MongoDB and Redis (e.g. via Docker Compose):

```bash
docker compose up -d postgres mongo redis
```

Then start the dev server:

```bash
source .venv/bin/activate
fastapi dev --host 0.0.0.0 --port 8000
```

API docs: <http://localhost:8000/api/docs>

### Run (Docker Compose, all-in-one)

```bash
docker compose up --build
```

## Project Structure

```
app/
├── main.py              # FastAPI app + exception handlers
├── lifespan.py          # Startup / shutdown (DB, cache, seed)
├── core/                # Cross-cutting infrastructure
│   ├── config.py        # pydantic-settings
│   ├── errors.py        # ErrorCode enum + BizError
│   ├── response.py      # Unified Result model
│   ├── security.py      # JWT + bcrypt utilities
│   └── database/        # PG / Mongo / Redis connections
├── domain/              # Domain layer (per bounded context)
│   └── auth/
│       ├── entity.py    # SQLModel ORM entities
│       ├── schema.py    # Request / Response DTOs
│       ├── repository.py# Repository protocols (interfaces)
│       └── service.py   # Business logic
├── infra/               # Infrastructure implementations
│   └── auth/
│       ├── pg_repository.py
│       └── redis_repository.py
└── api/                 # HTTP interface
    ├── deps.py          # FastAPI dependencies & auth guards
    └── v1/
        ├── router.py
        └── auth.py
```

## Code Conventions

### Docstrings (Google style)

```python
async def login(self, username: str, password: str) -> TokenPair:
    """Authenticate user and issue JWT token pair.

    Args:
        username: Login name.
        password: Plaintext password.

    Returns:
        TokenPair with access and refresh tokens.

    Raises:
        BizError: INVALID_CREDENTIALS if authentication fails.
    """
```

### Error Codes

| Range | Category        |
|-------|-----------------|
| 0     | Success         |
| 1xxx  | Client errors   |
| 2xxx  | Auth errors     |
| 5xxx  | Server errors   |

See `app/core/errors.py` for the full enumeration.

## Tooling

| Tool        | Purpose                  | Command                         |
|-------------|--------------------------|---------------------------------|
| uv          | Dependency management    | `uv sync`                       |
| ruff        | Lint + format            | `ruff check .` / `ruff format .`|
| pre-commit  | Git hooks                | `uv run pre-commit install`     |
| pytest      | Testing                  | `uv run pytest`                 |

## License

MIT
