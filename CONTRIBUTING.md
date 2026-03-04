# Contributing

## Development workflow

1. Create a feature branch from `main`.
2. Keep commits focused and descriptive.
3. Run backend + frontend quality checks before opening a PR.
4. Include testing/validation output in PR notes.

## Required quality checks

### Backend (`backend/`)

```bash
ruff check .
mypy leadbot tests
pytest
```

For faster local iteration, run targeted suites when touching those areas:

```bash
pytest tests/test_dedup.py tests/test_scorer.py tests/test_api_auth.py tests/test_api_routes_misc.py tests/test_mcp_tools.py
```

### Frontend (`frontend/`)

```bash
npm run lint
npm run typecheck
npm run build
```

## Project layout

- `backend/`: Python service, ingestion/scoring/export pipeline, API, and MCP interfaces.
- `frontend/`: Next.js App Router client.
- `docker-compose.yml`: local multi-service bootstrap (`leady-api` + `leady-ui`).

## Pull requests

- Include a concise summary and testing notes.
- Prefer incremental, scaffold-safe changes to avoid path churn.
- If behavior changes, update README and relevant environment docs.
