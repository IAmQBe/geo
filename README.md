# Geo / Jam Bot

Production-oriented implementation scaffold based on [ARCHITECTURE.md](./ARCHITECTURE.md).

## Implemented Coverage

- Section 4 (`Database Schema`): async SQLAlchemy models + Alembic bootstrap (`alembic/`)
- Section 5 (`Smart Parser`): `parser/` with sources, anti-detection, browser pool, normalization pipeline
- Section 6 (`Bot Flow`): aiogram handlers + FSM + middleware stack + core user flow
- Section 7 (`AI Integration`): LLM router, OpenAI/Ollama clients, recommendation engine, NL search, description generation
- Section 8 (`Admin Panel`): FastAPI admin, JWT auth, Jinja templates, CRUD/read screens
- Section 9 (`Infrastructure`): full `docker-compose.yml`, `docker-compose.dev.yml`, `nginx/`, `monitoring/`
- Section 10 (`Project Structure`): aligned folder layout across bot/db/parser/tasks/ai/admin/storage/tests
- Section 11 (`Security`): throttling middleware, JWT admin auth, parser proxy hooks, secret-based config
- Section 12 (`Scaling baseline`): Celery tasks/beat schedules, parse/AI/maintenance background jobs

## Quick Start

1. Create env and install dependencies

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

2. Start infrastructure

```bash
docker compose up -d postgres redis minio
```

3. Apply schema and seed

```bash
alembic upgrade head
python -m scripts.seed_data
```

4. Run services

```bash
# bot (polling if WEBHOOK_URL is empty)
python -m bot.main

# admin panel
uvicorn admin.main:app --host 0.0.0.0 --port 8000

# celery worker
celery -A tasks.celery_app:celery_app worker --loglevel=info

# celery beat
celery -A tasks.celery_app:celery_app beat --loglevel=info
```

## Utility Scripts

- `python -m scripts.init_db` — create tables directly from SQLAlchemy metadata
- `python -m scripts.seed_data` — seed cities/categories/demo places
- `python -m scripts.import_places <file.csv>` — import places
- `python -m scripts.export_places <file.csv> [--city CITY]` — export places
- `python -m scripts.health_check` — check DB/Redis/MinIO connectivity

## Tests

```bash
pytest -q
```

Note: runtime requires Python 3.11+ and project dependencies installed.
