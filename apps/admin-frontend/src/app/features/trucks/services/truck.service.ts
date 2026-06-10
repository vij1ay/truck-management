import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Truck {
    id: string;
    registration_no: string;
    truck_type: string;
    ownership_type: string;
    capacity_tons: number;
    make?: string;
    model?: string;
    year?: number;
    color?: string;

    // Owned
    owner_name?: string;
    owner_contact?: string;

    // Contract
    contractor_name?: string;
    contractor_contact?: string;
    contract_start_date?: string;
    contract_end_date?: string;

    // Leased
    lessor_name?: string;
    lessor_contact?: string;
    lease_start_date?: string;
    lease_end_date?: string;

    notes?: string;
    status: string; // e.g., ACTIVE, INACTIVE, IN_MAINTENANCE, DECOMMISSIONED
    is_available: boolean;
    created_at: string;
}

export interface PaginatedResponse<T> {
    data?: T[];
    items?: T[];
    total: number;
    skip?: number;
    page?: number;
    limit?: number;
    size?: number;
}

export interface TruckCreatePayload {
    registration_no: string;
    truck_type: string;
    ownership_type: string;
    capacity_tons?: number;
    make?: string;
    model?: string;
    year?: number;
    color?: string;

    owner_name?: string;
    owner_contact?: string;

    contractor_name?: string;
    contractor_contact?: string;
    contract_start_date?: string;
    contract_end_date?: string;

    lessor_name?: string;
    lessor_contact?: string;
    lease_start_date?: string;
    lease_end_date?: string;

    notes?: string;
}

export interface TruckUpdatePayload {
    truck_type?: string;
    ownership_type?: string;
    capacity_tons?: number;
    make?: string;
    model?: string;
    year?: number;
    color?: string;

    owner_name?: string;
    owner_contact?: string;

    contractor_name?: string;
    contractor_contact?: string;
    contract_start_date?: string;
    contract_end_date?: string;

    lessor_name?: string;
    lessor_contact?: string;
    lease_start_date?: string;
    lease_end_date?: string;

    notes?: string;
}


@Injectable({
    providedIn: 'root',
})
export class TruckService {
    private http = inject(HttpClient);
    private basePath = 'trucks';

    getTrucks(skip: number = 0, limit: number = 10, status?: string): Observable<PaginatedResponse<Truck>> {
        let params = new HttpParams()
            .set('skip', skip.toString())
            .set('limit', limit.toString());

        if (status) {
            params = params.set('status', status);
        }

        return this.http.get<PaginatedResponse<Truck>>(this.basePath, { params });
    }

    getTruckById(id: string): Observable<Truck> {
        return this.http.get<Truck>(`${this.basePath}/${id}`);
    }

    createTruck(payload: TruckCreatePayload): Observable<Truck> {
        return this.http.post<Truck>(this.basePath, payload);
    }

    updateTruck(id: string, payload: TruckUpdatePayload): Observable<Truck> {
        return this.http.put<Truck>(`${this.basePath}/${id}`, payload);
    }

    activateTruck(id: string): Observable<Truck> {
        return this.http.post<Truck>(`${this.basePath}/${id}/activate`, {});
    }

    deactivateTruck(id: string): Observable<Truck> {
        return this.http.post<Truck>(`${this.basePath}/${id}/deactivate`, {});
    }

    deleteTruck(id: string): Observable<any> {
        return this.http.delete(`${this.basePath}/${id}`);
    }
}
