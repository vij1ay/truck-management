from fastapi import APIRouter, Depends

from app.api.v1 import auth, users, tenants, roles, audit_logs
from app.api.v1 import trucks, drivers, clients, documents
from app.api.v1 import loads
from app.api.v1 import allocations
from app.api.v1 import reports
from app.api.v1 import invoices
from app.api.v1 import portal
from app.dependencies.logging import log_request

router = APIRouter(dependencies=[Depends(log_request)])

router.include_router(auth.router)
router.include_router(users.router)
router.include_router(tenants.router)
router.include_router(roles.router)
router.include_router(audit_logs.router)
router.include_router(trucks.router)
router.include_router(drivers.router)
router.include_router(clients.router)
router.include_router(documents.router)
router.include_router(loads.router)
router.include_router(allocations.loads_sub)
router.include_router(allocations.avail_router)
router.include_router(reports.router)
router.include_router(invoices.router)
router.include_router(portal.router)
