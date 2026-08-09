# Local production-like stack

1. Copy `.env.example` to `.env` and set a strong database password.
2. Start services:

```bash
docker compose up --build
```

3. API health endpoint: `http://localhost:8000/health`.

The compose stack separates API, worker, and scheduler processes and uses PostgreSQL for durable state and Redis for coordination/events.
