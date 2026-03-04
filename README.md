# Leady

Leady is a mono-repo for discovering, enriching, scoring, and exporting outbound leads with:

- **`leady-api`**: a Python/FastAPI backend with CLI + MCP tools.
- **`leady-ui`**: a Next.js dashboard for auth, pipeline monitoring, and lead review.

## Repository structure

```text
.
├── backend/
│   ├── leadbot/
│   │   ├── api/
│   │   ├── db/
│   │   ├── enrichment/
│   │   ├── exports/
│   │   ├── mcp/
│   │   ├── scoring/
│   │   ├── sources/
│   │   ├── utils/
│   │   ├── __main__.py
│   │   └── cli.py
│   ├── tests/
│   └── pyproject.toml
├── frontend/
│   └── src/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── docker-compose.yml
└── LICENSE
```

## Local setup

1. Copy and edit environment variables:

   ```bash
   cp .env.example .env
   ```

2. Start the full stack:

   ```bash
   docker compose up --build
   ```

3. Access services:
   - API: `http://localhost:8000`
   - UI: `http://localhost:3000`

### Useful Docker Compose commands

```bash
# Start services in detached mode
docker compose up -d

# Rebuild and restart services
docker compose up --build -d

# Follow logs for all services
docker compose logs -f

# View logs for a specific service
docker compose logs -f leady-api
docker compose logs -f leady-ui

# List running services and status
docker compose ps

# Stop services
docker compose stop

# Stop and remove containers, networks, and anonymous volumes
docker compose down

# Stop and remove everything including named volumes (full reset)
docker compose down -v
```

## Authentication flows

### API local login

```bash
curl -s http://localhost:8000/api/auth/login \
  -H 'content-type: application/json' \
  -d '{"email":"demo@example.com","password":"superpass123","full_name":"Demo User"}'
```

Use the returned bearer token in protected routes:

```bash
curl -s http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

### API Google login (dev-mode token exchange)

```bash
curl -s http://localhost:8000/api/auth/google \
  -H 'content-type: application/json' \
  -d '{"google_token":"demo@example.com","full_name":"Demo User"}'
```

## Backend quality checks

Run checks from `backend/`:

```bash
ruff check .
mypy leadbot tests
pytest tests/test_dedup.py tests/test_scorer.py tests/test_api_auth.py tests/test_api_routes_misc.py tests/test_mcp_tools.py
pytest
```

The targeted pytest command covers utility dedup behavior, scoring logic, API auth/routes, and MCP tool contracts.

## Frontend quality checks

Run checks from `frontend/`:

```bash
npm run lint
npm run typecheck
npm run build
```

## MCP usage

Leady exposes MCP endpoints/tools through the backend app (`backend/leadbot/mcp/`).

Typical MCP tool flow:

1. Start API (`docker compose up`).
2. Connect your MCP client to the API-mounted MCP app.
3. Invoke tools that query lead, company, and run data.

Reference implementation files:
- `backend/leadbot/mcp/server.py`
- `backend/leadbot/mcp/tools.py`
- `backend/tests/test_mcp_tools.py`

## Extension guide

### Add a new data source

1. Add source module under `backend/leadbot/sources/`.
2. Emit `RawCandidate` payloads compatible with enrichment/scoring.
3. Wire source into CLI ingestion path (`backend/leadbot/cli.py`).
4. Add source-focused tests under `backend/tests/`.

### Add/adjust scoring rules

1. Update scoring primitives in `backend/leadbot/scoring/scorer.py`.
2. Update orchestration in `backend/leadbot/scoring/engine.py` if needed.
3. Extend `backend/tests/test_scorer.py` coverage.

### Add API routes

1. Add route module under `backend/leadbot/api/routes/`.
2. Register router in `backend/leadbot/api/app.py`.
3. Add integration tests in `backend/tests/`.

### Add UI views/components

1. Add route/page under `frontend/src/app/`.
2. Add reusable components under `frontend/src/components/`.
3. Keep API bindings in `frontend/src/lib/api.ts` and shared types in `frontend/src/types/`.

## Sample outputs

### Auth response (abridged)

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "demo@example.com",
    "full_name": "Demo User",
    "provider": "local"
  }
}
```

### Stats response (abridged)

```json
{
  "totals": {
    "companies": 42,
    "contacts": 128,
    "runs": 9
  }
}
```
