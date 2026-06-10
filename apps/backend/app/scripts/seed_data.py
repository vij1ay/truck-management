"""
Database seeder script for initial data setup.

This script creates:
1. System roles (SuperAdmin, TenantAdmin, etc.)
2. SuperAdmin user (from environment variables)

Usage:
    python -m app.scripts.seed_data
"""

import os
import sys
from datetime import datetime

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session

from app.config import get_settings
from app.core.database import SessionLocal, engine
from app.core.security import hash_password
from app.models import Base, Role, User, UserRole, SYSTEM_ROLES

settings = get_settings()


def seed_roles(db: Session) -> dict[str, Role]:
    """Seed system roles."""
    roles = {}
    
    for role_data in SYSTEM_ROLES:
        existing = db.query(Role).filter_by(name=role_data["name"]).first()
        
        if existing:
            print(f"  Role '{role_data['name']}' already exists")
            roles[role_data["name"]] = existing
        else:
            role = Role(
                name=role_data["name"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_system_role=role_data["is_system_role"]
            )
            db.add(role)
            db.flush()
            print(f"  Created role: {role_data['name']}")
            roles[role_data["name"]] = role
    
    return roles


def seed_superadmin(db: Session, roles: dict[str, Role]) -> User | None:
    """Seed SuperAdmin user."""
    email = settings.SUPERADMIN_EMAIL
    password = settings.SUPERADMIN_PASSWORD
    
    if not password:
        print("  WARNING: SUPERADMIN_PASSWORD not set. Skipping SuperAdmin creation.")
        print("  Set SUPERADMIN_PASSWORD environment variable and run again.")
        return None
    
    # Check if SuperAdmin already exists
    existing = db.query(User).filter_by(email=email).first()
    if existing:
        print(f"  SuperAdmin '{email}' already exists")
        return existing
    
    # Create SuperAdmin user
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=settings.SUPERADMIN_FIRST_NAME,
        last_name=settings.SUPERADMIN_LAST_NAME,
        tenant_id=None,  # SuperAdmin has no tenant
        is_active=True,
        is_verified=True,
        password_changed_at=datetime.utcnow()
    )
    db.add(user)
    db.flush()
    
    # Assign SuperAdmin role
    superadmin_role = roles.get("SuperAdmin")
    if superadmin_role:
        user_role = UserRole(
            user_id=user.id,
            role_id=superadmin_role.id,
            tenant_id=None,
            assigned_at=datetime.utcnow()
        )
        db.add(user_role)
        db.flush()
    
    print(f"  Created SuperAdmin: {email}")
    return user


def create_tables():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("  Tables created successfully")


def run_seed():
    """Run the seeder."""
    print("\n" + "=" * 50)
    print("Transport Management System - Database Seeder")
    print("=" * 50 + "\n")
    
    # Create tables first
    create_tables()
    
    # Create session
    db = SessionLocal()
    
    try:
        print("\nSeeding roles...")
        roles = seed_roles(db)
        
        print("\nSeeding SuperAdmin...")
        seed_superadmin(db, roles)
        
        # Commit all changes
        db.commit()
        
        print("\n" + "=" * 50)
        print("Seeding completed successfully!")
        print("=" * 50 + "\n")
        
    except Exception as e:
        print(f"\nError during seeding: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
