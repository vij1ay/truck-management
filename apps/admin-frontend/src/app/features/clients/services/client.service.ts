import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PaginatedResponse } from '../../trucks/services/truck.service';

export interface Client {
    id: number;
    tenant_id?: string;
    company_name: string;
    contact_person: string;
    email: string;
    phone: string;
    gst_no: string;
    address: string;
    status: string; // ACTIVE, INACTIVE
    has_avatar?: boolean;
    created_at: string;
    /** Portal-user account linked to this client (company), if any. */
    user_id: string | null;
}

export interface ClientCreatePayload {
    company_name: string;
    contact_person: string;
    email: string;
    phone: string;
    gst_no: string;
    address: string;
}

export interface ClientUpdatePayload {
    company_name?: string;
    contact_person?: string;
    email?: string;
    phone?: string;
    gst_no?: string;
    address?: string;
    status?: string;
}

@Injectable({
    providedIn: 'root',
})
export class ClientService {
    private http = inject(HttpClient);
    private basePath = 'clients';

    getClients(page: number = 1, size: number = 10, isActive?: boolean, tenantId?: string): Observable<PaginatedResponse<Client>> {
        let params = new HttpParams()
            .set('page', page.toString())
            .set('size', size.toString());

        if (isActive !== undefined) {
            params = params.set('is_active', isActive.toString());
        }
        if (tenantId) {
            params = params.set('tenant_id', tenantId);
        }

        return this.http.get<PaginatedResponse<Client>>(this.basePath, { params });
    }

    getClientById(id: number): Observable<Client> {
        return this.http.get<Client>(`${this.basePath}/${id}`);
    }

    createClient(payload: ClientCreatePayload): Observable<Client> {
        return this.http.post<Client>(this.basePath, payload);
    }

    updateClient(id: number, payload: ClientUpdatePayload): Observable<Client> {
        return this.http.put<Client>(`${this.basePath}/${id}`, payload);
    }

    deleteClient(id: number): Observable<any> {
        return this.http.delete(`${this.basePath}/${id}`);
    }

    /** Link this client to an existing portal (Client-role) account by email —
     * how a shipper already registered with another tenant gains a relationship
     * with this tenant too. */
    linkPortalAccount(id: number | string, email: string): Observable<Client> {
        return this.http.post<Client>(`${this.basePath}/${id}/link-portal-account`, { email });
    }

    unlinkPortalAccount(id: number | string): Observable<Client> {
        return this.http.delete<Client>(`${this.basePath}/${id}/link-portal-account`);
    }
}
