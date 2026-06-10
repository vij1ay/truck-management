import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface Tenant {
    id: string;
    name: string;
    domain: string | null;
    subscription_tier: string;
    max_users: number;
    is_active: boolean;
    created_at: string;
    user_count?: number;
}

export interface TenantListResponse {
    data: Tenant[]; // Note: Backend uses 'items' based on LoadListResponse, let's map it or check
    items: Tenant[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface TenantCreate {
    name: string;
    domain?: string;
    subscription_tier: string;
    max_users: number;
    admin_email: string;
    admin_first_name: string;
    admin_last_name: string;
    admin_password?: string;
}

export interface TenantUpdate {
    name?: string;
    domain?: string;
    subscription_tier?: string;
    max_users?: number;
    is_active?: boolean;
}

@Injectable({
    providedIn: 'root'
})
export class TenantService {
    private http = inject(HttpClient);
    private endpoint = 'tenants';

    getTenants(page: number = 1, size: number = 10, isActive?: boolean): Observable<TenantListResponse> {
        let params = new HttpParams()
            .set('page', page.toString())
            .set('size', size.toString());

        if (isActive !== undefined) {
            params = params.set('is_active', isActive);
        }

        return this.http.get<TenantListResponse>(this.endpoint, { params });
    }

    getTenant(id: string): Observable<Tenant> {
        return this.http.get<Tenant>(`${this.endpoint}/${id}`);
    }

    createTenant(data: TenantCreate): Observable<Tenant> {
        return this.http.post<Tenant>(this.endpoint, data);
    }

    updateTenant(id: string, data: TenantUpdate): Observable<Tenant> {
        return this.http.patch<Tenant>(`${this.endpoint}/${id}`, data);
    }

    deleteTenant(id: string): Observable<void> {
        return this.http.delete<void>(`${this.endpoint}/${id}`);
    }
}
