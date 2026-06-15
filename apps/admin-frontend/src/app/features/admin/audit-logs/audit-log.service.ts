import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export type EventCategory = 'auth' | 'user_mgmt' | 'role_mgmt' | 'tenant_mgmt';

export interface AuditLogItem {
    id: string;
    tenant_id: string | null;
    user_id: string | null;
    user_email: string | null;
    event_type: string;
    event_category: EventCategory;
    resource_type: string | null;
    resource_id: string | null;
    old_value: Record<string, unknown> | null;
    new_value: Record<string, unknown> | null;
    ip_address: string | null;
    user_agent: string | null;
    extra_data: Record<string, unknown>;
    created_at: string;
}

export interface AuditLogListResponse {
    items: AuditLogItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface AuditLogFilters {
    event_category?: EventCategory | '';
    event_type?: string;
    start_date?: string;
    end_date?: string;
    tenant_id?: string;
}

@Injectable({ providedIn: 'root' })
export class AuditLogService {
    private http = inject(HttpClient);
    private base = 'audit-logs';

    getLogs(page = 1, size = 25, filters: AuditLogFilters = {}): Observable<AuditLogListResponse> {
        let params = new HttpParams().set('page', page).set('size', size);
        if (filters.event_category) params = params.set('event_category', filters.event_category);
        if (filters.event_type) params = params.set('event_type', filters.event_type);
        if (filters.start_date) params = params.set('start_date', filters.start_date);
        if (filters.end_date) params = params.set('end_date', filters.end_date);
        if (filters.tenant_id) params = params.set('tenant_id', filters.tenant_id);
        return this.http.get<AuditLogListResponse>(this.base, { params });
    }
}
