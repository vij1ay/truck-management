"""
Demo data seeder — creates a sample tenant with the accounts documented in
README's "Seed Accounts" table, plus a handful of trucks/drivers/clients so
the UI isn't empty on first login.

This is separate from `seed_data.py` (which only creates system roles + the
SuperAdmin) so that environments which don't want demo/sample data can skip
it. Safe to re-run — every entity is looked up before creation.

Usage:
    python -m app.scripts.seed_demo
"""

import os
import sys
from datetime import date, timedelta

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.datetime_utils import utc_now
from app.core.security import hash_password
from app.models import (
    Tenant,
    Role,
    User,
    UserRole,
    Truck, TruckType, TruckStatus, OwnershipType,
    Driver, DriverStatus, LicenseClass,
    Client, ClientType,
)
from app.scripts.seed_data import seed_roles

DEMO_PASSWORD = "password123"
TENANT_NAME = "Demo Transport Co"


def get_or_create_tenant(db: Session) -> Tenant:
    """Create the demo tenant if it doesn't already exist."""
    tenant = db.query(Tenant).filter_by(name=TENANT_NAME).first()
    if tenant:
        print(f"  Tenant '{TENANT_NAME}' already exists")
        return tenant

    tenant = Tenant(
        name=TENANT_NAME,
        domain="demo.transport.com",
        is_active=True,
    )
    db.add(tenant)
    db.flush()
    print(f"  Created tenant: {TENANT_NAME}")
    return tenant


def get_or_create_user(
    db: Session,
    *,
    email: str,
    first_name: str,
    last_name: str,
    role_name: str,
    tenant_id,
    roles: dict[str, Role],
) -> User:
    """Create a demo user with the given role, or return the existing one."""
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        print(f"  User '{email}' already exists")
        return existing

    user = User(
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        first_name=first_name,
        last_name=last_name,
        tenant_id=tenant_id,
        is_active=True,
        is_verified=True,
        password_changed_at=utc_now(),
    )
    db.add(user)
    db.flush()

    role = roles.get(role_name)
    if role:
        db.add(UserRole(
            user_id=user.id,
            role_id=role.id,
            tenant_id=tenant_id,
            assigned_at=utc_now(),
        ))
        db.flush()

    print(f"  Created user: {email} ({role_name}) — password: {DEMO_PASSWORD}")
    return user


def seed_demo_trucks(db: Session, tenant_id) -> list[Truck]:
    """Create a couple of sample trucks for the demo tenant."""
    specs = [
        dict(
            registration_no="MH-12-AB-1234",
            ownership_type=OwnershipType.OWNED,
            truck_type=TruckType.CONTAINER,
            status=TruckStatus.ACTIVE,
            make="Tata", model="Prima", year=2022, color="White",
            capacity_tons=16, owner_name="Demo Transport Co", owner_contact="9000000001",
        ),
        dict(
            registration_no="MH-14-CD-5678",
            ownership_type=OwnershipType.OWNED,
            truck_type=TruckType.FLATBED,
            status=TruckStatus.ACTIVE,
            make="Ashok Leyland", model="2518", year=2021, color="Blue",
            capacity_tons=18, owner_name="Demo Transport Co", owner_contact="9000000001",
        ),
        dict(
            registration_no="GJ-01-EF-9012",
            ownership_type=OwnershipType.CONTRACT,
            truck_type=TruckType.TANKER,
            status=TruckStatus.ACTIVE,
            make="Bharat Benz", model="3123", year=2020, color="Red",
            capacity_tons=20, contractor_name="XYZ Logistics", contractor_contact="9000000099",
        ),
    ]

    trucks = []
    for spec in specs:
        existing = db.query(Truck).filter_by(tenant_id=tenant_id, registration_no=spec["registration_no"]).first()
        if existing:
            print(f"  Truck '{spec['registration_no']}' already exists")
            trucks.append(existing)
            continue

        truck = Truck(tenant_id=tenant_id, is_available=True, **spec)
        db.add(truck)
        db.flush()
        print(f"  Created truck: {spec['registration_no']}")
        trucks.append(truck)

    return trucks


def seed_demo_drivers(db: Session, tenant_id, linked_user_id) -> list[Driver]:
    """Create sample drivers; the first is linked to driver@demo.transport.com."""
    specs = [
        dict(
            employee_id="EMP-001",
            first_name="Rajesh", last_name="Kumar",
            phone="9000000010", email="driver@demo.transport.com",
            license_no="MH1420230001234",
            license_class=LicenseClass.HMV,
            license_expiry=date.today() + timedelta(days=730),
            base_location="Mumbai Depot",
            user_id=linked_user_id,
        ),
        dict(
            employee_id="EMP-002",
            first_name="Suresh", last_name="Patil",
            phone="9000000011", email=None,
            license_no="MH1220220005678",
            license_class=LicenseClass.HGV,
            license_expiry=date.today() + timedelta(days=540),
            base_location="Pune Depot",
            user_id=None,
        ),
    ]

    drivers = []
    for spec in specs:
        existing = db.query(Driver).filter_by(tenant_id=tenant_id, license_no=spec["license_no"]).first()
        if existing:
            print(f"  Driver '{spec['first_name']} {spec['last_name']}' already exists")
            drivers.append(existing)
            continue

        driver = Driver(
            tenant_id=tenant_id,
            status=DriverStatus.AVAILABLE,
            is_available=True,
            **spec,
        )
        db.add(driver)
        db.flush()
        print(f"  Created driver: {spec['first_name']} {spec['last_name']}")
        drivers.append(driver)

    return drivers


def seed_demo_clients(db: Session, tenant_id, linked_user_id) -> list[Client]:
    """Create sample clients; the first is linked to client@demo.transport.com."""
    specs = [
        dict(
            company_name="Acme Industries Pvt Ltd",
            contact_person="Anil Mehta",
            email="client@demo.transport.com",
            phone="9000000020",
            city="Mumbai", state="Maharashtra", pincode="400001",
            gst_no="27AAAAA0000A1Z5",
            user_id=linked_user_id,
        ),
        dict(
            company_name="Bharat Retail Group",
            contact_person="Sunita Rao",
            email="contact@bharatretail.example",
            phone="9000000021",
            city="Pune", state="Maharashtra", pincode="411001",
            gst_no="27BBBBB0000B1Z5",
            user_id=None,
        ),
    ]

    clients = []
    for spec in specs:
        existing = db.query(Client).filter_by(tenant_id=tenant_id, company_name=spec["company_name"]).first()
        if existing:
            print(f"  Client '{spec['company_name']}' already exists")
            clients.append(existing)
            continue

        client = Client(
            tenant_id=tenant_id,
            client_type=ClientType.COMPANY,
            is_active=True,
            **spec,
        )
        db.add(client)
        db.flush()
        print(f"  Created client: {spec['company_name']}")
        clients.append(client)

    return clients


def run_seed():
    """Run the demo data seeder."""
    print("\n" + "=" * 50)
    print("Transport Management System - Demo Data Seeder")
    print("=" * 50 + "\n")

    db = SessionLocal()

    try:
        print("Seeding roles (in case seed_data hasn't run)...")
        roles = seed_roles(db)

        print(f"\nSeeding tenant '{TENANT_NAME}'...")
        tenant = get_or_create_tenant(db)

        print("\nSeeding demo users...")
        get_or_create_user(
            db, email="admin@demo.transport.com", first_name="Demo", last_name="Admin",
            role_name="TenantAdmin", tenant_id=tenant.id, roles=roles,
        )
        get_or_create_user(
            db, email="transport@demo.transport.com", first_name="Demo", last_name="Transport",
            role_name="TransportAdmin", tenant_id=tenant.id, roles=roles,
        )
        get_or_create_user(
            db, email="accounts@demo.transport.com", first_name="Demo", last_name="Accounts",
            role_name="Accounts", tenant_id=tenant.id, roles=roles,
        )
        client_user = get_or_create_user(
            db, email="client@demo.transport.com", first_name="Demo", last_name="Client",
            role_name="Client", tenant_id=tenant.id, roles=roles,
        )
        driver_user = get_or_create_user(
            db, email="driver@demo.transport.com", first_name="Demo", last_name="Driver",
            role_name="Driver", tenant_id=tenant.id, roles=roles,
        )

        print("\nSeeding demo trucks...")
        seed_demo_trucks(db, tenant.id)

        print("\nSeeding demo drivers...")
        seed_demo_drivers(db, tenant.id, driver_user.id)

        print("\nSeeding demo clients...")
        seed_demo_clients(db, tenant.id, client_user.id)

        db.commit()

        print("\n" + "=" * 50)
        print("Demo seeding completed successfully!")
        print(f"All demo accounts use password: {DEMO_PASSWORD}")
        print("=" * 50 + "\n")

    except Exception as e:
        print(f"\nError during demo seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
