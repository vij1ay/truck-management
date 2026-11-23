# Transport & Load Management System.

A comprehensive multi-tenant transport and logistics management platform designed for regional operations (~300 km radius). Built with FastAPI backend, Angular admin portal, and Flutter mobile applications (planned).

---

## Project Overview

### Business Intent

- **Eliminate load data loss** through centralized digital records
- **Digitize booking and allocation workflow** for transport operations
- **Maintain centralized documentation** with secure cloud storage
- **Track truck movements** with GPS integration (future phase)
- **Enable controlled fund management** with transparent financial tracking
- **Provide profit tracking** and operational reports per load

### Target Users

| Role | Description |
|------|-------------|
| **SuperAdmin** | System-wide access across all tenants. Can only add TenantAdmin. |
| **TenantAdmin** | Full access within their organization. Manages users, trucks, drivers, clients, bookings. |
| **TransportAdmin** | Manages transport operations. Adds Clients, Drivers, Trucks, assigns Trucks/Drivers for bookings. |
| **Accounts** | Handles financial operations, invoices, payments. |
| **Client** | Books loads, views invoices. Can request truck preference, pickup date/time, origin/destination. |
| **Driver** | Mobile app access for load execution. Views assigned trips and starts them. |

### User Guides

End-user documentation (not developer setup) lives in `docs/`:

- [`docs/user-guide-web.md`](docs/user-guide-web.md) — the Angular admin
  portal and Client Portal, by role (SuperAdmin/TenantAdmin/TransportAdmin/
  Accounts/Driver/Client)
- [`docs/user-guide-mobile.md`](docs/user-guide-mobile.md) — the Flutter
  mobile app, for Driver and Client modes

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CORE COMPONENTS                          │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   FastAPI   │  │  PostgreSQL │  │   Redis (planned)       │ │
│  │   Backend   │  │  Multi-AZ   │  │   Cache & Sessions      │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Angular   │  │   Flutter   │  │   Cloud Document        │ │
│  │   Admin     │  │ Driver App  │  │   Storage (planned)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend API** | FastAPI (Python 3.11+) |
| **Database** | PostgreSQL 15+ |
| **ORM / Migrations** | SQLAlchemy 2 + Alembic |
| **Cache** | Redis (planned) |
| **Admin Frontend** | Angular 21 (standalone components) |
| **Mobile Apps** | Flutter (Android & iOS), single codebase |
| **Authentication** | JWT (Access + Refresh Tokens) |
| **Containerization** | Docker + Docker Compose |
| **CI/CD** | GitHub Actions |

---

## Monorepo Structure

```
truck-management-product/
│
├── apps/
│   ├── backend/                    # FastAPI Backend API
│   │   ├── alembic/versions/       # Database migration files
│   │   ├── app/
│   │   │   ├── api/v1/             # Route handlers
│   │   │   ├── core/               # Security, database, exceptions, logger
│   │   │   ├── dependencies/       # FastAPI DI (auth, db, tenant)
│   │   │   ├── middleware/         # Tenant context, error handler, trace ID
│   │   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── repositories/       # Data access layer
│   │   │   ├── schemas/            # Pydantic request/response schemas
│   │   │   ├── services/           # Business logic layer
│   │   │   └── scripts/            # Seed data utility
│   │   ├── tests/                  # pytest test suite
│   │   ├── uploads/                 # Avatar/logo files (local disk, gitignored)
│   │   ├── requirements.txt
│   │   ├── pyproject.toml
│   │   └── .env.example
│   │
│   ├── admin-frontend/             # Angular 21 Admin Portal
│   │   ├── src/app/
│   │   │   ├── core/               # Guards, interceptors, auth/permission services
│   │   │   ├── shared/             # Reusable components, directives
│   │   │   ├── features/           # Feature modules (loads, trucks, drivers, clients…)
│   │   │   └── layouts/            # Admin + Auth layouts
│   │   ├── angular.json
│   │   └── package.json
│   │
│   └── driver-mobile/              # Flutter Driver + Client Portal app — Phase 14
│
├── infra/
│   └── docker/
│       ├── Dockerfile.backend      # Python 3.11-slim image for FastAPI
│       └── Dockerfile.frontend     # Node 20-alpine image for Angular dev server
│
├── .github/
│   └── workflows/
│       └── ci.yml                  # GitHub Actions: lint + test + build
│
├── docker-compose.yml              # Full local stack (postgres + backend + frontend)
├── Makefile                        # Developer convenience commands
├── CLAUDE.md                       # AI coding assistant guide
└── README.md
```

---

## Getting Started

### Option A — Docker Compose (recommended)

**Prerequisites**: Docker Desktop

```bash
# Clone the repository
git clone <repository-url>
cd truck-management-product

# Configure backend environment
cp apps/backend/.env.example apps/backend/.env
# Edit apps/backend/.env — set JWT_SECRET_KEY and SUPERADMIN_PASSWORD

# Start everything (PostgreSQL + backend + frontend)
make dev
```

Services will be available at:
- Backend API + Swagger UI: `http://localhost:8000/docs`
- Angular Admin: `http://localhost:4200`

First-time setup (run migrations and seed initial data):

```bash
make migrate
make seed
```

Stop all containers:

```bash
make stop
```

---

### Option B — Local Setup (without Docker)

**Prerequisites**: Python 3.11+, PostgreSQL 15+, Node 20+

**Backend:**

```bash
cd apps/backend
python -m venv .venv
source .venv/bin/activate       # Linux/Mac
# or: .venv\Scripts\activate    # Windows
pip install -r requirements.txt
cp .env.example .env            # then edit .env
make migrate
make seed
make dev-backend
```

**Frontend:**

```bash
cd apps/admin-frontend
npm install
make dev-frontend
```

---

## Makefile Reference

| Command | Description |
|---------|-------------|
| `make dev` | Start full stack with Docker Compose |
| `make stop` | Stop and remove Docker containers |
| `make test` | Run backend tests against local PostgreSQL |
| `make test-cov` | Run tests with coverage report |
| `make lint` | Lint backend code with ruff |
| `make migrate` | Run Alembic migrations (`upgrade head`) |
| `make seed` | Seed initial roles + SuperAdmin user |
| `make dev-backend` | Start backend dev server locally (no Docker) |
| `make dev-frontend` | Start Angular dev server locally (no Docker) |

Run `make help` to see all commands.

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/transport_db` |
| `JWT_SECRET_KEY` | Secret for JWT signing | *(required — change in production)* |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | `7` |
| `BCRYPT_COST_FACTOR` | bcrypt work factor | `12` |
| `SUPERADMIN_EMAIL` | Initial admin email | `admin@system.local` |
| `SUPERADMIN_PASSWORD` | Initial admin password | *(required)* |
| `DEBUG` | Enable Swagger UI + verbose logging | `false` |
| `DEFAULT_TIMEZONE` | IANA tz name used to render timestamps for users without a personal timezone set (validated against `pytz`) | `Asia/Kolkata` |
| `UPLOAD_DIR` | Local-disk directory for uploaded profile pictures / logos (`<UPLOAD_DIR>/avatars/...`, gitignored) | `uploads` |
| `MAX_AVATAR_SIZE_MB` | Max accepted size for profile picture / logo uploads | `5` |

> **Note**: `SUPERADMIN_EMAIL` (and any other login email) may use an internal-style
> domain like `.local` — login/account schemas use a lenient `UserEmail` format check
> rather than `pydantic.EmailStr`, which rejects special-use TLDs and would otherwise
> lock the seeded SuperAdmin account out of `/api/v1/auth/login` entirely.

---

## Testing

```bash
make test          # Run all tests
make test-cov      # Run with coverage report

# Run a specific module (from apps/backend/)
python -m pytest tests/test_trucks.py -v
```

> **Test database**: Tests run against a dedicated `transport_db_test` database that is created automatically from `DATABASE_URL` in `.env`.

### Test Coverage

| Module | Tests | Status |
|--------|-------|--------|
| Auth (login, refresh, logout, internal-domain emails, forgot/reset password) | 15 | ✅ Pass |
| Trucks (CRUD, activate/deactivate, ownership, filters, profile picture, SuperAdmin tenant filter) | 17 | ✅ Pass |
| Drivers (CRUD, availability toggle, location, SuperAdmin tenant filter) | 10 | ✅ Pass |
| Clients (CRUD, GST validation, search, portal-account linking, profile picture, SuperAdmin tenant filter) | 15 | ✅ Pass |
| Documents (create, expiry status, list, delete) | 8 | ✅ Pass |
| Loads (CRUD, state machine, history, Load ID, POD documents, SuperAdmin tenant filter) | 26 | ✅ Pass |
| Allocations (assign, swap, conflict check) | 16 | ✅ Pass |
| Invoices & Payments (CRUD, lifecycle, PDF, overdue alerting, SuperAdmin tenant filter) | 23 | ✅ Pass |
| Reports & Analytics (summary, trends, revenue, performance) | 14 | ✅ Pass |
| Users (timezone preference, localized timestamps, client linking, profile picture, SuperAdmin tenant filter) | 13 | ✅ Pass |
| Tenants (logo / profile picture upload) | 3 | ✅ Pass |
| Client Portal (profile, shipments, history, documents, access control, multi-carrier) | 9 | ✅ Pass |
| Audit Logs (filters, user enrichment, tenant isolation, RBAC) | 5 | ✅ Pass |

**Total: 173 passed, 1 skipped** (`make test`)

---

## CI/CD

GitHub Actions runs automatically on push and pull requests to `main`/`develop`:

| Job | Steps |
|-----|-------|
| **Backend** | ruff lint → pytest (with real PostgreSQL service) |
| **Frontend** | npm ci → ng build (production) |

Pipeline config: `.github/workflows/ci.yml`

---

## Timezones & Localization

All timestamps are stored in the database as naive UTC (`utc_now()` in
`app/core/datetime_utils.py`). Display formatting happens **server-side**, so any client
(the Angular admin app today, the Phase 14 mobile app in future) gets identical,
ready-to-render strings with zero timezone logic of its own.

- **`DEFAULT_TIMEZONE`** (config, default `Asia/Kolkata`) — fallback timezone for users
  without a personal preference set, validated against `pytz.all_timezones_set`.
- **Per-user timezone** — each user has an optional `timezone` field (IANA tz name, e.g.
  `America/New_York`), settable via a `pytz`-backed dropdown in **Add/Edit User**
  (`apps/admin-frontend/.../user-form`). `GET /api/v1/users/timezones` returns the
  selectable list (`pytz.common_timezones`).
- **Request-scoped conversion** — `get_current_user` (`app/dependencies/auth.py`) sets the
  authenticated user's timezone in a `ContextVar` (`app/core/timezone_context.py`) for the
  duration of the request.
- **`LocalDateTime` schema type** (`app/schemas/common.py`) — applied to ~28 user-facing
  `datetime` fields across all response schemas (users, audit logs, loads, invoices,
  trucks, drivers, clients, documents, allocations, roles, tenants). Each is serialized via
  `format_for_display()` to a string like `"10 Jun 2026, 06:30 PM IST"` in the requesting
  user's timezone — JWT internals (`exp`/`iat`) and audit-log date-range *filter* inputs are
  left as raw UTC `datetime` since they aren't display fields.
- **Frontend** — the shared data table's `'datetime'` column type renders these strings
  verbatim (no `DatePipe`, which can't parse a pre-formatted string); `'date'` columns
  remain for genuine date-only fields (`license_expiry`, `pickup_date`, etc.).

---

## Development Phases

### Phase 1: Multi-Tenant Architecture + Auth + RBAC ✅

- Multi-tenant database architecture with row-level tenant isolation (`tenant_id` on every operational table)
- JWT-based authentication (access + refresh tokens, 15-min / 7-day TTL, token rotation)
- Role-Based Access Control (6 roles: SuperAdmin, TenantAdmin, TransportAdmin, Accounts, Client, Driver)
- Account lockout after 5 failed attempts (15-minute lock)
- Comprehensive audit logging for all sensitive operations

### Phase 2: Master Data Management ✅

- **Trucks**: owned/contract/leased fleet with type, capacity, availability, status tracking; extended ownership fields
- **Drivers**: license tracking, availability management, emergency contacts, blacklist support, GPS coordinates, qualified truck mapping (M2M via `driver_trucks`)
- **Clients**: company profiles, GST validation, client type, billing address, contract rates
- **Documents**: entity-agnostic storage (trucks, drivers, clients) with expiry tracking and auto-status

Business rules: soft delete everywhere, duplicate registration/license/email blocked per tenant, document expiry auto-manages status.

### Phase 3: Load Booking Engine ✅

- Unique Load ID generation (`LD-YYYY-NNNNNN`)
- Booking status workflow with validated state machine
- Full status history audit trail
- Duplicate booking prevention; IN_TRANSIT cancellation requires TenantAdmin

**Status Machine:**
```
DRAFT → CONFIRMED → ALLOCATED → IN_TRANSIT → DELIVERED
  ↓         ↓           ↓            ↓
        ──────────→ CANCELLED ←───────────
```

### Phase 4: Allocation Engine ✅

- Truck/driver assignment to confirmed loads
- Conflict detection — no overlapping assignments for same truck or driver
- Availability validation at assignment time
- Full history audit trail via `load_allocations` table

### Phase 5: UI Foundation ✅

- Angular 21 standalone architecture with Angular Material
- Light/dark mode with persistence, multi-language runtime switching
- HTTP interceptor layer, global error handling, lazy-loaded feature modules

### Phase 6: Auth + RBAC UI ✅

- Login screen, JWT access + refresh handling, silent token refresh via interceptor
- Role-based sidebar via `PermissionService`, route guards, `*appHasRole` directive

### Phase 7: Master Modules UI ✅

- Trucks, Drivers, Clients, Documents management with server-side data tables and dialog forms

### Phase 8: Role-Based UI & Access Management ✅

- SuperAdmin: Tenant management; TenantAdmin/TransportAdmin: User management
- Client: "My Bookings" + booking form; Driver: "My Tasks" + Start Trip
- Admin Load Board: Approve, Allocate, Cancel loads

### Phase 9: Reports & Analytics Dashboard ✅ COMPLETED

- KPI cards: total loads, active trips, revenue, available trucks/drivers
- Load volume over time (daily/weekly/monthly), date-range filtering
- Revenue report per client (freight collected vs outstanding balance)
- Driver performance (trips completed, on-time delivery rate)
- Truck utilization breakdown

### Phase 10: Invoice & Payment Module ✅ COMPLETED

- Auto-generate draft invoice when a load reaches DELIVERED status
- Invoice lifecycle: `draft → sent → paid / partial / overdue`
- Record partial and full payments with reference numbers
- PDF invoice generation and download
- Overdue invoice alerting — auto-detected on invoice list/refresh, surfaced in Reports KPIs

### Phase 11: Customer (Client) Portal ✅ COMPLETED

- Separate read-only portal at `/portal/*` for CLIENT-role users, gated by `roleGuard`
- `Client.user_id` links a login account to its client/company record (set via "Linked
  Client" dropdown on the user form); `/portal/*` resolves the caller's client via this link
- **Multi-carrier shippers**: a single portal login can be linked to a separate `Client`
  record in more than one tenant (one relationship per carrier). A TenantAdmin links an
  *existing* shipper account to one of their own `Client` records via "Link Portal
  Account" (by email) on the Client form — the reverse direction of the "Linked Client"
  dropdown. `/portal/me` lists every linked carrier; `/portal/loads` aggregates shipments
  across all of them (each tagged with `carrier_name`); new bookings (`POST /portal/loads`)
  pick which carrier (`tenant_id`) to book with.
- Clients track their own shipments ("My Shipments"), view full load status timeline
- **My Invoices**: `/portal/invoices` aggregates invoices across every linked carrier
  (status filter, paid/outstanding amounts, PDF download) — same multi-carrier
  aggregation pattern as `/portal/loads`
- Proof of Delivery: admins upload PODs (and other documents) on DELIVERED loads from the
  Load Board; clients view/download them from the shipment detail page
- Admin Load Board "My Bookings" flow removed — booking now happens entirely via the portal
- Per-tenant white-label branding (Phase 12) and 2FA (Phase 13) remain recommended before
  external go-live, but are not blockers for internal/staging use

### Phase 12: White-Label / Per-Tenant Branding 🔜 PLANNED

- Per-tenant: logo, primary colour, accent colour, favicon, custom domain
- Public branding endpoint — loaded before login for white-labelled portals
- Angular Material dynamic theme via CSS custom properties at runtime

### Phase 13: Two-Factor Authentication (TOTP) 🔜 PLANNED

- TOTP-based 2FA for all admin users (compatible with Google Authenticator, Authy)
- Two-step login: password → 6-digit code via short-lived temp token
- Setup flow with QR code in user profile settings; disable with current code

### Phase 14: Flutter Driver Mobile App 🟡 IN PROGRESS

- **Platforms**: Android (Play Store) + iOS (App Store), single Flutter codebase
  (native build tooling — Gradle / Xcode, or Codemagic/Fastlane CI)
- **UI shell ✅ done** (`apps/driver-mobile/`): Material 3, light + dark theme
  (toggle on Profile, persisted), Inter typography, all 10 screens from
  `mobile_app_design.md` (login, dashboard, my trips, active-trip map, trip
  details, proof of delivery, notifications, profile, vehicle info, documents)
- **First-launch onboarding ✅ done**: choose a UI language (English/Hindi/Tamil,
  fully localized) and whether you're a **Driver** or a **Client** — persisted,
  changeable later from Profile → Settings
- **Driver real-data wiring ✅ done**:
  - **My Trips / Trip Details / Dashboard** are backed by `GET /loads` (Driver
    role auto-scoped to the caller's allocated loads), including the shipper's
    company name (`LoadResponse.client_name`)
  - **Start Trip** (`POST /loads/{id}/start-trip`, ALLOCATED → IN_TRANSIT) and
    **Mark Delivered** (`POST /loads/{id}/deliver`, IN_TRANSIT → DELIVERED,
    auto-creates the draft invoice)
  - **Checkpoints** ("Reached Pickup" on the Active Trip Map, "Loaded"/"Reached
    Destination" on Trip Details) via `POST /loads/{id}/checkpoints` — recorded
    as `LoadHistory` entries and shown on the Timeline tab alongside real status
    transitions
  - **Proof of Delivery**: photo capture **and** a drawn signature (`signature`
    package, exported to PNG) both upload to `POST /loads/{id}/documents/pod`
    (same image-storage pattern as the Client Portal's document uploads below) —
    photo required, signature optional; submitting records a "Delivered to ..."
    checkpoint and marks the trip delivered. Both are viewable full-screen from
    the Documents tab.
  - **Documents tab** is real: Vehicle/Driver tabs list metadata from
    `GET /trucks/{id}/documents` / `GET /drivers/{id}/documents` (now
    Driver-permitted for their own truck/record); Trip tab aggregates POD
    photos/signatures across the driver's 5 most recent trips
  - **GPS location polling** (Phase 15 MVP): while a trip is IN_TRANSIT, the
    Active Trip Map screen calls `PATCH /drivers/{id}/location` every 30s via
    `geolocator` and shows "Sharing live location" — fails silently if location
    services/permissions are unavailable
  - **Notifications feed**: a lightweight "Recent Activity" list derived from
    each trip's `LoadHistory` (no backend notification model needed yet) — New
    Trip Assigned / Trip Started / Trip Completed / Trip Cancelled / checkpoints;
    the bottom-nav badge counts newly-allocated trips
- **Client Portal ✅ done**: picking "Client" during onboarding leads to a
  4-tab shell (Home/Shipments/Invoices/Profile) backed by `/portal/*` —
  dashboard summary, shipment list/detail with status timeline + document
  viewer/uploads, editable/cancellable DRAFT-CONFIRMED bookings, invoice list
  with payment history and PDF download, multi-carrier filtering
- **Remaining**: real push notifications (`firebase_messaging`/FCM — device-token
  registration + dispatch hooks, no backend model yet), background GPS (the
  polling above only runs while the Active Trip Map screen is open), 2FA/OTP
  login step, and the Active Trip Map's live route/tiles (Phase 15 — the GPS
  data is now being sent, but nothing broadcasts/consumes it on the admin side
  yet)

### Phase 15: Real-Time GPS Tracking 🔜 PLANNED

- WebSocket endpoint for live driver location broadcasts (tenant-scoped)
- Driver mobile app (Phase 14) pushes GPS coordinates every 30s during active trips
- Admin live map (Leaflet.js) showing all active trucks with driver + load info
- Marker click → load details side panel

---

## Recent Platform Improvements

Cross-cutting work that doesn't map to a single phase number:

- **SuperAdmin tenant filter**: a searchable "Filter by Tenant" dropdown
  (`apps/admin-frontend/.../shared/components/tenant-filter`) is now available to
  SuperAdmin on the **Users, Audit Logs, Loads, Clients, Drivers, Trucks, and
  Invoices** list pages — each backed by an optional `tenant_id` query param on the
  corresponding `GET` list endpoint, plus a "Tenant" column showing which tenant each
  row belongs to. TenantAdmin views are unaffected (still scoped to their own tenant).
- **Profile pictures / logos**: Users, Trucks, Clients, and Tenants can each have a
  profile picture or logo, uploaded with a crop & zoom step
  (`ngx-image-cropper`) before saving. Images are stored on local disk
  (`UPLOAD_DIR/avatars/<entity>/<uuid>.<ext>`) and served via authenticated
  `GET /{resource}/{id}/avatar` endpoints (`POST`/`DELETE` to upload/remove) — list
  pages show a small circular thumbnail, edit forms show a larger preview with
  Upload/Remove controls. See [Security Considerations](#security-considerations).
- **Admin Load Board**: search (load #/origin/destination), status/client/pickup-date
  filters, and pagination — previously a flat unfiltered list of the first 50 loads
- **Forgot / Reset Password**: `POST /auth/forgot-password` + `/auth/reset-password`
  (single-use, 1h-expiry tokens; resetting revokes all sessions). No email service yet —
  see [Security Considerations](#security-considerations)
- **Audit Log viewer**: SuperAdmin/TenantAdmin nav item — filter by category/event
  type/date range, "View Details" dialog with old/new value diffs and `user_email`
- **`make seed-demo`**: seeds a demo tenant + the 5 documented [Seed Accounts](#seed-accounts)
  (previously only `make seed`'s SuperAdmin existed)
- **SuperAdmin login fix**: `admin@system.local` now logs in (`UserEmail` lenient
  validator instead of `pydantic.EmailStr`, which rejected `.local`)
- **Phase 14 Flutter UI shell**: see Phase 14 above and `mobile_app_design.md`

---

## Project Status

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | ✅ **COMPLETED** | Multi-Tenant + Auth + RBAC |
| Phase 2 | ✅ **COMPLETED** | Master Data Management |
| Phase 3 | ✅ **COMPLETED** | Load Booking Engine |
| Phase 4 | ✅ **COMPLETED** | Allocation Engine |
| Phase 5 | ✅ **COMPLETED** | UI Foundation |
| Phase 6 | ✅ **COMPLETED** | Auth + RBAC UI |
| Phase 7 | ✅ **COMPLETED** | Master Modules UI |
| Phase 8 | ✅ **COMPLETED** | Role-Based UI & Access Management |
| Infra | ✅ **COMPLETED** | Docker Compose + GitHub Actions CI |
| Phase 9 | ✅ **COMPLETED** | Reports & Analytics Dashboard |
| Phase 10 | ✅ **COMPLETED** | Invoice & Payment Module |
| Phase 11 | ✅ **COMPLETED** | Customer (Client) Portal |
| Phase 12 | 🔜 **NEXT** | White-Label / Per-Tenant Branding |
| Phase 13 | 🔜 **PLANNED** | Two-Factor Authentication (TOTP) |
| Phase 14 | 🟡 **IN PROGRESS** | Flutter Driver App + Client Portal — Android + iOS (real-data wiring done; map SDK, push, 2FA remain) |
| Phase 15 | 🔜 **PLANNED** | Real-Time GPS Tracking (WebSocket + Live Map) |

---

## Seed Accounts

`make seed` (`docker-seed`) only creates the **SuperAdmin** (`admin@system.local` /
`DevPassword123!` — see `apps/backend/.env`), which has no tenant and is meant for
tenant administration, not day-to-day demo use.

To get a "Demo Transport Co" tenant with the accounts below (plus a few sample
trucks/drivers/clients), run **`make seed-demo`** (`docker-seed-demo`). It's safe to
re-run — every entity is looked up before creation.

> Password for all demo accounts: `password123`

| Email | Role | Capabilities |
|-------|------|-------------|
| `admin@demo.transport.com` | TenantAdmin | Full system CRUD |
| `transport@demo.transport.com` | TransportAdmin | Standard master data CRUD |
| `accounts@demo.transport.com` | Accounts | Clients & Loads only |
| `client@demo.transport.com` | Client | Own loads only (linked to "Acme Industries Pvt Ltd") |
| `driver@demo.transport.com` | Driver | Own tasks only (linked to driver "Rajesh Kumar") |

---

## Security Considerations

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with short expiry and rotation; refresh tokens persisted in DB
- Tenant isolation enforced at repository level
- Audit trail for all write operations — viewable in-app via the **Audit Log**
  page (SuperAdmin/TenantAdmin), `GET /audit-logs`
- Account lockout after 5 failed login attempts
- Soft delete for data retention compliance — no hard deletes
- **Forgot/reset password** (`POST /auth/forgot-password` / `/auth/reset-password`):
  single-use, 1-hour-expiry tokens (`password_reset_tokens` table); resetting
  revokes all of the user's refresh tokens. No email service is wired up yet — when
  `DEBUG=true`, `/auth/forgot-password` returns the raw `reset_token` directly in
  the response (and the portal/login UI surfaces a "Continue to Reset Password"
  link) so the flow works end-to-end in dev/demo. Replace this with a real email
  send before any external deployment.
- **Profile picture / logo uploads**: validated server-side (`image/jpeg|png|webp`,
  ≤`MAX_AVATAR_SIZE_MB`, Pillow-verified) and stored on local disk under `UPLOAD_DIR`
  with randomized filenames (`avatar_path`, never exposed to the client). Retrieved
  only via authenticated `GET /{resource}/{id}/avatar`, which applies the same
  tenant-isolation / role checks as the resource's other endpoints — the frontend
  fetches them through `HttpClient` (auth interceptor) and renders `blob:` object
  URLs rather than plain `<img src>`.

---

## License

Proprietary — All rights reserved.
