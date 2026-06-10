import calendar
from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select, func, case, and_, extract
from sqlalchemy.orm import Session

from app.models.driver import Driver, DriverStatus
from app.models.load import Load, LoadStatus
from app.models.client import Client
from app.models.truck import Truck, TruckStatus


class ReportRepository:
    """Read-only queries for analytics and reporting. Always tenant-scoped."""

    def __init__(self, db: Session, tenant_id: UUID | None = None):
        self.db = db
        self.tenant_id = tenant_id

    # ── Summary ────────────────────────────────────────────────────────────────

    def get_summary(self) -> dict:
        today = date.today()

        # Load counts by status
        status_rows = self.db.execute(
            select(Load.status, func.count().label("cnt"))
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.tenant_id == self.tenant_id,
                )
            )
            .group_by(Load.status)
        ).all()
        by_status = {row.status.value: row.cnt for row in status_rows}
        total_loads = sum(by_status.values())

        # Financial totals from DELIVERED loads
        fin = self.db.execute(
            select(
                func.coalesce(func.sum(Load.freight_amount), 0).label("total_freight"),
                func.coalesce(func.sum(Load.advance_amount), 0).label("total_advance"),
                func.coalesce(
                    func.sum(
                        func.greatest(
                            func.coalesce(Load.freight_amount, 0)
                            - func.coalesce(Load.advance_amount, 0),
                            0,
                        )
                    ),
                    0,
                ).label("total_outstanding"),
            )
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.tenant_id == self.tenant_id,
                    Load.status == LoadStatus.DELIVERED,
                )
            )
        ).one()

        # Truck counts
        active_trucks = self.db.execute(
            select(func.count())
            .select_from(Truck)
            .where(
                and_(
                    Truck.is_deleted == False,
                    Truck.tenant_id == self.tenant_id,
                    Truck.status != TruckStatus.DECOMMISSIONED,
                )
            )
        ).scalar_one()

        available_trucks = self.db.execute(
            select(func.count())
            .select_from(Truck)
            .where(
                and_(
                    Truck.is_deleted == False,
                    Truck.tenant_id == self.tenant_id,
                    Truck.is_available == True,
                    Truck.status == TruckStatus.ACTIVE,
                )
            )
        ).scalar_one()

        # Driver counts
        active_drivers = self.db.execute(
            select(func.count())
            .select_from(Driver)
            .where(
                and_(
                    Driver.is_deleted == False,
                    Driver.tenant_id == self.tenant_id,
                    Driver.status.notin_([DriverStatus.INACTIVE, DriverStatus.BLACKLISTED]),
                )
            )
        ).scalar_one()

        available_drivers = self.db.execute(
            select(func.count())
            .select_from(Driver)
            .where(
                and_(
                    Driver.is_deleted == False,
                    Driver.tenant_id == self.tenant_id,
                    Driver.is_available == True,
                )
            )
        ).scalar_one()

        # This-month stats
        loads_this_month = self.db.execute(
            select(func.count())
            .select_from(Load)
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.tenant_id == self.tenant_id,
                    extract("year", Load.pickup_date) == today.year,
                    extract("month", Load.pickup_date) == today.month,
                )
            )
        ).scalar_one()

        revenue_this_month = self.db.execute(
            select(func.coalesce(func.sum(Load.freight_amount), 0))
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.tenant_id == self.tenant_id,
                    Load.status == LoadStatus.DELIVERED,
                    Load.actual_delivery_date != None,
                    extract("year", Load.actual_delivery_date) == today.year,
                    extract("month", Load.actual_delivery_date) == today.month,
                )
            )
        ).scalar_one()

        return {
            "total_loads": total_loads,
            "by_status": by_status,
            "total_freight": float(fin.total_freight),
            "total_advance": float(fin.total_advance),
            "total_outstanding": float(fin.total_outstanding),
            "active_trucks": active_trucks,
            "available_trucks": available_trucks,
            "active_drivers": active_drivers,
            "available_drivers": available_drivers,
            "loads_this_month": loads_this_month,
            "revenue_this_month": float(revenue_this_month),
        }

    # ── Load trend ─────────────────────────────────────────────────────────────

    def get_load_trend(self, months: int = 12) -> list[dict]:
        """Monthly load counts grouped by pickup_date, last N months."""
        start_date = date.today() - timedelta(days=months * 31)

        rows = self.db.execute(
            select(
                extract("year", Load.pickup_date).label("yr"),
                extract("month", Load.pickup_date).label("mo"),
                func.count().label("total"),
                func.count(
                    case((Load.status == LoadStatus.DELIVERED, 1), else_=None)
                ).label("delivered"),
                func.count(
                    case((Load.status == LoadStatus.CANCELLED, 1), else_=None)
                ).label("cancelled"),
            )
            .where(
                and_(
                    Load.is_deleted == False,
                    Load.tenant_id == self.tenant_id,
                    Load.pickup_date >= start_date,
                )
            )
            .group_by("yr", "mo")
            .order_by("yr", "mo")
        ).all()

        return [
            {
                "period": f"{calendar.month_abbr[int(row.mo)]} {int(row.yr)}",
                "total": row.total,
                "delivered": row.delivered,
                "cancelled": row.cancelled,
            }
            for row in rows
        ]

    # ── Revenue by client ──────────────────────────────────────────────────────

    def get_revenue_by_client(self) -> dict:
        rows = self.db.execute(
            select(
                Client.id.label("client_id"),
                Client.company_name.label("client_name"),
                func.count(Load.id).label("load_count"),
                func.coalesce(func.sum(Load.freight_amount), 0).label("total_freight"),
                func.coalesce(func.sum(Load.advance_amount), 0).label("total_advance"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Load.status == LoadStatus.DELIVERED,
                                func.greatest(
                                    func.coalesce(Load.freight_amount, 0)
                                    - func.coalesce(Load.advance_amount, 0),
                                    0,
                                ),
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("total_outstanding"),
            )
            .join(
                Load,
                and_(
                    Load.client_id == Client.id,
                    Load.is_deleted == False,
                    Load.status != LoadStatus.CANCELLED,
                ),
            )
            .where(
                and_(
                    Client.is_deleted == False,
                    Client.tenant_id == self.tenant_id,
                )
            )
            .group_by(Client.id, Client.company_name)
            .order_by(func.sum(Load.freight_amount).desc())
        ).all()

        by_client = [
            {
                "client_id": str(row.client_id),
                "client_name": row.client_name,
                "load_count": row.load_count,
                "total_freight": float(row.total_freight),
                "total_advance": float(row.total_advance),
                "total_outstanding": float(row.total_outstanding),
            }
            for row in rows
        ]
        return {
            "by_client": by_client,
            "total_freight": sum(c["total_freight"] for c in by_client),
            "total_advance": sum(c["total_advance"] for c in by_client),
            "total_outstanding": sum(c["total_outstanding"] for c in by_client),
        }

    # ── Driver performance ─────────────────────────────────────────────────────

    def get_driver_performance(self) -> list[dict]:
        rows = self.db.execute(
            select(
                Driver.id.label("driver_id"),
                Driver.first_name.label("first_name"),
                Driver.last_name.label("last_name"),
                func.count(Load.id).label("total_trips"),
                func.count(
                    case((Load.status == LoadStatus.DELIVERED, 1), else_=None)
                ).label("trips_completed"),
                func.count(
                    case((Load.status == LoadStatus.CANCELLED, 1), else_=None)
                ).label("trips_cancelled"),
                func.count(
                    case(
                        (
                            and_(
                                Load.status == LoadStatus.DELIVERED,
                                Load.actual_delivery_date != None,
                                Load.expected_delivery_date != None,
                                Load.actual_delivery_date <= Load.expected_delivery_date,
                            ),
                            1,
                        ),
                        else_=None,
                    )
                ).label("on_time"),
            )
            .join(
                Load,
                and_(
                    Load.allocated_driver_id == Driver.id,
                    Load.is_deleted == False,
                ),
            )
            .where(
                and_(
                    Driver.is_deleted == False,
                    Driver.tenant_id == self.tenant_id,
                )
            )
            .group_by(Driver.id, Driver.first_name, Driver.last_name)
            .order_by(func.count(Load.id).desc())
        ).all()

        return [
            {
                "driver_id": str(row.driver_id),
                "driver_name": f"{row.first_name} {row.last_name}",
                "total_trips": row.total_trips,
                "trips_completed": row.trips_completed,
                "trips_cancelled": row.trips_cancelled,
                "on_time_deliveries": row.on_time,
            }
            for row in rows
        ]

    # ── Truck utilization ──────────────────────────────────────────────────────

    def get_truck_utilization(self) -> dict:
        truck_rows = self.db.execute(
            select(
                Truck.id.label("truck_id"),
                Truck.registration_no.label("registration_no"),
                Truck.status.label("status"),
                func.count(Load.id).label("trips_completed"),
            )
            .outerjoin(
                Load,
                and_(
                    Load.allocated_truck_id == Truck.id,
                    Load.is_deleted == False,
                    Load.status == LoadStatus.DELIVERED,
                ),
            )
            .where(
                and_(
                    Truck.is_deleted == False,
                    Truck.tenant_id == self.tenant_id,
                )
            )
            .group_by(Truck.id, Truck.registration_no, Truck.status)
            .order_by(func.count(Load.id).desc())
        ).all()

        trucks = [
            {
                "truck_id": str(row.truck_id),
                "registration_no": row.registration_no,
                "trips_completed": row.trips_completed,
                "status": row.status.value if hasattr(row.status, "value") else str(row.status),
            }
            for row in truck_rows
        ]

        status_rows = self.db.execute(
            select(Truck.status, func.count().label("cnt"))
            .where(
                and_(
                    Truck.is_deleted == False,
                    Truck.tenant_id == self.tenant_id,
                )
            )
            .group_by(Truck.status)
        ).all()
        by_status = {
            (row.status.value if hasattr(row.status, "value") else str(row.status)): row.cnt
            for row in status_rows
        }

        return {"trucks": trucks, "by_status": by_status}
