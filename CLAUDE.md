# CLAUDE.md

Multi-tenant SaaS for truck fleet ops: load booking, driver/allocation management, client tracking, invoicing, GPS tracking, reports. Phases 1–11 complete (incl. invoicing/PDF and the customer Client Portal); Phase 14 (Flutter driver app) UI shell done; 12, 13, 15 planned (branding, 2FA, live GPS tracking).

## Stack
- **Backend**: Python 3.11, FastAPI 0.128, SQLAlchemy 2, Pydantic v2, Alembic → `apps/backend/`
- **Frontend**: Angular 21 standalone, Angular Material, ngx-translate → `apps/admin-frontend/`
- **Mobile** (Phase 14): Flutter (Dart), Riverpod + GoRouter → `apps/driver-mobile/` — UI shell + light/dark theme done (mock data); see `mobile_app_design.md` for the API gaps to wire up next
- **DB/Infra**: PostgreSQL 15, Docker Compose, GitHub Actions CI

## Run
```
make dev        # full stack (docker)
make test       # pytest (real postgres)
make migrate    # alembic upgrade head
make seed       # roles + superadmin (admin@system.local)
make seed-demo  # demo tenant + sample accounts (admin@demo.transport.com etc., see README)
```

## Conventions (strict)
- **Tenant isolation** — all queries via `TenantAwareRepository`; never raw queries without `tenant_id`
- **Soft delete** — `soft_delete()` only; `get_active_by_id()`, never `get_by_id()`
- **Load state machine** — only via `LoadService.transition_status()`; no direct status writes
- **Auth** — `get_current_user_context()` → `CurrentUser{user_id, tenant_id, roles, is_superadmin}`; gate with `require_roles()`
- **Audit** — `AuditService.log()` on every write; never skip
- **Dates (storage)** — `utc_now()` from `app/core/datetime_utils.py`, never `datetime.utcnow()`
- **Dates (display)** — schema fields shown to users use `LocalDateTime` (`app/schemas/common.py`); it serializes via `format_for_display(dt, get_current_timezone())`, rendering in the requesting user's `User.timezone` (set via `timezone_context.ContextVar`, populated in `get_current_user`). Falls back to `settings.DEFAULT_TIMEZONE`.
- **Client portal linking** — `Client.user_id` (nullable FK → `users.id`, unique per `(tenant_id, user_id)` — NOT globally unique) links a login to a client/company record, mirroring `Driver.user_id`. A shipper can have a separate `Client`/relationship per tenant. Set/changed via `_link_client()` in `user_service.py` (User form → pick Client) or `ClientService.link_portal_account()`/`unlink_portal_account()` (Client form → enter shipper email, cross-tenant lookup via `UserRepository.get_by_email()`); both always `db.flush()` after unsetting the old link before assigning a new one, or the unique constraint raises. `/portal/*` aggregates across ALL of the caller's linked `Client` rows via `ClientRepository.get_all_by_user_id()` (cross-tenant, by design — scoped to the caller's own `user_id`).
- **Login/account emails** — `User.email`, `LoginRequest.email`, `TenantCreate.admin_email`, `LinkPortalAccountRequest.email` etc. use `UserEmail` (`app/schemas/common.py`), a lenient `local@domain.tld` check — NOT `pydantic.EmailStr`, which rejects special-use TLDs like `.local` and would lock out internal accounts (e.g. the seeded SuperAdmin). Business contact emails (`Client.email`, `Driver.email`) are unaffected, plain `Optional[str]`.
- **Password complexity** — shared `validate_password_complexity()` (`app/schemas/common.py`, ≥8 chars + upper/lower/digit) used by `UserCreate.password` and `PasswordResetConfirm.new_password`; don't re-inline the regex checks.
- **Forgot/reset password** — `PasswordResetToken` (mirrors `RefreshToken`: hashed via `hash_token()`, single-use, 1h TTL, `PasswordResetTokenRepository`). `POST /auth/forgot-password` always returns the same generic message (no email enumeration); `reset_token` is only included when `settings.DEBUG=True` (no email service yet — UI shows a "Continue to Reset Password" link in dev). `reset_password()` revokes all of the user's refresh tokens.
- **Angular** — no HTTP in components; `*appHasRole` for visibility; `NotificationService` for toasts; no cross-feature imports

## Key Paths
| | Path |
|-|------|
| API routes | `apps/backend/app/api/v1/*.py` |
| Client portal API | `apps/backend/app/api/v1/portal.py` (role `Client` only, read-mostly, scoped via `Client.user_id`) |
| Services | `apps/backend/app/services/*_service.py` |
| Repos | `apps/backend/app/repositories/*.py` |
| Models / Schemas | `apps/backend/app/models/*.py` · `app/schemas/*.py` |
| Migrations | `apps/backend/alembic/versions/` |
| Angular features | `apps/admin-frontend/src/app/features/` |
| Client portal UI | `apps/admin-frontend/src/app/features/portal/`, `layouts/portal-layout/` |
| Test fixtures | `apps/backend/tests/conftest.py` |

## Patterns
**New endpoint:** schema → repo → service → `api/v1/` → register in `__init__.py` → test

**New Angular feature:** `features/<name>/` → lazy route in `app.routes.ts` → service for all HTTP → `*appHasRole`

**Migration:** `alembic revision --autogenerate -m "name"` → `alembic upgrade head`. Adding a value to a Postgres native ENUM is **not** autogenerated — hand-write `with op.get_context().autocommit_block(): op.execute("ALTER TYPE <enum> ADD VALUE IF NOT EXISTS '<value>'")` (downgrade is a no-op; Postgres can't drop enum values).

**Tests** hit real PostgreSQL (`transport_db_test`); fixtures: `db_session`, `client`, `seed_roles`, `seed_tenant`, `seed_superadmin`
