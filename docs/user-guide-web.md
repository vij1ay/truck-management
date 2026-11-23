# TransTrack — Web Application User Guide.

This guide explains how to use the TransTrack **admin web application**
(`apps/admin-frontend`) — the Angular portal used by transport company staff
(SuperAdmin, TenantAdmin, TransportAdmin, Accounts, Driver) and by customers
through the **Client Portal**.

> Looking for the mobile driver/customer app instead? See
> [`docs/user-guide-mobile.md`](./user-guide-mobile.md).

---

## Table of Contents

1. [Who This Guide Is For](#1-who-this-guide-is-for)
2. [Signing In](#2-signing-in)
3. [Getting Around](#3-getting-around)
4. [Load Management (Dispatch Board)](#4-load-management-dispatch-board)
5. [My Tasks (Driver)](#5-my-tasks-driver)
6. [Trucks](#6-trucks)
7. [Drivers](#7-drivers)
8. [Clients](#8-clients)
9. [Tenants (SuperAdmin)](#9-tenants-superadmin)
10. [Users & Access](#10-users--access)
11. [Audit Log](#11-audit-log)
12. [Reports](#12-reports)
13. [Invoices & Payments](#13-invoices--payments)
14. [Client Portal](#14-client-portal)
15. [End-to-End Walkthrough: From Booking to Payment](#15-end-to-end-walkthrough-from-booking-to-payment)
16. [Tips, Settings & Troubleshooting](#16-tips-settings--troubleshooting)

---

## 1. Who This Guide Is For

TransTrack is a multi-tenant platform — each transport company ("tenant") has
its own isolated data. Within a tenant, what you can see and do depends on
your **role**:

| Role | What they typically do |
|------|--------------------------|
| **SuperAdmin** | Manages the platform itself — creates and oversees tenants (transport companies). Can view data across all tenants using the Tenant filter. |
| **TenantAdmin** | Full control of their own company: users, trucks, drivers, clients, loads, invoices, audit log, reports. |
| **TransportAdmin** | Day-to-day operations: loads, allocation, trucks, drivers, reports. |
| **Accounts** | Finance: clients, invoices, payments, reports. |
| **Client** (Web Portal) | A customer of the transport company. Logs into the **Client Portal** (separate area) to request bookings, track shipments, and view/download invoices. |
| **Driver** | Primarily uses the mobile app, but can also log into the web app to see **My Tasks** and start trips. |

Every screen below notes which roles can see it. If a menu item described
here is missing for you, your account doesn't have that role — ask your
TenantAdmin.

---

## 2. Signing In

### 2.1 Login

Open the web app in your browser and go to the **Login** page
(`/auth/login`):

1. Enter your **Email** and **Password**.
2. Click **Login**.
3. You'll land on your home page — for most staff roles this is the
   **Load Management** dashboard; for the **Client** role it's the
   **Client Portal** ("My Shipments").

> **Try it with demo data** — after the project has been seeded with
> `make seed-demo`, you can sign in with any of these (password
> `password123` for all):
>
> | Email | Role | What you'll see |
> |-------|------|------------------|
> | `admin@demo.transport.com` | TenantAdmin | Full access to "Demo Transport Co" |
> | `transport@demo.transport.com` | TransportAdmin | Operations (loads, trucks, drivers, reports) |
> | `accounts@demo.transport.com` | Accounts | Clients, invoices, reports |
> | `client@demo.transport.com` | Client | Client Portal for "Acme Industries Pvt Ltd" |
> | `driver@demo.transport.com` | Driver | "My Tasks" for driver "Rajesh Kumar" |

### 2.2 Forgot Password

If you can't remember your password:

1. On the Login page, click **Forgot password?**
2. Enter your account email and click **Send Reset Link**.
3. For privacy/security, you'll always see the same confirmation message —
   whether or not that email has an account ("if an account exists, a reset
   link has been sent").
4. In a production deployment, you'll receive an email with a reset link.
   In a development/demo environment (no email service configured yet), the
   page itself shows a **"Continue to Reset Password"** button you can click
   directly.

### 2.3 Reset Password

On the **Reset Password** page:

1. Enter a **New Password** and **Confirm New Password**.
   - Must be **at least 8 characters** and include an **uppercase letter**,
     a **lowercase letter**, and a **digit**.
2. Click **Reset Password**.
3. You'll be returned to the Login page. Resetting your password also signs
   you out of all other devices/sessions for security.

---

## 3. Getting Around

### 3.1 The Main Layout

After login, staff roles see:

- A **side navigation menu** (left) listing the sections you have access to
  (see the table below).
- A **top toolbar** with:
  - A button to collapse/expand the side menu.
  - A **light/dark theme toggle**.
  - A **language switcher** (English / Español).
  - Your **profile menu** (your name and email) with a **Logout** option.

### 3.2 Menu Items by Role

| Menu item | Visible to |
|-----------|------------|
| **Dashboard / Load Board** | SuperAdmin, TenantAdmin, TransportAdmin, Accounts (and SuperAdmin) |
| **My Tasks** | Driver |
| **Tenants** | SuperAdmin |
| **Users** | TenantAdmin, TransportAdmin (and SuperAdmin) |
| **Trucks** | TenantAdmin, TransportAdmin (and SuperAdmin) |
| **Drivers** | TenantAdmin, TransportAdmin (and SuperAdmin) |
| **Clients** | TenantAdmin, Accounts (and SuperAdmin) |
| **Reports** | TenantAdmin, TransportAdmin, Accounts, SuperAdmin |
| **Invoices** | TenantAdmin, TransportAdmin, Accounts, SuperAdmin |
| **Audit Log** | SuperAdmin, TenantAdmin |

> SuperAdmin sees everything above, plus a **Tenant filter** dropdown at the
> top of most list screens to view data across all transport companies.

### 3.3 The Client Portal

If you log in as a **Client**, you don't see the menu above at all — you land
directly in the **Client Portal**, a simplified view with just:

- **My Shipments** (your bookings)
- **My Invoices** (your bills)
- The same theme toggle and profile/logout menu

See [Section 14](#14-client-portal) for details.

---

## 4. Load Management (Dispatch Board)

**Who sees this:** SuperAdmin, TenantAdmin, TransportAdmin, Accounts — labeled
**"Load Management"**.

This is the central screen for tracking every shipment ("load") through its
lifecycle:

```
draft → confirmed → allocated → in_transit → delivered
                  ↘ cancelled (from any non-final status)
```

| Status | Meaning |
|--------|---------|
| **Draft** | A new booking request (usually placed by a Client through the Client Portal) awaiting review. |
| **Confirmed** | Approved by your team; ready to be assigned a truck and driver. |
| **Allocated** | A truck and driver have been assigned; ready to start. |
| **In Transit** | The driver has started the trip. |
| **Delivered** | The shipment arrived; an invoice is automatically created as a draft. |
| **Cancelled** | The load was cancelled (with a reason recorded). |

### 4.1 Finding Loads

Use the filter bar at the top:

- **Search** — free text across Load #, origin, and destination.
- **Status** — filter to a single status (or "All Statuses").
- **Client** — filter to a specific customer.
- **Pickup From / Pickup To** — date range on the pickup date.
- **Clear Filters** — appears once any filter is active; resets the view.

(SuperAdmin additionally sees a **Tenant** dropdown and a **Tenant** column.)

The table shows: **Load #**, From, To, Pickup Date, Goods type, and a
color-coded **Status** badge. Results are paginated (10/20/50 per page).

### 4.2 Approving a Booking

New customer bookings arrive with status **Draft**. To approve one:

1. Find the load (filter by Status = Draft if needed).
2. Click the **✓ (Approve)** icon in the Actions column.
3. The load moves to **Confirmed**, ready for allocation.

### 4.3 Assigning a Truck & Driver (Allocation)

Once a load is **Confirmed**:

1. Click the **Assign Truck & Driver** icon (clipboard with person).
2. The **Assign Truck & Driver** dialog opens, showing the load summary
   (Load #, route, pickup date).
3. **Select Truck** — only trucks that are free on the pickup date are
   listed (registration number, type, capacity). If none are available, the
   dialog tells you so — you may need to free up a truck or add one
   ([Section 6](#6-trucks)).
4. **Select Driver** — likewise, only drivers free on that date are listed
   (name + license class).
5. Optionally add **Notes** for the driver/operations team.
6. Click **Assign & Dispatch**. The load moves to **Allocated**.

### 4.4 Cancelling a Load

Any load that isn't already **Delivered** or **Cancelled** can be cancelled:

1. Click the **✕ (Cancel)** icon.
2. You must enter a **cancellation reason** in the confirmation dialog —
   this is required and is recorded on the load's history/timeline (visible
   to the customer in the Client Portal).
3. Confirm. The load moves to **Cancelled**.

### 4.5 Uploading Proof of Delivery (POD)

Once a load is **Delivered** (the driver marks this from the mobile app), you
can attach the proof-of-delivery paperwork from the web too:

1. Click the **Upload Proof of Delivery** icon (only shown for Delivered
   loads).
2. In the dialog, enter a **File Name**, the **File URL** (link to where the
   document is stored), and optional **Notes**.
3. Click **Upload**. The document is attached to the load's record.

---

## 5. My Tasks (Driver)

**Who sees this:** users with the **Driver** role (this is the "My Tasks"
menu item; full driver functionality — checkpoints, photos, signatures, live
location — lives in the **mobile app**, see
[`docs/user-guide-mobile.md`](./user-guide-mobile.md)).

This screen shows a card for each load **allocated to you**:

- Load #, status badge, route (origin → destination), pickup date, cargo
  type, and any special instructions.
- If the load is **Allocated**, a **Start Trip** button is shown. Tapping it
  opens a confirmation ("Confirm you are starting the trip for load X from A
  to B?") — confirming moves the load to **In Transit**.
- If the load is already **In Transit**, the card shows a **"Trip in
  Progress"** badge instead.

If you have no assigned loads, the screen shows "No tasks currently assigned
to you."

---

## 6. Trucks

**Who sees this:** TenantAdmin, TransportAdmin (and SuperAdmin).

### 6.1 The Truck List

Shows every truck registered to your company: photo, registration number,
type, capacity, status, and date added. (SuperAdmin also sees a Tenant
filter/column.)

Row actions:
- **Edit** — open the truck's details.
- **Activate** / **Deactivate** — toggle a truck between **Available** and
  **Inactive**/**Maintenance** (the action shown depends on current status).
- **Delete** — remove the truck record.

### 6.2 Adding or Editing a Truck

Click **Add New** (or **Edit** on an existing truck) to open the truck form:

- **Photo** — upload a picture of the truck (you can change/remove it once
  the truck exists).
- **Identification**
  - **Registration Number** *(required, cannot be changed after creation)*
  - **Truck Type** — Flatbed, Container, Tanker, Refrigerated, Tipper,
    Low-Bed, or Other
  - **Ownership Type** — Owned, Contract, or Leased
- **Specifications** — Make, Model, Year of Manufacture (1980–present),
  Color, Capacity (tons, 0–200)
- Depending on **Ownership Type**, additional fields appear:
  - *Owned*: Owner Name, Owner Contact
  - *Contract*: Contractor Name/Contact, Contract Start/End Date
  - *Leased*: Lessor Name/Contact, Lease Start/End Date
- **Notes** — free text

Click **Register Truck** (new) or **Save Changes** (edit).

### 6.3 Photo Gallery & Documents (existing trucks only)

When editing a truck that already exists, two extra sections appear:

- **Photo Gallery** — a grid of additional photos. Click the **Add** tile to
  upload more (PNG/JPEG/WEBP); each photo can be removed (with confirmation).
- **Attached Documents** — lists documents on file for this truck (file name,
  type, date, and status — including an "EXPIRED" badge for out-of-date
  documents like insurance/permits), with a **View** action to open the file.

---

## 7. Drivers

**Who sees this:** TenantAdmin, TransportAdmin (and SuperAdmin).

### 7.1 The Driver List

Shows: Name, Phone, License No, License Class, License Expiry, Base Location,
and Status. (SuperAdmin also sees a Tenant filter/column.)

Row actions:
- **Edit**
- **Mark Available** / **Mark Unavailable** — toggles whether the driver can
  be assigned new loads.
- **Delete**

### 7.2 Adding or Editing a Driver

Click **Add New** (or **Edit**):

- **Personal Information** — First Name*, Last Name*, Phone* (min. 7
  digits), Email, Employee ID, Address
- **Licence Details**
  - **Licence Number** *(required, cannot be changed after creation)*
  - **Licence Class*** — LMV (Light Motor Vehicle), HMV (Heavy Motor
    Vehicle), HGV (Heavy Goods Vehicle), or Other
  - **Licence Expiry Date*** (date picker)
- **Location & Truck Assignment** — Base Location (home depot), and a
  multi-select of **Qualified Trucks** the driver is allowed to operate
  (used when allocating loads)
- **Emergency Contact** (optional) — Contact Name, Contact Phone
- **Notes**

Click **Register Driver** (new) or **Save Changes** (edit).

### 7.3 Documents (existing drivers only)

When editing an existing driver, an **Attached Documents** section lists
files on record (e.g. a scanned license copy) with file name, type, date,
status, and a **View** action.

---

## 8. Clients

**Who sees this:** TenantAdmin, Accounts (and SuperAdmin).

### 8.1 The Client List

Shows each customer's logo, company name, contact person, email, GST number,
status, and date added. (SuperAdmin also sees a Tenant filter/column.)

Row actions: **Edit**, **Delete**.

### 8.2 Adding or Editing a Client

Click **Add New** (or **Edit**):

- **Logo** — optional company logo upload
- **Company Name*** , **Contact Person*** , **Contact Phone*** (validated
  phone format), **Email Address*** , **GST Number*** *(cannot be changed
  after creation)*, **Billing Address***

### 8.3 Linking a Client Portal Account

Every client record can optionally be linked to a login that lets the
customer use the **Client Portal** (Section 14) to track their own shipments
and invoices. This section only appears when **editing** a client:

- **If already linked**, you'll see "Linked to a portal (Client) account"
  with an **Unlink** button. Unlinking removes that login's access to this
  client's data (it doesn't delete the user account itself).
- **If not linked**, enter the customer's **portal account email** (the
  email they registered or were given for portal access — this can be a
  login created under a *different* tenant, since one customer can ship with
  multiple carriers) and click **Link**.

> One login can be linked to a different `Client` record in each transport
> company it ships with — linking here only affects this company's records.

---

## 9. Tenants (SuperAdmin)

**Who sees this:** SuperAdmin only.

This is where the platform owner manages transport companies ("tenants").

### 9.1 The Tenant List

Shows each tenant's logo, name, domain, subscription tier, user quota
(maximum users), status, and creation date.

Row actions: **Edit**, **Delete** (deleting a tenant also deletes **all** of
that company's users and data — you'll be warned before confirming).

### 9.2 Adding a Tenant

Click **Add New**:

- **Tenant Details** — Company Name*, Domain (optional), Subscription Tier,
  Max Users
- **Admin User Profile** (creation only) — First Name, Last Name, Admin
  Email, Initial Password — this creates the company's first **TenantAdmin**
  account in the same step.

Click **Add New** to save. (When editing, this becomes **Save** and the admin
user fields are not shown — manage users via [Section 10](#10-users--access)
instead.)

---

## 10. Users & Access

**Who sees this:** TenantAdmin, TransportAdmin (and SuperAdmin).

### 10.1 The User List

Shows each user's avatar, name, email, (Tenant, for SuperAdmin), assigned
roles, and active/inactive status.

Row actions: **Edit**, **Activate**/**Deactivate**, **Delete**.

### 10.2 Adding or Editing a User

Click **Add New** (or **Edit**):

- **Avatar** — optional profile picture
- **First Name*** , **Last Name*** , **Email*** *(cannot be changed after
  creation)*, **Phone** (optional)
- **Access Role** — choose one of **TransportAdmin**, **Accounts**,
  **Client**, or **Driver**.
  - This can only be set when **creating** the user. When editing, the field
    is locked with a hint to "use the Roles tab" for role changes.
- **Timezone** — controls how dates/times are displayed to this user
  throughout the app (defaults to `Asia/Kolkata`).
- **Linked Client** — appears only when the role is **Client**. Pick which
  customer company (from your Clients list) this login represents — this is
  the same link described in [Section 8.3](#83-linking-a-client-portal-account),
  done from the user's side instead of the client's side.
- **Initial Password** (creation only) — set a starting password for the new
  user (they can change it later, or use Forgot Password).

Click **Add New** or **Save**.

> **Note:** SuperAdmin can only create **TenantAdmin** users directly (when
> creating a new tenant). TenantAdmin/TransportAdmin create the
> TransportAdmin/Accounts/Client/Driver users for their own company.

---

## 11. Audit Log

**Who sees this:** SuperAdmin, TenantAdmin.

Every significant action in the system (logins, role changes, record
creation/updates, etc.) is recorded here for accountability.

### 11.1 Filtering

- **Category** — All Categories, Auth, User Management, Role Management,
  Tenant Management
- **Event Type** — free text (e.g. type "LOGIN" or "USER_CREATED")
- **From / To** — date range
- **Clear Filters**

(SuperAdmin also sees a Tenant filter/column.)

### 11.2 The Log Table

Columns: Time, (Tenant), User (email), Event, Category, Resource type,
Resource ID. Default page size is 25.

### 11.3 Viewing Details

Click the **eye icon** (View Details) on any row to open a dialog showing:

- When it happened, the category, and which user did it
- The resource type/ID affected
- IP address and browser/user-agent (if recorded)
- **Old Value** / **New Value** — a side-by-side diff of what changed (if
  applicable)
- **Extra Data** — any additional structured details

This dialog is read-only — click **Close** when done.

---

## 12. Reports

**Who sees this:** TenantAdmin, TransportAdmin, Accounts, SuperAdmin.

A read-only analytics dashboard for your company (or, for SuperAdmin, the
selected tenant).

### 12.1 KPI Cards (top of page)

- **Total Loads** (with this-month count)
- **Delivered Revenue** (with this-month figure, in ₹)
- **Outstanding Balance** on delivered loads
- **Trucks Available / Active**
- **Drivers Available / Active**
- **Overdue Invoices** (amount and count)

### 12.2 Tabs

- **Overview**
  - *Load Status Breakdown* — a progress bar for each status (Delivered, In
    Transit, Confirmed, Allocated, Draft, Cancelled) with counts and
    percentages.
  - *Monthly Load Trend* — a table of the last 12 months: Total, Delivered,
    Cancelled.
- **Revenue**
  - Summary chips: Total Freight, Total Advance, Outstanding.
  - *Revenue by Client* — per-customer breakdown of Loads, Total Freight,
    Advance, and Outstanding (cancelled loads excluded; sorted by total
    freight). Non-zero outstanding amounts are highlighted.
- **Drivers**
  - *Driver Performance* — per-driver Total trips, Delivered, Cancelled, and
    On-Time count/percentage (of completed trips).
- **Trucks**
  - Fleet status chips (count of trucks per status).
  - *Truck Utilization* — per-truck status and number of delivered trips.

---

## 13. Invoices & Payments

**Who sees this:** TenantAdmin, TransportAdmin, Accounts, SuperAdmin.

Invoices are created automatically when a load is marked **Delivered**.
Statuses: **Draft → Sent → Partial/Paid** (or **Overdue** if past due, or
**Cancelled**).

### 13.1 The Invoice List

- Filter by **Status** (All, Draft, Sent, Partial, Paid, Overdue, Cancelled).
- Columns: Invoice #, (Tenant for SuperAdmin), Client, Load #, Issued date,
  Total, Paid, Outstanding (highlighted if > 0), Status.
- Actions per row: **Download PDF**, **View Details** (or click the row).
- Paginated (25/50/100).

### 13.2 Invoice Detail

Opens when you click an invoice. Shows:

- **Invoice Details** — Client, Load, Issued date, Due date, Notes
- **Amounts** — Subtotal, Tax (with rate), Total, Paid, Outstanding
- **Payment History** — table of Date, Method, Reference, Amount (or "No
  payments recorded yet")

Actions:
- **Download PDF** — always available.
- **Mark as Sent** — only while status is **Draft**; moves it to **Sent**
  (i.e., it has been issued to the customer).
- **Record Payment** — available while status is **Sent**, **Partial**, or
  **Overdue**. Opens the **Record Payment** dialog:
  - Shows the current **Outstanding** amount.
  - Enter **Amount** (must be > 0), **Payment Date** (defaults to today),
    **Payment Method** (Dummy/Test, Cash, Bank Transfer, Cheque), and
    optional **Notes**.
  - Click **Record Payment**. The invoice's Paid/Outstanding amounts update,
    and the status becomes **Partial** (if balance remains) or **Paid** (if
    fully settled).

---

## 14. Client Portal

**Who sees this:** users with the **Client** role. This is a separate,
simplified area (`/portal/...`) — no side menu, just a top bar with **My
Shipments**, **My Invoices**, theme toggle, and your profile/logout menu.

> A "Client" portal account can be linked to companies in **more than one**
> transport company (tenant) — your portal aggregates shipments/invoices
> across **all** companies you're linked to. Each shipment/invoice shows
> which **Carrier** (transport company) it belongs to.

### 14.1 My Shipments

The landing page after login.

**Requesting a new booking:**

1. Click **New Booking Request**. An inline form expands.
2. Fill in:
   - **Carrier** — which transport company should handle this (only shown if
     you're linked to more than one; auto-selected if you're linked to just
     one).
   - **From (Origin)*** and **To (Destination)***
   - **Pickup Date*** (date picker)
   - **Goods Type** — General, Fragile, Hazardous, Chilled, Frozen, Bulk,
     Liquid, Electronics, Furniture, or Machinery
   - **Weight (kg)** (optional)
   - **Truck Preference** (optional free text)
   - **Goods Description** and **Special Instructions / Remarks**
3. Click **Submit Booking Request**.
4. Your shipment appears in the table with status **Draft** — the carrier's
   operations team will review and confirm it (see
   [Section 4.2](#42-approving-a-booking)).
5. Click **Cancel** (the toggle button) to close the form without submitting.

**The shipments table** shows your Booking Ref (load number), Carrier, From,
To, Pickup Date, Goods type, and Status. Click the **open** icon on any row
to see full details.

### 14.2 Shipment Detail

- **Shipment Details** — Route, Pickup Date, Expected Delivery Date,
  Delivered On (once delivered), Goods Type, Description, Weight, Special
  Instructions, and (if applicable) the Cancellation Reason.
- **Status Timeline** — every status change in order, each with a timestamp
  and any remarks (e.g. checkpoints like "Reached Pickup" added by the
  driver, or a cancellation reason).
- **Documents** — any files attached to the shipment (e.g. proof of
  delivery), each with a **Download** button.

### 14.3 My Invoices

- Filter by **Status** (same options as the admin invoice list).
- Table: Invoice #, Carrier, Issued, Due, Total, Paid, Outstanding
  (highlighted if > 0), Status.
- Action: **Download PDF**.
- (Recording payments is done by the carrier's Accounts/TenantAdmin staff,
  not from the portal.)

---

## 15. End-to-End Walkthrough: From Booking to Payment

A typical full cycle, showing who does what and where:

1. **Client** (Client Portal → My Shipments) submits **New Booking
   Request** → load is created with status **Draft**.
2. **TransportAdmin/TenantAdmin** (Load Management) reviews and clicks
   **Approve** → status becomes **Confirmed**.
3. **TransportAdmin/TenantAdmin** clicks **Assign Truck & Driver**, picks an
   available truck + driver, clicks **Assign & Dispatch** → status becomes
   **Allocated**.
4. **Driver** (mobile app, or web "My Tasks") clicks **Start Trip** → status
   becomes **In Transit**. The driver may add checkpoints (e.g. "Reached
   Pickup") which show up on the shipment's Status Timeline.
5. **Driver** (mobile app) uploads a delivery photo/signature and marks the
   load **Delivered** → status becomes **Delivered**, and TransTrack
   automatically creates a **Draft invoice**.
6. **Accounts** (Invoices) reviews the draft invoice, clicks **Mark as Sent**
   → status becomes **Sent**.
7. As payments come in, **Accounts** clicks **Record Payment** for each
   payment received → status becomes **Partial** then **Paid** once fully
   settled.
8. Throughout, the **Client** can track progress on **My Shipments** (Status
   Timeline) and download the invoice PDF from **My Invoices**.
9. **TenantAdmin/SuperAdmin** can review everything that happened via the
   **Audit Log**, and **Reports** summarizes revenue, fleet usage, and driver
   performance across all loads.

---

## 16. Tips, Settings & Troubleshooting

- **Switching theme** — click the sun/moon icon in the top toolbar to toggle
  light/dark mode. Your preference is remembered.
- **Switching language** — use the language dropdown in the top toolbar
  (English / Español).
- **Status colors** — status badges use consistent colors throughout the app
  (Draft = neutral, Confirmed/Allocated = blue/orange tones, In Transit =
  active color, Delivered/Paid = green, Cancelled/Overdue = red) — useful for
  quickly scanning long lists.
- **"Clear Filters"** — if a list looks empty or smaller than expected, check
  the filter bar — an active Status/Client/date filter is a common cause.
  Click **Clear Filters** to reset.
- **SuperAdmin "Tenant" filter** — if you're a SuperAdmin and a screen looks
  empty, make sure you've selected the right tenant (or "All Tenants") in the
  filter dropdown.
- **Why can't I edit a Registration Number / Licence Number / GST Number?**
  These identifying fields are locked after a truck/driver/client is created
  to keep historical records consistent. If you made a typo, contact your
  TenantAdmin/SuperAdmin.
- **Why is "Assign Truck & Driver" not available?** It only appears for loads
  with status **Confirmed**. Approve the load first ([Section 4.2](#42-approving-a-booking)).
- **Why is "Record Payment" not available on an invoice?** It only appears
  for **Sent**, **Partial**, or **Overdue** invoices. A **Draft** invoice
  must first be marked **Sent**.
- **Logging out** — use the profile menu (your name/email) in the top-right
  corner → **Logout**. This also happens automatically if your session
  expires; you'll be returned to the Login page.
- **Forgot Password / Reset Password** — see [Section 2.2–2.3](#22-forgot-password).
