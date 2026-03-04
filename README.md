# Leady

Leady is a scaffolded mono-repo for building a lead discovery, enrichment, scoring,
and export platform with a Python backend and a Next.js frontend.

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
│   └── tests/
├── frontend/
│   └── src/
│       ├── app/
│       ├── components/
│       ├── lib/
│       ├── stores/
│       └── types/
├── .env.example
├── .gitignore
├── CONTRIBUTING.md
├── docker-compose.yml
└── LICENSE
```

## Quick start

1. Copy environment defaults:
   ```bash
   cp .env.example .env
   ```
2. Start local services:
   ```bash
   docker compose up
   ```

## Incremental implementation plan

- Fill backend package modules under `backend/leadbot/` by domain.
- Add backend tests in `backend/tests/` as each module is implemented.
- Build frontend routes/components under `frontend/src/` using App Router patterns.

This scaffold intentionally favors stable paths so future phases can ship without
renaming files or moving directories.
