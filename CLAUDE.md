# My Gym Trainer — Backend Migration

## Skills
Always load the following skills before generating code.
Skills must be applied in the following order:

1. ~/.agents/skills/senior-backend/SKILL.md  
2. ~/.agents/skills/backend-patterns/SKILL.md
3. ~/.agents/skills/python-performance-optimization/SKILL.md
4. ~/.agents/skills/code-documentation-code-explain/SKILL.md

When rules conflict, follow the higher-priority skill.
Do not skip these skills.
Apply them before proposing architecture, writing code, refactoring, or explaining implementation details.

---

## Project Overview
PWA for personal trainers and their clients. Currently uses Firebase as full backend.
**Goal:** Replace Firebase (Auth, Firestore, Storage, Cloud Functions) with FastAPI + PostgreSQL.
The frontend (Vue 3) is NOT to be touched — only the backend is in scope.

---

## Target Stack
- **Framework:** FastAPI (Python 3.11+)
- **ORM:** SQLModel (Pydantic v2 compatible)
- **Database:** PostgreSQL 16
- **Auth:** JWT with python-jose + bcrypt
- **Async:** asyncpg + AsyncSession everywhere
- **Deploy:** Docker Compose on Orange Pi 5 (ARM64)
- **Storage:** Cloudflare R2 (prepare fields, do not implement yet)
- **Migrations:** Alembic

---

## Project Structure
```
backend/
├── app/
│   ├── main.py
│   ├── core/
│   │   ├── config.py          # Settings from .env
│   │   ├── security.py        # JWT create/verify, bcrypt
│   │   └── dependencies.py    # get_current_user, require_trainer, require_client
│   ├── models/                # SQLModel table models (one file per domain)
│   ├── schemas/               # Pydantic request/response schemas
│   ├── routers/               # FastAPI routers (one file per domain)
│   ├── services/              # Business logic (one file per domain)
│   ├── repositories/          # DB access via AsyncSession (one file per domain)
│   └── db/
│       ├── session.py         # Async engine + session factory
│       └── init_db.py         # Table creation
├── alembic/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Domain Models
Map directly from Firestore collections to PostgreSQL tables:

| Table | Key Fields |
|---|---|
| users | id (UUID), email, name, role (trainer\|client), phone, created_at |
| clients | id, trainer_id (FK), status, start_date, goals, weight, height, age, plan_id, nutrition_plan_id |
| training_plans | id, trainer_id (FK), name, weeks (JSON), created_at, updated_at |
| nutrition_plans | id, trainer_id (FK), name, days (JSON), target_calories, created_at, updated_at |
| training_logs | id, client_id (FK), trainer_id (FK), date, exercises (JSON), duration |
| meal_logs | id, client_id (FK), date, type (desayuno\|almuerzo\|cena\|snack), description, calories, protein |
| progress_entries | id, client_id (FK), type, date, weight, measurements (JSON), photos (JSON), notes |
| attendance | id, client_id (FK), trainer_id (FK), date, attended (bool), notes |
| metrics | id, client_id (FK), date, weight_kg, body_fat_pct, muscle_pct, waist, arm, chest |

**Rules:**
- All PKs are UUID
- All tables have `created_at`, `updated_at`
- JSON fields (weeks, days, exercises, measurements, photos) use PostgreSQL JSON type
- Passwords stored as bcrypt hash, never exposed in responses

---

## Auth System (replaces Firebase Auth + Cloud Function)

| Endpoint | Role | Description |
|---|---|---|
| POST /auth/register | public | Create trainer account |
| POST /auth/login | public | Returns access_token + refresh_token |
| POST /auth/refresh | public | Renew access_token |
| POST /auth/create-client | trainer only | Create client user (replaces Cloud Function) |

JWT payload: `{ sub: user_id, role: "trainer"|"client", exp }`

---

## API Endpoints

### Clients (trainer only)
```
GET    /clients                      → list trainer's clients
POST   /clients                      → create client profile
GET    /clients/{id}                 → full client profile
PUT    /clients/{id}                 → update client data
GET    /clients/{id}/summary         → dashboard summary
```

### Training Plans
```
GET    /training-plans               → trainer: list own plans
POST   /training-plans               → trainer: create plan
GET    /training-plans/{id}          → trainer or assigned client
PUT    /training-plans/{id}          → trainer: update
POST   /training-plans/{id}/assign   → trainer: assign to client with dates
```

### Nutrition Plans
```
GET    /nutrition-plans              → trainer: list own plans
POST   /nutrition-plans              → trainer: create plan
GET    /nutrition-plans/{id}         → trainer or assigned client
PUT    /nutrition-plans/{id}         → trainer: update
POST   /nutrition-plans/{id}/assign  → trainer: assign to client
```

### Training Logs
```
GET    /training-logs                         → filters: client_id, week_start
POST   /training-logs                         → client: create or upsert by day
PUT    /training-logs/{id}                    → client: update session
GET    /training-logs/{client_id}/week/{date} → logs for a specific week
```

### Meal Logs
```
GET    /meal-logs        → filters: client_id, date, range
POST   /meal-logs        → client: register meal
DELETE /meal-logs/{id}   → client: delete meal
```

### Progress
```
GET    /progress/{client_id}   → trainer or client: list entries
POST   /progress               → client: new entry (photos: store path only, no upload yet)
```

### Attendance
```
GET    /attendance/{client_id}   → trainer: list attendance
POST   /attendance               → trainer: register attendance
PUT    /attendance/{id}          → trainer: update
```

### Metrics
```
GET    /metrics/{client_id}   → trainer or client: list metrics
POST   /metrics               → client: new entry
PUT    /metrics/{id}          → client: update
DELETE /metrics/{id}          → client: delete
```

---

## Authorization Rules
Every endpoint must validate ownership:
- A **trainer** can only access data from their own clients
- A **client** can only access their own data
- Use `require_trainer` and `require_client` dependencies from `core/dependencies.py`
- Return 403 (not 404) when a user tries to access someone else's resource

---

## Coding Rules
- All DB operations must be `async/await` (AsyncSession + asyncpg)
- Never put business logic in routers — routers call services, services call repositories
- Use `HTTPException` with correct status codes: 401, 403, 404, 422
- Never expose `password_hash` in any response schema
- CORS: allow `http://localhost:3000` in development
- All JSON fields validated as `dict | list` in Pydantic schemas
- Use `Optional` and sensible defaults in schemas to handle partial updates (PATCH-style via PUT)

---

## Docker Compose (Orange Pi ARM64)
- `fastapi` service: `python:3.11-slim` (ARM64 compatible)
- `postgres` service: `postgres:16` (ARM64 compatible)
- `nginx` service: reverse proxy to fastapi
- Persistent volume for PostgreSQL data
- Health checks on both fastapi and postgres
- All secrets via `.env` file

---

## Seed Data (for testing without frontend)
Create a script `scripts/seed.py` that inserts:
- 1 trainer user
- 2 client users linked to that trainer
- 1 training plan assigned to client 1
- 1 nutrition plan assigned to client 1
- Sample training logs and metrics for client 1

---

## Out of Scope (do not implement)
- Anything inside `/vue/` — frontend is migrated later
- WebSockets or realtime features
- File upload to R2 (prepare the field in the model, nothing more)
- Payments or push notifications
- Multi-tenancy beyond trainer → clients relationship

---

## Definition of Done
- All endpoints documented and testable via `/docs` (FastAPI Swagger)
- Docker Compose runs with `docker compose up` on ARM64
- Alembic migration creates all tables from scratch
- Seed script populates test data
- Auth flow works end to end: register → login → use token → access protected route