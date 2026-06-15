import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface AssignedTruck {
    id: string;
    registration_no: string;
    truck_type: string;
}

export interface Driver {
    id: string;
    tenant_id: string;
    first_name: string;
    last_name: string;
    full_name: string;
    phone: string;
    email?: string;
    employee_id?: string;
    address?: string;
    license_no: string;
    license_class: string;
    license_expiry: string;       // ISO Date String
    status: string;               // AVAILABLE, ON_TRIP, ON_LEAVE, INACTIVE, BLACKLISTED
    is_available: boolean;
    is_license_valid: boolean;
    is_allocatable: boolean;
    base_location?: string;       // Home depot / base
    current_lat?: number;         // GPS latitude  (future)
    current_lon?: number;         // GPS longitude (future)
    assigned_trucks: AssignedTruck[];
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    notes?: string;
    created_at: string;
    updated_at: string;
}

export interface DriverListResponse {
    items: Driver[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface DriverCreatePayload {
    first_name: string;
    last_name: string;
    phone: string;
    email?: string;
    employee_id?: string;
    address?: string;
    license_no: string;
    license_class: string;
    license_expiry: string;
    base_location?: string;
    assigned_truck_ids?: string[];
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    notes?: string;
}

export interface DriverUpdatePayload {
    first_name?: string;
    last_name?: string;
    phone?: string;
    email?: string;
    employee_id?: string;
    address?: string;
    license_expiry?: string;
    base_location?: string;
    assigned_truck_ids?: string[];
    emergency_contact_name?: string;
    emergency_contact_phone?: string;
    notes?: string;
}

export interface DriverLocationPayload {
    current_lat?: number;
    current_lon?: number;
    base_location?: string;
}

@Injectable({
    providedIn: 'root',
})
export class DriverService {
    private http = inject(HttpClient);
    private basePath = 'drivers';

    getDrivers(page = 1, size = 50, status?: string, tenantId?: string): Observable<DriverListResponse> {
        let params = new HttpParams().set('page', page).set('size', size);
        if (status) params = params.set('status', status);
        if (tenantId) params = params.set('tenant_id', tenantId);
        return this.http.get<DriverListResponse>(this.basePath, { params });
    }

    getDriverById(id: string): Observable<Driver> {
        return this.http.get<Driver>(`${this.basePath}/${id}`);
    }

    createDriver(payload: DriverCreatePayload): Observable<Driver> {
        return this.http.post<Driver>(this.basePath, payload);
    }

    updateDriver(id: string, payload: DriverUpdatePayload): Observable<Driver> {
        return this.http.patch<Driver>(`${this.basePath}/${id}`, payload);
    }

    updateLocation(id: string, payload: DriverLocationPayload): Observable<Driver> {
        return this.http.patch<Driver>(`${this.basePath}/${id}/location`, payload);
    }

    toggleAvailability(id: string, isAvailable: boolean): Observable<Driver> {
        return this.http.post<Driver>(`${this.basePath}/${id}/toggle-availability`, { is_available: isAvailable });
    }

    deleteDriver(id: string): Observable<any> {
        return this.http.delete(`${this.basePath}/${id}`);
    }
}
