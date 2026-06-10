# Transport & Load Management System

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
│  │   Angular   │  │ React Native│  │   Cloud Document        │ │
│  │   Admin     │  │  (Expo) App │  │   Storage (planned)     │ │
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
| **Mobile Apps** | React Native with Expo (Android & iOS) |
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
│   └── driver-mobile/              # React Native Driver App (planned — Phase 15)
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
| Auth (login, refresh, logout) | 6 | ✅ Pass |
| Trucks (CRUD, activate/deactivate, filters) | 12 | ✅ Pass |
| Drivers (CRUD, availability toggle, location) | 9 | ✅ Pass |
| Clients (CRUD, GST validation, search) | 9 | ✅ Pass |
| Documents (create, expiry status, list, delete) | 8 | ✅ Pass |
| Loads (CRUD, state machine, history, Load ID) | 18 | ✅ Pass |
| Allocations (assign, swap, conflict check) | 12 | ✅ Pass |

---

## CI/CD

GitHub Actions runs automatically on push and pull requests to `main`/`develop`:

| Job | Steps |
|-----|-------|
| **Backend** | ruff lint → pytest (with real PostgreSQL service) |
| **Frontend** | npm ci → ng build (production) |

Pipeline config: `.github/workflows/ci.yml`

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

### Phase 10: Invoice & Payment Module 🔜 NEXT

- Auto-generate draft invoice when a load reaches DELIVERED status
- Invoice lifecycle: `draft → sent → paid / partial / overdue`
- Record partial and full payments with reference numbers
- PDF invoice generation and download
- Overdue invoice alerting

### Phase 11: Customer (Client) Portal 🔜 PLANNED

- Separate read-only portal at `/portal/*` for CLIENT-role users
- Clients track their own shipments, view load status timeline, download PODs
- Per-tenant white-label branding applied (Phase 12 prerequisite)
- Requires 2FA to be in place before go-live (Phase 13 prerequisite)

### Phase 12: White-Label / Per-Tenant Branding 🔜 PLANNED

- Per-tenant: logo, primary colour, accent colour, favicon, custom domain
- Public branding endpoint — loaded before login for white-labelled portals
- Angular Material dynamic theme via CSS custom properties at runtime

### Phase 13: Two-Factor Authentication (TOTP) 🔜 PLANNED

- TOTP-based 2FA for all admin users (compatible with Google Authenticator, Authy)
- Two-step login: password → 6-digit code via short-lived temp token
- Setup flow with QR code in user profile settings; disable with current code

### Phase 14: React Native Driver Mobile App 🔜 PLANNED

- **Platforms**: Android (Play Store) + iOS (App Store) via Expo EAS Build
- **Native push notifications**: FCM (Android) + APNs (iOS) via Expo Push API
- **Background GPS**: foreground service (Android) + UIBackgroundModes (iOS)
- Screens: login (with 2FA), trip list, trip detail, status update, POD photo capture, profile
- Triggers: push on new assignment, 1h pickup reminder, cancellation alert

### Phase 15: Real-Time GPS Tracking 🔜 PLANNED

- WebSocket endpoint for live driver location broadcasts (tenant-scoped)
- Driver mobile app (Phase 14) pushes GPS coordinates every 30s during active trips
- Admin live map (Leaflet.js) showing all active trucks with driver + load info
- Marker click → load details side panel

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
| Phase 10 | 🔜 **NEXT** | Invoice & Payment Module |
| Phase 11 | 🔜 **PLANNED** | Customer (Client) Portal |
| Phase 12 | 🔜 **PLANNED** | White-Label / Per-Tenant Branding |
| Phase 13 | 🔜 **PLANNED** | Two-Factor Authentication (TOTP) |
| Phase 14 | 🔜 **PLANNED** | React Native Driver App — Android + iOS |
| Phase 15 | 🔜 **PLANNED** | Real-Time GPS Tracking (WebSocket + Live Map) |

---

## Seed Accounts

> Password for all accounts: `password123`

| Email | Role | Capabilities |
|-------|------|-------------|
| `admin@demo.transport.com` | TenantAdmin | Full system CRUD |
| `transport@demo.transport.com` | TransportAdmin | Standard master data CRUD |
| `accounts@demo.transport.com` | Accounts | Clients & Loads only |
| `client@demo.transport.com` | Client | Own loads only |
| `driver@demo.transport.com` | Driver | Own tasks only |

---

## Security Considerations

- Passwords hashed with bcrypt (cost factor 12)
- JWT tokens with short expiry and rotation; refresh tokens persisted in DB
- Tenant isolation enforced at repository level
- Audit trail for all write operations
- Account lockout after 5 failed login attempts
- Soft delete for data retention compliance — no hard deletes

---

## License

Proprietary — All rights reserved.
