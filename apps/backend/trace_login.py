import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.services.auth_service import AuthService

def test_login_internals():
    db = SessionLocal()
    try:
        service = AuthService(db)
        user, access, refresh, expires = service.authenticate("admin@demo.transport.com", "password123")
        print("Success!", user.email)
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_login_internals()
