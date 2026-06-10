# Transport & Load Management — Knowledge Graph

## System Architecture

```mermaid
graph TB
    subgraph FRONTEND["🖥️ Angular Frontend (localhost:4200)"]
        AppInit["APP_INITIALIZER\nloadProfile()"]
        AuthGuard["AuthGuard\ncheckToken()"]
        PermSvc["PermissionService\ncurrentRoles() signal"]
        HasRole["*appHasRole directive"]
        Router["Angular Router"]

        AppInit -->|populates| PermSvc
        AuthGuard -->|allows route| Router
        PermSvc -->|drives| HasRole
        HasRole -->|shows/hides| SideNav

        subgraph SideNav["Sidebar (role-aware)"]
            S1["Load Board\n(TenantAdmin, TransportAdmin)"]
            S2["My Bookings\n(Client)"]
            S3["My Tasks\n(Driver)"]
            S4["Trucks / Drivers / Clients\n(Admin)"]
            S5["Users (Admin)\nTenants (SuperAdmin)"]
        end

        subgraph LoadsMain["LoadsMainComponent"]
            AdminView["Admin Dispatch Board"]
            ClientView["Client Booking Form"]
            DriverView["Driver Task Cards"]
        end

        SideNav -->|/loads| LoadsMain
    end

    subgraph BACKEND["🐍 FastAPI Backend (localhost:8000)"]
        subgraph API["API Routers"]
            AuthR["/auth\nlogin · logout · refresh"]
            UsersR["/users\nme · CRUD"]
            LoadsR["/loads\nCRUD · transition · allocate · start-trip · cancel"]
            TrucksR["/trucks\nCRUD · activate · deactivate"]
            DriversR["/drivers\nCRUD · toggle-avail · location · docs"]
            ClientsR["/clients\nCRUD"]
            TenantsR["/tenants\nCRUD"]
            AllocR["/allocations\ntrucks/available · drivers/available"]
        end

        subgraph Services["Services"]
            AuthSvc["AuthService"]
            LoadSvc["LoadService\nstate machine"]
            AllocSvc["AllocationService\nconflict detection"]
            DriverSvc["DriverService\ntruck mapping"]
            AuditSvc["AuditService\nevery mutation"]
        end

        subgraph Models["SQLAlchemy Models"]
            Tenant["Tenant"]
            User["User"]
            Role["Role ←→ User\nuser_roles (M2M)"]
            Load["Load\nDRAFT→CONFIRMED\n→ALLOCATED→IN_TRANSIT\n→DELIVERED|CANCELLED"]
            Truck["Truck\nownership: owned|contract|leased\nstatus: ACTIVE|INACTIVE\n|IN_MAINTENANCE|DECOMMISSIONED"]
            Driver["Driver\nstatus: AVAILABLE|ON_TRIP\n|ON_LEAVE|INACTIVE|BLACKLISTED"]
            DriverTruck["driver_trucks\n(M2M association)"]
            Client["Client"]
            Document["Document\nentity_type: truck|driver"]
            Allocation["LoadAllocation\ntruck_id · driver_id"]
            AuditLog["AuditLog\nall write events"]
            RefreshTok["RefreshToken"]
        end

        subgraph DB["🐘 PostgreSQL"]
            Tables["tenants · users · roles\nloads · trucks · drivers\ndriver_trucks · clients\ndocuments · load_allocations\naudit_logs · refresh_tokens"]
        end

        AuthR --> AuthSvc
        LoadsR --> LoadSvc
        AllocR --> AllocSvc
        DriversR --> DriverSvc
        AuthSvc --> AuditSvc
        LoadSvc --> AuditSvc
        DriverSvc --> AuditSvc
        Models --> DB
    end

    FRONTEND -->|HTTP + JWT Bearer| BACKEND
    AppInit -->|GET /users/me| UsersR
```

---

## Domain Model

```mermaid
erDiagram
    TENANT ||--o{ USER : "has many"
    TENANT ||--o{ TRUCK : "owns"
    TENANT ||--o{ DRIVER : "employs"
    TENANT ||--o{ CLIENT : "serves"
    TENANT ||--o{ LOAD : "manages"

    USER }o--o{ ROLE : "user_roles"
    USER ||--o| DRIVER : "driver profile"

    DRIVER }o--o{ TRUCK : "driver_trucks (qualified)"
    DRIVER ||--o{ LOAD_ALLOCATION : "allocated to"

    TRUCK ||--o{ LOAD_ALLOCATION : "used in"

    CLIENT ||--o{ LOAD : "books"
    LOAD ||--o| LOAD_ALLOCATION : "allocated via"

    DRIVER ||--o{ DOCUMENT : "has docs"
    TRUCK  ||--o{ DOCUMENT : "has docs"

    LOAD_ALLOCATION ||--o| AUDIT_LOG : "logged"
```

---

## Load Lifecycle (State Machine)

```mermaid
stateDiagram-v2
    [*] --> DRAFT : Client submits booking
    DRAFT --> CONFIRMED : Admin approves
    DRAFT --> CANCELLED : Admin rejects
    CONFIRMED --> ALLOCATED : Admin assigns Truck + Driver
    CONFIRMED --> CANCELLED : Admin cancels
    ALLOCATED --> IN_TRANSIT : Driver clicks "Start Trip"
    ALLOCATED --> CANCELLED : TenantAdmin cancels
    IN_TRANSIT --> DELIVERED : System / Admin marks delivered
    IN_TRANSIT --> CANCELLED : TenantAdmin only
    DELIVERED --> [*]
    CANCELLED --> [*]
```

---

## Role Access Matrix

| Feature | SuperAdmin | TenantAdmin | TransportAdmin | Client | Driver |
|---|:---:|:---:|:---:|:---:|:---:|
| Create Tenant | ✅ | ❌ | ❌ | ❌ | ❌ |
| Manage Users | ❌ | ✅ | Limited | ❌ | ❌ |
| Manage Trucks | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage Drivers | ✅ | ✅ | ✅ | ❌ | ❌ |
| Manage Clients | ✅ | ✅ | ✅ | ❌ | ❌ |
| View Load Board | ✅ | ✅ | ✅ | ❌ | ❌ |
| Approve / Reject Load | ✅ | ✅ | ✅ | ❌ | ❌ |
| Allocate Truck + Driver | ✅ | ✅ | ✅ | ❌ | ❌ |
| Submit Booking | ❌ | ❌ | ❌ | ✅ | ❌ |
| View My Bookings | ❌ | ❌ | ❌ | ✅ | ❌ |
| View My Tasks | ❌ | ❌ | ❌ | ❌ | ✅ |
| Start Trip | ❌ | ❌ | ❌ | ❌ | ✅ |
| Update Own Location | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| **Row-level tenant isolation** | Every model carries `tenant_id`; all queries are scoped by it |
| **JWT + Refresh Token** | Short-lived access tokens (stored in memory); refresh tokens persisted in DB |
| **Signals for auth state** | Angular signals (`currentUser`, `isAuthenticated`) are reactive; no NgRx needed |
| **APP_INITIALIZER for profile** | `loadProfile()` runs before first render — ensures roles are populated even on hard refresh |
| **Soft delete everywhere** | `is_deleted` flag, never hard DELETE; full audit trail preserved |
| **driver_trucks M2M** | A driver qualifies for multiple trucks; one truck can have multiple qualified drivers |
| **State machine for loads** | All status transitions validated server-side; UI just reflects backend state |
| **Alembic migrations** | Every schema change is versioned; `down_revision` chain is explicit |

---

## File Structure (Key Paths)

```
apps/
├── admin-frontend/src/app/
│   ├── app.config.ts              ← APP_INITIALIZER (refresh fix)
│   ├── app.routes.ts              ← /loads, /trucks, /drivers, /users, /tenants
│   ├── core/
│   │   ├── auth/
│   │   │   ├── auth.service.ts    ← login, loadProfile, logout
│   │   │   ├── permission.service.ts  ← currentRoles(), hasAnyRole()
│   │   │   └── token.service.ts
│   │   └── guards/auth.guard.ts
│   ├── shared/
│   │   └── directives/has-role.directive.ts  ← *appHasRole
│   ├── layouts/admin-layout/      ← Sidebar with role-aware nav
│   └── features/
│       ├── loads/
│       │   ├── loads-main/        ← Single component, 3 role views
│       │   ├── allocate-dialog/   ← Admin truck+driver picker
│       │   └── services/load.service.ts
│       ├── trucks/                ← Admin CRUD
│       ├── drivers/               ← Admin CRUD
│       ├── clients/               ← Admin CRUD
│       ├── admin/
│       │   ├── tenants/           ← SuperAdmin only
│       │   └── users/             ← TenantAdmin / TransportAdmin
│       └── auth/login/
└── backend/app/
    ├── models/
    │   ├── driver.py              ← driver_trucks M2M, base_location, GPS
    │   └── truck.py               ← qualified_drivers back-ref
    ├── schemas/driver.py          ← DriverLocationUpdate, AssignedTruckBasic
    ├── services/driver_service.py ← truck mapping sync, update_location
    ├── api/v1/drivers.py          ← PATCH /drivers/{id}/location
    └── alembic/versions/
        ├── 20260312_driver_enhancements.py
        └── 20260312_truck_ownership_fields.py
```
