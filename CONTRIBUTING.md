# Contributing

## Development workflow

1. Create a feature branch from `main`.
2. Keep commits focused and descriptive.
3. Run tests and lint checks before opening a PR.

## Project layout

- `backend/`: Python service, ingestion/scoring/export pipeline, API, and MCP interfaces.
- `frontend/`: Next.js App Router client.
- `docker-compose.yml`: local multi-service bootstrap.

## Pull requests

- Include a concise summary and testing notes.
- Prefer incremental, scaffold-safe changes to avoid path churn.
