# CLAUDE.md

Multi-tenant SaaS for truck fleet ops: load booking, driver/allocation management, client tracking, invoicing, GPS tracking, reports. Phases 1–10 complete; 11–15 planned (client portal, branding, 2FA, React Native driver app, live GPS tracking).

## Stack
- **Backend**: Python 3.11, FastAPI 0.128, SQLAlchemy 2, Pydantic v2, Alembic → `apps/backend/`
- **Frontend**: Angular 21 standalone, Angular Material, ngx-translate → `apps/admin-frontend/`
- **Mobile** (Phase 15): React Native + Expo → `apps/driver-mobile/`
- **DB/Infra**: PostgreSQL 15, Docker Compose, GitHub Actions CI

## Run
```
make dev        # full stack (docker)
make test       # pytest (real postgres)
make migrate    # alembic upgrade head
make seed       # roles + superadmin
```

## Conventions (strict)
- **Tenant isolation** — all queries via `TenantAwareRepository`; never raw queries without `tenant_id`
- **Soft delete** — `soft_delete()` only; `get_active_by_id()`, never `get_by_id()`
- **Load state machine** — only via `LoadService.transition_status()`; no direct status writes
- **Auth** — `get_current_user_context()` → `CurrentUser{user_id, tenant_id, roles, is_superadmin}`; gate with `require_roles()`
- **Audit** — `AuditService.log()` on every write; never skip
- **Dates** — `datetime.now(timezone.utc)`, never `datetime.utcnow()`
- **Angular** — no HTTP in components; `*appHasRole` for visibility; `NotificationService` for toasts; no cross-feature imports

## Key Paths
| | Path |
|-|------|
| API routes | `apps/backend/app/api/v1/*.py` |
| Services | `apps/backend/app/services/*_service.py` |
| Repos | `apps/backend/app/repositories/*.py` |
| Models / Schemas | `apps/backend/app/models/*.py` · `app/schemas/*.py` |
| Migrations | `apps/backend/alembic/versions/` |
| Angular features | `apps/admin-frontend/src/app/features/` |
| Test fixtures | `apps/backend/tests/conftest.py` |

## Patterns
**New endpoint:** schema → repo → service → `api/v1/` → register in `__init__.py` → test

**New Angular feature:** `features/<name>/` → lazy route in `app.routes.ts` → service for all HTTP → `*appHasRole`

**Migration:** `alembic revision --autogenerate -m "name"` → `alembic upgrade head`

**Tests** hit real PostgreSQL (`transport_db_test`); fixtures: `db_session`, `client`, `seed_roles`, `seed_tenant`, `seed_superadmin`
