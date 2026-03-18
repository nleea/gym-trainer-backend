# trainerGM — backend

FastAPI + PostgreSQL + SQLModel. Backend del sistema gym-trainer.

See `AGENTS.md` for the full agent workflow and MCP protocol.

---

## Stack

- Python + FastAPI
- SQLModel + SQLAlchemy (async)
- PostgreSQL
- Alembic (migraciones)
- Poetry (dependencias)

## Project root

```
backend/
  app/
    core/         # config, seguridad, dependencies.py
    db/           # session.py (AsyncSession)
    dependencies.py  # factories de repos y services
    main.py       # registro de routers
    models/       # SQLModel table classes
    repositories/ # interface/ + implementations/postgres/
    routers/      # endpoints FastAPI
    schemas/      # Pydantic/SQLModel request/response schemas
    services/     # lógica de negocio
  alembic/        # migraciones
```

## Architecture pattern

```
router → service → repository (interface + postgres impl) → AsyncSession
```

- **Routers**: solo HTTP, sin lógica de negocio. Llaman al service.
- **Services**: lógica de negocio. Llaman al repository.
- **Repositories**: acceso a DB. Interface ABC + implementación postgres.
- **Models**: SQLModel con `table=True`. Solo estructura de datos.
- **Schemas**: Pydantic/SQLModel sin `table=True`. Request/response DTOs.

## Key files

- `app/core/dependencies.py` — `get_current_user` (auth guard)
- `app/db/session.py` — `db_context` (AsyncSession)
- `app/dependencies.py` — factories de repos y services inyectados en routers
- `app/main.py` — registro de todos los routers con prefix

## Auth

- JWT Bearer token
- `get_current_user` → dependency injection en cualquier endpoint protegido
- `User.id` es `uuid.UUID` (no int)

## Async

- Todo `async/await`. No usar funciones síncronas de SQLAlchemy.
- `AsyncSession` de `sqlalchemy.ext.asyncio`

## Naming

- Archivos: `snake_case.py`
- Clases SQLModel: PascalCase (`UserConfig`)
- Schemas: PascalCase con sufijo descriptivo (`UserConfigResponse`, `AppearanceConfigSchema`)
- Repos: clase con sufijo `Repository` (`UserConfigRepository`)
- Services: clase con sufijo `Service` (`UserConfigService`)

## Migraciones

- Siempre crear migración Alembic al añadir/modificar modelos.
- Archivo en `alembic/versions/` con número secuencial: `00N_descripcion.py`.
- Preferir migraciones aditivas (no destructivas).

## Do NOT

- No lógica de negocio en routers.
- No acceso directo a DB en services (usar repos).
- No mezclar schemas de tabla con schemas de respuesta.
- No usar `User.id` como int — es `uuid.UUID`.
- No crear endpoints sin pasar por `get_current_user` si requieren auth.
