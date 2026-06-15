# TransTrack — Mobile App User Guide

This guide explains how to use the **TransTrack mobile app**
(`apps/driver-mobile`, built with Flutter) — for **Drivers** running
shipments, and for **Clients** (customers) tracking their bookings on the go.

> Looking for the web admin/operations portal instead? See
> [`docs/user-guide-web.md`](./user-guide-web.md).

The same app serves two very different experiences depending on which option
you choose the first time you open it — **Driver** or **Client** — described
in their own sections below.

---

## Table of Contents

1. [Getting the App Running](#1-getting-the-app-running)
2. [First Launch: Onboarding](#2-first-launch-onboarding)
3. [Signing In](#3-signing-in)
4. [Driver Mode](#4-driver-mode)
   - [4.1 Dashboard](#41-dashboard)
   - [4.2 My Trips](#42-my-trips)
   - [4.3 Trip Details](#43-trip-details)
   - [4.4 Starting a Trip & the Active Trip Map](#44-starting-a-trip--the-active-trip-map)
   - [4.5 Adding Checkpoints](#45-adding-checkpoints)
   - [4.6 Proof of Delivery & Marking Delivered](#46-proof-of-delivery--marking-delivered)
   - [4.7 Documents](#47-documents)
   - [4.8 Notifications](#48-notifications)
   - [4.9 Profile](#49-profile)
5. [Client Mode (Mobile Client Portal)](#5-client-mode-mobile-client-portal)
   - [5.1 Home](#51-home)
   - [5.2 Shipments](#52-shipments)
   - [5.3 Invoices](#53-invoices)
   - [5.4 Profile](#54-profile)
6. [Settings: Language, Theme & Logout](#6-settings-language-theme--logout)
7. [Troubleshooting & FAQ](#7-troubleshooting--faq)

---

## 1. Getting the App Running

The mobile app needs to be able to reach your company's TransTrack backend
over the network. If your IT/admin team has published the app (Play
Store/App Store/internal distribution), just install and open it as normal.

If you're running it from source for testing/demo purposes, see
[`apps/driver-mobile/README.md`](../apps/driver-mobile/README.md) for setup
instructions (`flutter run`, choosing the right `API_BASE_URL`, etc.). The
rest of this guide assumes the app is installed and can reach the backend.

---

## 2. First Launch: Onboarding

The **very first time** you open the app, you'll see a short onboarding flow:

1. **Choose your language** — English, हिन्दी (Hindi), or தமிழ் (Tamil). You
   can change this later from **Profile → Settings** (Section 6).
2. **Choose how you'll use the app**:
   - **Driver** — for drivers running shipments (trips, deliveries,
     documents).
   - **Client** — for customers tracking shipments and invoices.

Your choice is **remembered** — the app won't ask again, and it determines
which set of tabs you see at the bottom of the screen from now on (Driver
tabs vs. Client tabs, described below).

> **Changing your mind later:** the app doesn't currently have an in-app
> "switch mode" option. If you picked the wrong mode, reinstall the app (or
> clear its app data) to see the onboarding screen again.

---

## 3. Signing In

After onboarding, you'll see the **Login** screen:

1. Enter your **Email** and **Password**.
2. Tap **Login**.

You'll land on the Dashboard (Driver mode) or Home (Client mode) depending on
which mode you chose during onboarding.

> **Demo accounts** (after `make seed-demo`, password `password123` for all):
>
> | Email | Pick this onboarding mode | What you'll see |
> |-------|---------------------------|-------------------|
> | `driver@demo.transport.com` | **Driver** | Real trips for driver "Rajesh Kumar" |
> | `client@demo.transport.com` | **Client** | Client Portal for "Acme Industries Pvt Ltd" |

Your session stays signed in between app launches. If it expires, the app
will return you to the Login screen automatically.

---

## 4. Driver Mode

Driver mode has 5 tabs along the bottom: **Home**, **Trips**, **Map**,
**Notifications**, and **Profile**.

### 4.1 Dashboard

The Home tab gives you a daily overview:

- A greeting with your name.
- **KPI cards** — counts of your Assigned, Active, and Completed trips.
- **Active Trip** card — your current "in transit" (or next "allocated")
  trip, with a shortcut into its details.
- **Upcoming Trips** — your allocated trips, soonest pickup date first.

Pull down on the screen to refresh.

### 4.2 My Trips

The Trips tab is organized into **four tabs** matching trip status:

| Tab | Shows trips that are... |
|-----|---------------------------|
| **Assigned** | Allocated to you, not yet started |
| **Active** | In transit (you've started the trip) |
| **Completed** | Delivered |
| **Cancelled** | Cancelled |

Each **trip card** shows:
- Load number
- **Client name** (the customer this shipment is for)
- Pickup → Destination
- Pickup date
- Status badge

Tap any card to open **Trip Details**.

> If you have zero trips assigned yet, the screens show sample/placeholder
> data so you can see how things look — once you have real trips, those take
> over automatically.

### 4.3 Trip Details

Tapping a trip opens its full details:

- **Header** — load number, status, your truck (registration + make/model
  from your assigned vehicle).
- **Timeline** — every status change and checkpoint for this trip, in order
  (e.g. "Allocated" → "Reached Pickup" → "In Transit" → "Reached
  Destination" → "Delivered"), each with a timestamp. Checkpoints (informal
  progress notes) are shown distinctly from formal status changes.
- **Pickup Address** and **Delivery Address** — tap either to open it in your
  phone's Maps app for navigation.
- **Client**, **Weight**, and any special instructions.
- **Documents** — proof-of-delivery photos/signatures already uploaded for
  this trip (tap to view full-screen).

From here, depending on the trip's current status, you'll see action buttons
described in the next sections.

### 4.4 Starting a Trip & the Active Trip Map

When a trip is **Assigned** (allocated to you but not started):

1. Open the trip (from Home's Active Trip card, or My Trips → Assigned).
2. Tap **Start Trip**.
3. Confirm. The trip becomes **Active** (in transit).

Once a trip is **Active**, the **Map** tab shows:

- A map view centered on your route (note: the map is currently a stylized
  placeholder — turn-by-turn routing/live tiles are planned for a future
  update).
- A floating card with the trip's key details (load #, route, status).
- **Live location sharing** — while you have an active trip, the app
  periodically sends your phone's GPS location to your company (every ~30
  seconds), so dispatch can see roughly where you are. You'll see a
  **"Sharing live location"** indicator while this is running.
  - This requires **Location permission**. If you deny it or your phone's
    location services are off, the app simply won't share location — it
    won't crash or repeatedly nag you, but dispatch won't see your position.
  - Location sharing automatically stops when you don't have an active trip.

### 4.5 Adding Checkpoints

While a trip is active, you can log progress milestones — these don't change
the trip's overall status but appear on the **Timeline** (and on the
customer's shipment tracking in the Client Portal). Typical checkpoints:

- **Reached Pickup**
- **Loaded**
- **Reached Destination**

Use the checkpoint buttons on the Active Trip Map / Trip Details screens to
record these as they happen — they help dispatch and the customer follow
along in real time.

### 4.6 Proof of Delivery & Marking Delivered

When you've arrived and handed over the goods, open the trip and go to
**Proof of Delivery**:

1. **Delivery Photo** — tap to capture/select a photo of the delivered goods
   (using your camera or photo gallery).
2. **Signature** — draw the receiver's signature directly on the screen with
   your finger/stylus. There's a **Clear** button if you need to redo it.
   (Signature is optional — the photo is the only required field.)
3. **Receiver Name** and **Remarks** — fill these in.
4. Tap **Submit Delivery**.

What happens next:
- A checkpoint like *"Delivered to {receiver name}: {remarks}"* is added to
  the trip's timeline.
- The photo (and signature, if drawn) are uploaded and attached to the trip
  as documents — viewable later from the **Documents** tab.
- The trip's status changes to **Delivered**, which automatically generates
  a draft invoice on the back end (handled by Accounts/TenantAdmin in the web
  app).

### 4.7 Documents

The **Documents** screen (under Profile, or its own section) has three tabs:

- **Vehicle** — documents on file for your currently assigned truck (e.g.
  registration, insurance, fitness certificate, permit). If you have no
  assigned truck, you'll see a message explaining that.
- **Driver** — documents on file for you personally (e.g. license copy,
  medical certificate).
- **Trip** — proof-of-delivery photos and signatures from your 5 most recent
  trips, each labeled with its load number.

Each document shows its type and file name. Tap any document that has a file
attached (POD photos/signatures, and any uploaded vehicle/driver documents)
to view it full-screen.

### 4.8 Notifications

The **Notifications** tab shows a **"Recent Activity"** feed — a simple,
always-up-to-date summary of what's happened on your recent trips, such as:

- **New Trip Assigned** — you've been allocated a new load.
- **Trip Started** — you started a trip.
- **Trip Completed** — a trip was marked delivered.
- **Trip Cancelled** — a trip was cancelled.
- Checkpoint updates (e.g. "Reached Pickup").

A small badge on the bottom-nav Notifications icon shows how many newly
assigned trips you haven't started yet. Pull down to refresh.

> This is a lightweight, in-app feed (not push notifications) — open the app
> to see what's new.

### 4.9 Profile

The **Profile** tab shows:

- Your name, photo, and basic contact info.
- **License** — license number, class, and expiry date.
- **Emergency Contact**.
- **Assigned Vehicle** — your currently assigned truck's details and photos
  (tap through to **Vehicle Information** for the full view).
- **Settings** — see [Section 6](#6-settings-language-theme--logout).
- **Logout**.

---

## 5. Client Mode (Mobile Client Portal)

Client mode has 4 tabs along the bottom: **Home**, **Shipments**,
**Invoices**, and **Profile**.

> Just like the web Client Portal, your account can be linked to more than
> one transport company ("carrier") — your shipments and invoices from **all**
> linked carriers appear together, each labeled with its carrier.

### 5.1 Home

A quick overview:

- Your company name.
- A summary of your shipments by status (how many are in transit, delivered,
  etc.).
- Your **total outstanding** balance across all invoices.
- Your most recent shipments, with a shortcut into each.

### 5.2 Shipments

The **Shipments** tab lists all your bookings, with:

- **Filters** — by status and by carrier (if you ship with more than one
  transport company).
- Each row shows the load number, carrier, route, pickup date, goods type,
  and status.

**Creating a new booking request:**

1. Tap the **New Booking** button (usually a `+` or similar action).
2. Fill in the form:
   - **Carrier** (if applicable)
   - **From** and **To**
   - **Pickup Date**
   - **Goods Type**
   - Optional: Weight, Truck Preference, Goods Description, Special
     Instructions
3. Submit. Your new shipment appears with status **Draft**, pending review by
   the carrier's operations team.

**Viewing a shipment:**

Tap any shipment to see:

- Full route and date details, goods type/weight/description, special
  instructions, and (if cancelled) the cancellation reason.
- **Status Timeline** — every status change and checkpoint, with timestamps —
  the same information the driver sees, so you can follow your shipment's
  progress (e.g. "Reached Pickup", "In Transit", "Delivered").
- **Documents** — any files attached (e.g. proof of delivery photo), with a
  way to view/download each.

**Editing or cancelling a booking:** while a shipment is still **Draft** or
**Confirmed** (i.e., not yet allocated/dispatched), you can edit its details
or cancel it from the shipment's detail screen. Once a truck/driver has been
assigned, changes must go through the carrier directly.

### 5.3 Invoices

The **Invoices** tab lists your bills:

- **Filter by status** (Draft, Sent, Partial, Paid, Overdue, Cancelled).
- Each row shows invoice number, carrier, issued/due dates, total, paid, and
  outstanding amounts, plus the status.

Tap an invoice to see full details — line items, amounts, and **Payment
History** (any payments the carrier has recorded against it).

**Downloading a PDF:** tap **Download** (or the share icon) on an invoice to
save or share a PDF copy — useful for your own records or accounting.

> Recording payments is done by the carrier's staff in the web app — you can
> view and download, but not mark invoices as paid.

### 5.4 Profile

Shows:

- Your linked company/carrier details.
- **Settings** — language and theme (Section 6).
- **Logout**.

---

## 6. Settings: Language, Theme & Logout

From the **Profile** tab (in either Driver or Client mode), under
**Settings**:

- **Dark Mode** — toggle between light and dark appearance. Your choice is
  saved on this device.
- **Language** — switch between English, हिन्दी (Hindi), and தமிழ் (Tamil) at
  any time — the whole app updates immediately, no restart needed.
- **Logout** — signs you out and returns you to the Login screen. (Your
  Driver/Client mode choice is preserved — you won't see the onboarding
  screen again unless you reinstall/clear app data.)

---

## 7. Troubleshooting & FAQ

- **The app can't log in / shows a network error.** Make sure your device has
  internet access and can reach your company's TransTrack server. If you're
  testing locally, double-check the `API_BASE_URL` used to launch the app
  (see [`apps/driver-mobile/README.md`](../apps/driver-mobile/README.md)).
- **I picked the wrong mode (Driver/Client) during onboarding.** There's no
  in-app switch yet — reinstall the app or clear its app data to see the
  onboarding screen again.
- **"Sharing live location" never appears on the Map tab.** This only shows
  while you have an **active (in-transit)** trip, and requires **Location
  permission** granted to the app and your device's location services turned
  on. If permission is denied, the app fails silently (no live location sent,
  but no crash either) — check your phone's app permissions for TransTrack.
- **My trips/documents show sample data instead of my real trips.** This
  happens only when you have **zero** assigned trips — it's placeholder
  content so the screens aren't empty. Once you're allocated a real load, it
  replaces the sample data automatically.
- **The map doesn't show a route/road tiles.** This is expected for now — the
  Active Trip Map is a simplified placeholder; live GPS *is* being sent to
  dispatch (see above), but a full interactive map is planned for a future
  update.
- **I don't see push notifications.** TransTrack mobile currently uses an
  in-app "Recent Activity" feed (Section 4.8) rather than push notifications
  — open the app to see the latest updates.
- **Forgot your password?** Use **Forgot Password** on the Login screen —
  this follows the same process as the web app
  ([`docs/user-guide-web.md`](./user-guide-web.md#22-forgot-password)). If no
  reset link arrives (no email service configured in your environment yet),
  contact your dispatcher/administrator.
- **Pull-to-refresh** — almost every list screen (Trips, Documents,
  Notifications, Shipments, Invoices) supports pulling down to refresh with
  the latest data from the server.
