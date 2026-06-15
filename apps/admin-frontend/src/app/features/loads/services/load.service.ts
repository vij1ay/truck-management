import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface LoadItem {
    id: string;
    tenant_id: string;
    load_no: string;
    load_seq_no: number;
    status: string; // DRAFT, CONFIRMED, ALLOCATED, IN_TRANSIT, DELIVERED, CANCELLED
    client_id: string;
    origin: string;
    destination: string;
    distance_km: number | null;
    pickup_date: string;
    pickup_time: string | null;
    expected_delivery_date: string | null;
    actual_delivery_date: string | null;
    goods_type: string;
    goods_description: string | null;
    weight_kg: number | null;
    volume_cbm: number | null;
    quantity: number | null;
    freight_amount: number | null;
    advance_amount: number | null;
    balance_amount: number;
    truck_preference: string | null;
    special_instructions: string | null;
    notes: string | null;
    booked_by: string | null;
    allocated_truck_id: string | null;
    allocated_driver_id: string | null;
    allocated_at: string | null;
    allocated_by: string | null;
    cancelled_by: string | null;
    cancellation_reason: string | null;
    cancelled_at: string | null;
    is_editable: boolean;
    is_deletable: boolean;
    created_at: string;
    updated_at: string;
}

export interface LoadListResponse {
    items: LoadItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface LoadFilters {
    page?: number;
    size?: number;
    status?: string;
    client_id?: string;
    pickup_date_from?: string;
    pickup_date_to?: string;
    search?: string;
    tenant_id?: string;
}

export interface LoadCreate {
    origin: string;
    destination: string;
    pickup_date: string;
    pickup_time?: string;
    expected_delivery_date?: string;
    goods_type: string;
    goods_description?: string;
    weight_kg?: number;
    quantity?: number;
    truck_preference?: string;
    special_instructions?: string;
    notes?: string;
    client_id: string;
}

export interface LoadStatusTransition {
    to_status: string;
    remarks?: string;
}

export interface AllocationData {
    truck_id: string;
    driver_id: string;
    pickup_date: string;
    effective_delivery_date?: string;
    notes?: string;
}

@Injectable({
    providedIn: 'root'
})
export class LoadService {
    private http = inject(HttpClient);
    private endpoint = 'loads';

    getLoads(filters: LoadFilters = {}): Observable<LoadListResponse> {
        let params = new HttpParams();
        Object.entries(filters).forEach(([key, value]) => {
            if (value !== undefined && value !== null && value !== '') {
                params = params.set(key, String(value));
            }
        });
        return this.http.get<LoadListResponse>(this.endpoint, { params });
    }

    getLoad(id: string): Observable<LoadItem> {
        return this.http.get<LoadItem>(`${this.endpoint}/${id}`);
    }

    createLoad(data: LoadCreate): Observable<LoadItem> {
        return this.http.post<LoadItem>(this.endpoint, data);
    }

    updateLoad(id: string, data: Partial<LoadCreate>): Observable<LoadItem> {
        return this.http.patch<LoadItem>(`${this.endpoint}/${id}`, data);
    }

    deleteLoad(id: string): Observable<void> {
        return this.http.delete<void>(`${this.endpoint}/${id}`);
    }

    transitionStatus(id: string, data: LoadStatusTransition): Observable<LoadItem> {
        return this.http.post<LoadItem>(`${this.endpoint}/${id}/transition`, data);
    }

    cancelLoad(id: string, reason: string): Observable<LoadItem> {
        return this.http.post<LoadItem>(`${this.endpoint}/${id}/cancel`, { reason });
    }

    startTrip(id: string): Observable<LoadItem> {
        return this.http.post<LoadItem>(`${this.endpoint}/${id}/start-trip`, {});
    }

    allocate(loadId: string, data: AllocationData): Observable<LoadItem> {
        return this.http.post<LoadItem>(`${this.endpoint}/${loadId}/allocate`, data);
    }

    getAvailableTrucks(pickupDate: string, deliveryDate?: string): Observable<any> {
        let params = new HttpParams().set('pickup_date', pickupDate);
        if (deliveryDate) params = params.set('delivery_date', deliveryDate);
        return this.http.get<any>('allocations/trucks/available', { params });
    }

    getAvailableDrivers(pickupDate: string, deliveryDate?: string): Observable<any> {
        let params = new HttpParams().set('pickup_date', pickupDate);
        if (deliveryDate) params = params.set('delivery_date', deliveryDate);
        return this.http.get<any>('allocations/drivers/available', { params });
    }
}
