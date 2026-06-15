# TransTrack Mobile App (Flutter)

Single Flutter codebase targeting Android and iOS (web/desktop also enabled
for quick preview/testing), built from `mobile_app_design.md`'s 10-screen
reference. Now wired to the real backend (`apps/backend`) — see
[What's here](#whats-here) below.

## Run

Requires the backend running (`make dev` from the repo root, or
`docker compose up --build`).

```bash
cd apps/driver-mobile
flutter pub get

# Android emulator (10.0.2.2 reaches the host's localhost — the default):
flutter run

# Web / Windows / macOS / Linux desktop — point at the host backend directly:
flutter run -d chrome  --dart-define=API_BASE_URL=http://localhost:8000/api/v1
flutter run -d windows --dart-define=API_BASE_URL=http://localhost:8000/api/v1

# Physical device on the same network as the backend — use the host's LAN IP:
flutter run --dart-define=API_BASE_URL=http://<host-ip>:8000/api/v1
```

`flutter test` runs the widget tests (`test/widget_test.dart`,
`test/trips_screen_test.dart`) — these don't need a backend (Dio is replaced
with a `FakeTripRepository` via Riverpod overrides).

### Try it with the seeded demo accounts
After `make seed-demo` (password for all: `password123`):

| Email | Onboarding role to pick | What you get |
|-------|--------------------------|---------------|
| `driver@demo.transport.com` | Driver | Real allocated/in-transit/delivered trips for "Rajesh Kumar" |
| `client@demo.transport.com` | Client | Client Portal for "Acme Industries Pvt Ltd" |

## What's here

### First launch — Onboarding
- **Language**: English / Hindi (हिन्दी) / Tamil (தமிழ்) — fully localized,
  changeable later from Profile → Settings
- **Driver or Client**: persisted (`shared_preferences`), determines which app
  shell + router branch you land in. `lib/core/onboarding/onboarding_prefs.dart`,
  `lib/core/providers/app_mode_provider.dart`.

### Driver mode (`AppMode.driver`) — Home/Trips/Map/Notifications/Profile
- **Design system** (`lib/core/theme/`): light + dark `ThemeData`, Material 3,
  Inter typography, orange `#F5A623` brand accent — toggle from Profile.
- **My Trips / Dashboard / Trip Details** — real data from `GET /loads`
  (Driver role auto-scoped to the caller's allocated loads), including the
  shipper's name (`LoadResponse.client_name`). Falls back to `MockData` only
  when the driver has zero allocated trips, so the screens stay meaningful
  when empty.
- **Start Trip** / **checkpoints** ("Reached Pickup"/"Loaded"/"Reached
  Destination") / **Mark Delivered** — `POST /loads/{id}/start-trip`,
  `POST /loads/{id}/checkpoints`, `POST /loads/{id}/deliver`. Checkpoints show
  up on the Timeline tab alongside real status transitions.
- **Proof of Delivery** — photo capture (`image_picker`) + drawn signature
  (`signature` package, exported to PNG), both uploaded via
  `POST /loads/{id}/documents/pod`; submitting records a "Delivered to ..."
  checkpoint and marks the trip delivered.
- **Documents tab** — Vehicle/Driver tabs list real metadata from
  `GET /trucks/{id}/documents` / `GET /drivers/{id}/documents`; Trip tab
  aggregates POD photos/signatures across the 5 most recent trips, tap to view
  full-screen (`shared/widgets/document_image_dialog.dart`).
- **Active Trip Map** — still a `CustomPainter` placeholder (no map SDK), but
  while a trip is IN_TRANSIT it polls `PATCH /drivers/{id}/location` every 30s
  via `geolocator` (Phase 15 MVP) and shows "Sharing live location".
- **Notifications** — "Recent Activity" feed derived from each trip's latest
  `GET /loads/{id}/history` entry (no backend notification model needed);
  bottom-nav badge counts newly-allocated trips.
- **Profile / Vehicle Information** — `GET /drivers/me` (license, emergency
  contact, assigned truck + photo gallery), profile picture upload, preferred
  language.

### Client mode (`AppMode.client`) — Home/Shipments/Invoices/Profile
Backed by `/portal/*` (role `Client`, scoped via `Client.user_id`):
- **Home**: company name, shipment-status summary, total outstanding, recent
  shipments
- **Shipments**: status/carrier-filtered list, detail with status timeline +
  document viewer/uploads, edit/cancel DRAFT-CONFIRMED bookings, new booking form
- **Invoices**: status-filtered list, detail with payment history + PDF
  download (`share_plus`)
- **Profile**: linked company/carrier details, language + theme, logout

### Shared infrastructure
- **Riverpod** (`core/providers/`) — `FutureProvider`/`.family` for all server
  data; `ApiClient` (`core/network/`, Dio + JWT refresh interceptor) is shared
  across every repository.
- **GoRouter** (`core/router/app_router.dart`) — two `StatefulShellRoute`s (one
  per `AppMode`), `redirect` gates on onboarding/session/mode.
- **Models** (`shared/models/`) — plain Dart `fromJson`/`copyWith` classes
  mirroring backend schemas field-for-field (`load_no`, `client_name`, etc.);
  a shared `_decimal()` helper handles Pydantic's `Decimal`-as-JSON-string
  serialization.
- **Pull-to-refresh** (`shared/widgets/refresh_wrapper.dart`) on every list
  screen, wired to `ref.invalidate(...)` on the relevant provider.

## What's still placeholder / not done
See `mobile_app_design.md` ("Backend Readiness — Gaps to Close Before Build")
for the full gap table. In short:
- **Active Trip Map**: no real map SDK/tiles/route — GPS is now being *sent*
  (above), but nothing renders it on a map yet, and the admin side doesn't
  consume it either (full Phase 15).
- **Push notifications**: only the in-app "Recent Activity" feed exists; real
  FCM push needs a device-token endpoint + dispatch hooks (gap #7).
- **2FA/OTP** (gap #8) and **Forgot Password email delivery** (gap #10): not
  built (login routes "Forgot Password" to "contact your dispatcher" for now).
- **POD signature/photo storage** is local-disk (`avatar_storage.py`), not
  S3/cloud — fine for development, may need revisiting for production scale.
