# Mobile App Design Reference
## Transport & Load Management System — Driver App

> **Tech stack: Flutter, single codebase targeting Android (Play Store) and iOS
> (App Store).** `README.md`/`CLAUDE.md` are now corrected to say Flutter
> (previously stale "React Native + Expo").

## ✅ Implementation Status

The **UI shell is built** at `apps/driver-mobile/` — all 10 screens below,
light + dark theme (Material 3, Inter font, toggle on Profile, persisted),
Riverpod + GoRouter. See `apps/driver-mobile/README.md` for how to run it
(`flutter run -d chrome`/`-d windows` for a quick preview).

**Diverged from this doc during review** (kept here for traceability):
- **Dashboard**: the top app bar's hamburger menu (no drawer to open) and
  notification bell (duplicates the bottom-nav Notifications tab) were
  **removed**. The bottom-nav Notifications icon now carries a badge (count of
  newly-allocated trips) instead — single indicator, no redundancy.

**Real API wiring is done** for the Driver role — gaps #1, #2, #4, #5, #6 below
are all closed, and #9 has its MVP (location polling) in place. Dashboard, My
Trips, Trip Details, Proof of Delivery (photo + signature), and Documents are
all backed by real `/loads`/`/drivers`/`/trucks` endpoints; only `MockData`
fallbacks remain for a driver with zero allocated trips (so the screens stay
meaningful when empty).

**First-launch onboarding** (language + Driver/Client mode) is also done, and
picking "Client" leads to a full Client Portal (`/portal/*`) — see
`apps/driver-mobile/README.md`.

**Still not done**: real map SDK/tiles (Active Trip Map's route is still a
stylized placeholder — the GPS coordinates are now being *sent* via #9's MVP,
but nothing renders them on a real map yet), push notifications (#7 — only a
derived in-app feed exists), 2FA (#8), forgot-password email delivery (#10).

### Design Style
- Material 3
- Dark map background
- White elevated cards
- Orange primary action color (#F5A623)
- Large touch targets
- Mobile-first logistics workflow

---

## ⚠️ Backend Readiness — Gaps to Close Before Build

The backend (`apps/backend`) is built around the **admin/web** roles
(SuperAdmin/TenantAdmin/TransportAdmin/Accounts/Client) plus a minimal `Driver`
role. This table was originally written when the `Driver` role was
**read-almost-nothing, write-almost-nothing**. Gaps #1/#2/#4/#5/#6 are now
**closed**, and #3/#9 have working MVPs — kept here for traceability and
because #7/#8/#10 remain open.

| # | Gap | Status |
|---|-----|--------|
| 1 | **Driver can't mark a load `DELIVERED`** | ✅ **Done** — `POST /loads/{id}/deliver` (Driver-permitted, IN_TRANSIT→DELIVERED, mirrors `start-trip`, auto-creates the draft invoice). |
| 2 | **Driver can't upload POD** | ✅ **Done** — `POST /loads/{id}/documents/pod` (multipart, Driver-permitted, scoped to the driver's own allocated load, `document_type=pod`). |
| 3 | **No binary file upload / cloud storage** | ✅ **Done for app uploads** (local disk, not S3/cloud) — `app/core/avatar_storage.py`'s `save_avatar()`/`read_avatar()`/`has_file` pattern (originally built for avatars/truck photos) is now reused for POD photos+signatures (`/loads/{id}/documents/pod` + `/loads/{id}/documents/{id}/file`) and Client Portal document uploads (`/portal/loads/{id}/documents`). Migrating to S3/GCS/Cloudinary remains a future infra task if needed, but the app no longer needs it to function. |
| 4 | **Driver can't view their own profile** | ✅ **Done** — `GET /drivers/me`, plus `Driver` allowed on `GET /drivers/{own_id}/documents` and `GET /trucks/{assigned_truck_id}/documents`. |
| 5 | **Trip list/detail has no client name** | ✅ **Done** — `LoadResponse.client_name` (populated in `_to_response`, `app/api/v1/loads.py`), flows through to `/loads/*` and `/portal/loads/*`. |
| 6 | **No granular trip checkpoints** | ✅ **Done** — `POST /loads/{id}/checkpoints` (`LoadService.add_checkpoint`) appends a `LoadHistory` row with `from_status == to_status` (no state-machine change); "Reached Pickup"/"Loaded"/"Reached Destination" are real timeline entries, rendered distinctly from status transitions in both the driver and Client Portal timelines. |
| 7 | **No push notifications** | 🟡 **Partial** — a lightweight in-app "Recent Activity" feed (`notifications_screen.dart`) derives from `GET /loads` + `GET /loads/{id}/history`, no backend changes. Real FCM push (device-token registration + dispatch hooks on allocate/cancel) is still open — same root cause as the "no email service" gap (#10). |
| 8 | **2FA / OTP is Phase 13, not built** | ❌ Open — login screens (web + mobile) still have placeholder OTP steps; JWT login/refresh works today without it. |
| 9 | **Live GPS tracking is single-point, not continuous** | 🟡 **Partial (MVP done)** — the Active Trip Map screen now calls `PATCH /drivers/{id}/location` every 30s via `geolocator` while a trip is IN_TRANSIT (fails silently if location services/permissions are unavailable). The *admin* side (WebSocket broadcast + live map showing other trucks) is still Phase 15. |
| 10 | **Forgot-password has no real delivery on mobile** | ❌ Open — `/auth/forgot-password` still only returns `reset_token` when `DEBUG=true`; no email/SMS service exists. |

---

## Reference Screens

### 1. Login
Purpose: Driver authentication (+ 2FA, when Phase 13 ships).

Components:
- Logo
- Email/Phone
- Password
- Login Button
- Forgot Password
- OTP Verification *(Phase 13 — not yet built; omit from v1)*

**API**: `POST /auth/login` ✅, `POST /auth/refresh` ✅, `POST /auth/logout` ✅.
"Forgot Password" → see gap #10 (route to dispatcher for v1).

---

### 2. Dashboard
Purpose: Daily overview.

> No app bar chrome — the original mockup's hamburger menu (no drawer to open)
> and notification bell (duplicates the bottom-nav Notifications tab, which
> now carries the unread badge) were dropped during implementation.

Sections:
- Greeting (from `GET /users/me` ✅)
- KPI Cards (Assigned, Active, Completed) — derive client-side by calling
  `GET /loads?status=allocated|in_transit|delivered` ✅ and counting; no
  dedicated "driver summary" endpoint exists yet (optional future addition,
  mirrors `GET /reports/summary` but driver-scoped)
- Active Trip Card — first `in_transit` (or `allocated`) load
- Upcoming Trips — `allocated` loads sorted by `pickup_date`

---

### 3. My Trips
Tabs map directly to `LoadStatus` filters on `GET /loads?status=...` ✅:

| Tab | `status` filter |
|-----|------------------|
| Assigned | `allocated` |
| Active | `in_transit` |
| Completed | `delivered` |
| Cancelled | `cancelled` |

Trip Card:
- Load ID → `load_no` ✅
- Client → `client_name` ✅ (gap #5, done)
- Pickup → `origin` / `pickup_date` ✅
- Destination → `destination` ✅
- Date → `pickup_date` ✅
- Status → `status` ✅ (lowercase: `draft|confirmed|allocated|in_transit|delivered|cancelled`)

---

### 4. Active Trip Map
Full-screen map with:
- Driver GPS location — `PATCH /drivers/{id}/location` ✅ sent every 30s while
  IN_TRANSIT (gap #9 MVP, done). The map itself is still a stylized
  `CustomPaint` placeholder — nothing on the *admin* side consumes this yet
  (full Phase 15).
- Route polyline — client-side (e.g. Google Directions API), not backend —
  still a placeholder
- Destination marker — from `destination` (geocode client-side; no lat/lon stored on `Load`)
- Floating trip card — same fields as My Trips card

Actions (matching the real state machine):
- **Start Trip** → `POST /loads/{id}/start-trip` ✅ (ALLOCATED→IN_TRANSIT)
- **Reached Pickup** (this screen) / **Loaded** / **Reached Destination** (Trip
  Details Overview) → ✅ gap #6, done — `POST /loads/{id}/checkpoints`,
  informational `LoadHistory` entries (no status change)
- **Mark Delivered** (Trip Details → Proof of Delivery) →
  `POST /loads/{id}/deliver` ✅ gap #1, done (IN_TRANSIT→DELIVERED)

---

### 5. Trip Details
Header:
- Load ID → `load_no` ✅
- Truck → driver's `current_truck` from `GET /drivers/me` ✅ (registration_no +
  make/model — `LoadResponse` itself still doesn't carry truck info, but the
  driver's own assigned truck covers the common case)
- Driver → self (from `/drivers/me`) ✅ gap #4, done
- Status → `status` ✅

Sections:
- Timeline → `GET /loads/{id}/history` ✅ (Driver-permitted; same shape as the
  Client Portal's "Status Timeline"; checkpoints render distinctly from real
  status transitions)
- Pickup Address → `origin` ✅ (tappable → opens in Maps)
- Delivery Address → `destination` ✅ (tappable → opens in Maps)
- Client → `client_name` ✅ gap #5, done
- Weight → `weight_kg` ✅
- Documents → `GET /loads/{id}/documents` ✅ now Driver-permitted (gap #2/#4),
  same ownership check as `get_load`

---

### 6. POD Upload (Proof of Delivery)
Fields:
- Delivery Photo
- Signature
- Receiver Name
- Remarks

Actions — ✅ **all done** (gaps #1/#2/#3 closed):
- Capture Photo (`image_picker`, gallery) → uploaded via
  `POST /loads/{id}/documents/pod` (multipart, `document_type=pod`)
- Capture Signature (`signature` package canvas) → exported to PNG, uploaded
  via the same endpoint as a second POD document (optional)
- Submit Delivery → records a "Delivered to {receiver}: {remarks}" checkpoint
  (`POST /loads/{id}/checkpoints`) then `POST /loads/{id}/deliver`
  (IN_TRANSIT→DELIVERED)

Both the photo and signature are viewable full-screen from the Documents tab
(`GET /loads/{id}/documents/{id}/file`).

---

### 7. Notifications
**Status**: 🟡 gap #7 partial — no backend notification model/push exists, but
the screen now shows a real **"Recent Activity"** feed: for each of the
driver's 5 most-recent trips, the latest `GET /loads/{id}/history` entry is
mapped to a tile (New Trip Assigned / Trip Started / Trip Completed / Trip
Cancelled / checkpoint label). The bottom-nav badge counts newly-allocated
trips. Real push (FCM) is still open.

---

### 8. Profile
Sections — ✅ all done (gap #4):
- Driver Info → `GET /drivers/me`
- License → `Driver.license_no/license_class/license_expiry` (same endpoint)
- Emergency Contact → `Driver.emergency_contact_name/emergency_contact_phone` (same endpoint)
- Assigned Vehicle → `current_truck` (same endpoint)

---

## Documentation Fix — Done

`README.md` Phase 14 and `CLAUDE.md`'s Stack table previously said **React
Native + Expo** for `apps/driver-mobile/`, contradicting this doc's Flutter
architecture. Both now say **Flutter**:

- README Phase 14 title → "Flutter Driver Mobile App", marked 🟡 IN PROGRESS
  (UI shell done, API wiring pending)
- "via Expo EAS Build" → "via Flutter's native build tooling (Gradle / Xcode,
  or Codemagic/Fastlane CI)"
- "Expo Push API" → **`firebase_messaging`** (FCM) — works for both Android and
  iOS (FCM relays to APNs under the hood), avoiding two separate push stacks
- CLAUDE.md Stack table: `apps/driver-mobile/` → "Flutter (Dart), Riverpod + GoRouter"

---

## Flutter Architecture

```
lib/
  core/
    network/      # ApiClient (Dio + auth interceptor), TokenStorage
    providers/     # Riverpod providers (auth, trip, profile, portal, notification, locale, theme)
    onboarding/     # first-launch language/role prefs
    router/         # GoRouter (driver shell + client-portal shell)
    theme/
  features/
    auth/
    dashboard/
    trips/          # My Trips, Trip Details, Active Trip Map, Proof of Delivery
    notifications/
    profile/        # Profile, Vehicle Info, Documents
    onboarding/
    portal/         # Client Portal (AppMode.client) — shipments, invoices, dashboard
    trucks/
  shared/
    models/
    widgets/
    utils/
```

As actually built (vs. the original "Recommended" list):
- **Riverpod** ✅ — `FutureProvider`/`FutureProvider.family` for all server
  data, `ConsumerWidget`/`ConsumerStatefulWidget` throughout
- **GoRouter** ✅ — `StatefulShellRoute` per `AppMode` (driver vs. client),
  `redirect` gates on onboarding/session/mode
- **Dio** ✅ — `ApiClient` (`core/network/api_client.dart`) attaches
  `Authorization: Bearer`, handles 401 → `/auth/refresh` → retry once
- **Plain Dart model classes with `fromJson`/`copyWith`** — used instead of
  Freezed (no code-gen step); field names mirror backend schemas
  (`load_no`, `pickup_date`, `client_name`, etc.), with a shared `_decimal()`
  helper since Pydantic serializes `Decimal` fields as JSON strings
- **flutter_secure_storage** ✅ — access/refresh tokens
- **geolocator** ✅ — periodic `PATCH /drivers/{id}/location` while IN_TRANSIT
  (gap #9 MVP)
- **image_picker** + **signature** package ✅ — POD photo + signature capture,
  uploaded via `app/core/avatar_storage.py`'s local-disk pattern (gap #3/#6)
- **path_provider** / **share_plus** / **url_launcher** — invoice PDF
  download/share (Client Portal), signature PNG export, "open in Maps"
- **firebase_messaging** + **flutter_local_notifications** — still **not**
  added; real push (gap #7) remains future work
