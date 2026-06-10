from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.report import ReportRepository
from app.schemas.report import (
    ClientRevenueItem,
    DriverPerformanceItem,
    DriverPerformanceResponse,
    LoadStatusCounts,
    LoadTrendPoint,
    LoadTrendResponse,
    RevenueReportResponse,
    SummaryResponse,
    TruckUtilizationItem,
    TruckUtilizationResponse,
)


class ReportService:
    def __init__(self, db: Session, tenant_id: UUID | None = None, is_superadmin: bool = False):
        self.db = db
        self.tenant_id = tenant_id
        self.is_superadmin = is_superadmin
        self.repo = ReportRepository(db, tenant_id)

    def get_summary(self) -> SummaryResponse:
        data = self.repo.get_summary()
        by_status = data["by_status"]
        return SummaryResponse(
            total_loads=data["total_loads"],
            loads_by_status=LoadStatusCounts(
                draft=by_status.get("draft", 0),
                confirmed=by_status.get("confirmed", 0),
                allocated=by_status.get("allocated", 0),
                in_transit=by_status.get("in_transit", 0),
                delivered=by_status.get("delivered", 0),
                cancelled=by_status.get("cancelled", 0),
            ),
            total_freight=data["total_freight"],
            total_advance_collected=data["total_advance"],
            total_outstanding=data["total_outstanding"],
            active_trucks=data["active_trucks"],
            available_trucks=data["available_trucks"],
            active_drivers=data["active_drivers"],
            available_drivers=data["available_drivers"],
            loads_this_month=data["loads_this_month"],
            revenue_this_month=data["revenue_this_month"],
        )

    def get_load_trend(self, months: int = 12) -> LoadTrendResponse:
        data = self.repo.get_load_trend(months)
        return LoadTrendResponse(data=[LoadTrendPoint(**row) for row in data])

    def get_revenue_report(self) -> RevenueReportResponse:
        data = self.repo.get_revenue_by_client()
        return RevenueReportResponse(
            by_client=[ClientRevenueItem(**c) for c in data["by_client"]],
            total_freight=data["total_freight"],
            total_advance=data["total_advance"],
            total_outstanding=data["total_outstanding"],
        )

    def get_driver_performance(self) -> DriverPerformanceResponse:
        data = self.repo.get_driver_performance()
        return DriverPerformanceResponse(
            drivers=[DriverPerformanceItem(**d) for d in data]
        )

    def get_truck_utilization(self) -> TruckUtilizationResponse:
        data = self.repo.get_truck_utilization()
        return TruckUtilizationResponse(
            trucks=[TruckUtilizationItem(**t) for t in data["trucks"]],
            by_status=data["by_status"],
        )
