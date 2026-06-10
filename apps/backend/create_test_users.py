import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.core.database import SessionLocal
from app.core.security import hash_password
import uuid

def create_test_users():
    db = SessionLocal()
    try:
        # Check tenant using raw SQL
        res = db.execute(text("SELECT id FROM tenants WHERE name='Demo Transport Co'")).fetchone()
        if not res:
            tenant_id = str(uuid.uuid4())
            db.execute(text("""
                INSERT INTO tenants (id, name, domain, is_active, subscription_tier, max_users, settings, created_at, updated_at, is_deleted)
                VALUES (:id, 'Demo Transport Co', 'demo.transport.com', true, 'trial', 10, '{}', now(), now(), false)
            """), {"id": tenant_id})
            print(f"Created Tenant (Raw SQL) ID: {tenant_id}")
        else:
            tenant_id = str(res[0])
            print(f"Found existing Tenant ID: {tenant_id}")
            
        roles_to_create = [
            ("TenantAdmin", "admin@demo.transport.com", "Admin", "User", "password123"),
            ("TransportAdmin", "transport@demo.transport.com", "Transport", "Manager", "password123"),
            ("Accounts", "accounts@demo.transport.com", "Accounts", "Manager", "password123"),
            ("Driver", "driver@demo.transport.com", "Driver", "User", "password123"),
            ("Client", "client@demo.transport.com", "Client", "Customer", "password123"),
        ]
        
        for role_name, email, first, last, pwd in roles_to_create:
            role_res = db.execute(text("SELECT id FROM roles WHERE name=:name"), {"name": role_name}).fetchone()
            if not role_res:
                print(f"Role {role_name} not found! Skipping {email}")
                continue
            role_id = role_res[0]
                
            user_res = db.execute(text("SELECT id FROM users WHERE email=:email"), {"email": email}).fetchone()
            if not user_res:
                user_id = str(uuid.uuid4())
                pwd_hash = hash_password(pwd)
                db.execute(text("""
                    INSERT INTO users (id, email, password_hash, first_name, last_name, tenant_id, is_active, is_verified, failed_login_attempts, created_at, updated_at, is_deleted)
                    VALUES (:id, :email, :hash, :f, :l, :tid, true, true, 0, now(), now(), false)
                """), {
                    "id": user_id, "email": email, "hash": pwd_hash, "f": first, "l": last, "tid": tenant_id
                })
                
                user_role_id = str(uuid.uuid4())
                db.execute(text("""
                    INSERT INTO user_roles (id, user_id, role_id, tenant_id, assigned_at, created_at, updated_at, is_deleted)
                    VALUES (:id, :uid, :rid, :tid, now(), now(), now(), false)
                """), {
                    "id": user_role_id, "uid": user_id, "rid": role_id, "tid": tenant_id
                })
                print(f"Created User: {email} with Role: {role_name}")
            else:
                user_id = user_res[0]
                has_role = db.execute(text("SELECT id FROM user_roles WHERE user_id=:uid AND role_id=:rid"), {"uid": user_id, "rid": role_id}).fetchone()
                if not has_role:
                    user_role_id = str(uuid.uuid4())
                    db.execute(text("""
                        INSERT INTO user_roles (id, user_id, role_id, tenant_id, assigned_at, created_at, updated_at, is_deleted)
                        VALUES (:id, :uid, :rid, :tid, now(), now(), now(), false)
                    """), {
                        "id": user_role_id, "uid": user_id, "rid": role_id, "tid": tenant_id
                    })
                    print(f"Assigned Role {role_name} to existing User: {email}")
                else:
                    print(f"User {email} already exists with Role {role_name}")
                
        db.commit()
        print("Done creating test users (Raw SQL bypass).")
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_users()
