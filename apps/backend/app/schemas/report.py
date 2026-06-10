from pydantic import BaseModel


class LoadStatusCounts(BaseModel):
    draft: int = 0
    confirmed: int = 0
    allocated: int = 0
    in_transit: int = 0
    delivered: int = 0
    cancelled: int = 0


class SummaryResponse(BaseModel):
    total_loads: int
    loads_by_status: LoadStatusCounts
    total_freight: float
    total_advance_collected: float
    total_outstanding: float
    active_trucks: int
    available_trucks: int
    active_drivers: int
    available_drivers: int
    loads_this_month: int
    revenue_this_month: float


class LoadTrendPoint(BaseModel):
    period: str  # e.g. "Apr 2026"
    total: int
    delivered: int
    cancelled: int


class LoadTrendResponse(BaseModel):
    data: list[LoadTrendPoint]


class ClientRevenueItem(BaseModel):
    client_id: str
    client_name: str
    total_freight: float
    total_advance: float
    total_outstanding: float
    load_count: int


class RevenueReportResponse(BaseModel):
    by_client: list[ClientRevenueItem]
    total_freight: float
    total_advance: float
    total_outstanding: float


class DriverPerformanceItem(BaseModel):
    driver_id: str
    driver_name: str
    total_trips: int
    trips_completed: int
    trips_cancelled: int
    on_time_deliveries: int


class DriverPerformanceResponse(BaseModel):
    drivers: list[DriverPerformanceItem]


class TruckUtilizationItem(BaseModel):
    truck_id: str
    registration_no: str
    trips_completed: int
    status: str


class TruckUtilizationResponse(BaseModel):
    trucks: list[TruckUtilizationItem]
    by_status: dict[str, int]
