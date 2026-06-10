import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LoadStatusCounts {
    draft: number;
    confirmed: number;
    allocated: number;
    in_transit: number;
    delivered: number;
    cancelled: number;
}

export interface ReportSummary {
    total_loads: number;
    loads_by_status: LoadStatusCounts;
    total_freight: number;
    total_advance_collected: number;
    total_outstanding: number;
    active_trucks: number;
    available_trucks: number;
    active_drivers: number;
    available_drivers: number;
    loads_this_month: number;
    revenue_this_month: number;
}

export interface LoadTrendPoint {
    period: string;
    total: number;
    delivered: number;
    cancelled: number;
}

export interface LoadTrendResponse {
    data: LoadTrendPoint[];
}

export interface ClientRevenueItem {
    client_id: string;
    client_name: string;
    total_freight: number;
    total_advance: number;
    total_outstanding: number;
    load_count: number;
}

export interface RevenueReportResponse {
    by_client: ClientRevenueItem[];
    total_freight: number;
    total_advance: number;
    total_outstanding: number;
}

export interface DriverPerformanceItem {
    driver_id: string;
    driver_name: string;
    total_trips: number;
    trips_completed: number;
    trips_cancelled: number;
    on_time_deliveries: number;
}

export interface DriverPerformanceResponse {
    drivers: DriverPerformanceItem[];
}

export interface TruckUtilizationItem {
    truck_id: string;
    registration_no: string;
    trips_completed: number;
    status: string;
}

export interface TruckUtilizationResponse {
    trucks: TruckUtilizationItem[];
    by_status: Record<string, number>;
}

@Injectable({ providedIn: 'root' })
export class ReportService {
    private http = inject(HttpClient);
    private endpoint = 'reports';

    getSummary(): Observable<ReportSummary> {
        return this.http.get<ReportSummary>(`${this.endpoint}/summary`);
    }

    getLoadTrend(months = 12): Observable<LoadTrendResponse> {
        const params = new HttpParams().set('months', months);
        return this.http.get<LoadTrendResponse>(`${this.endpoint}/loads/trend`, { params });
    }

    getRevenue(): Observable<RevenueReportResponse> {
        return this.http.get<RevenueReportResponse>(`${this.endpoint}/revenue`);
    }

    getDriverPerformance(): Observable<DriverPerformanceResponse> {
        return this.http.get<DriverPerformanceResponse>(`${this.endpoint}/drivers/performance`);
    }

    getTruckUtilization(): Observable<TruckUtilizationResponse> {
        return this.http.get<TruckUtilizationResponse>(`${this.endpoint}/trucks/utilization`);
    }
}
