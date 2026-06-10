from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.logger import get_logger
from app.dependencies.auth import get_current_user_context, require_roles, CurrentUser
from app.dependencies.database import get_db
from app.schemas.report import (
    SummaryResponse,
    LoadTrendResponse,
    RevenueReportResponse,
    DriverPerformanceResponse,
    TruckUtilizationResponse,
)
from app.services.report_service import ReportService

router = APIRouter(prefix="/reports", tags=["Reports"])
logger = get_logger(__name__)


def get_report_service(
    db: Annotated[Session, Depends(get_db)],
    context: Annotated[CurrentUser, Depends(get_current_user_context)],
) -> ReportService:
    return ReportService(db=db, tenant_id=context.tenant_id, is_superadmin=context.is_superadmin)


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts")
    )],
):
    """Overall KPI summary: load counts, revenue totals, fleet availability."""
    logger.info("Get reports summary")
    return service.get_summary()


@router.get("/loads/trend", response_model=LoadTrendResponse)
async def get_load_trend(
    service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin", "Accounts")
    )],
    months: int = Query(12, ge=1, le=24, description="Number of past months to include"),
):
    """Monthly load volume trend (total, delivered, cancelled)."""
    logger.info(f"Get load trend months={months}")
    return service.get_load_trend(months)


@router.get("/revenue", response_model=RevenueReportResponse)
async def get_revenue_report(
    service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "Accounts")
    )],
):
    """Revenue breakdown per client: freight, advance collected, outstanding balance."""
    logger.info("Get revenue report")
    return service.get_revenue_report()


@router.get("/drivers/performance", response_model=DriverPerformanceResponse)
async def get_driver_performance(
    service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """Driver performance: trips completed, cancelled, on-time deliveries."""
    logger.info("Get driver performance report")
    return service.get_driver_performance()


@router.get("/trucks/utilization", response_model=TruckUtilizationResponse)
async def get_truck_utilization(
    service: Annotated[ReportService, Depends(get_report_service)],
    _: Annotated[object, Depends(
        require_roles("SuperAdmin", "TenantAdmin", "TransportAdmin")
    )],
):
    """Truck utilization: completed trips per truck, fleet status breakdown."""
    logger.info("Get truck utilization report")
    return service.get_truck_utilization()
