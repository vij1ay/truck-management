import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { LoadItem } from '../../loads/services/load.service';
import { InvoiceItem, InvoiceStatus } from '../../invoices/services/invoice.service';

/** An invoice plus which carrier (tenant) it belongs to. */
export interface PortalInvoiceItem extends InvoiceItem {
    carrier_name: string;
}

export interface PortalInvoiceListResponse {
    items: PortalInvoiceItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

/** A shipment plus which carrier (tenant) it belongs to. */
export interface PortalLoadItem extends LoadItem {
    carrier_name: string;
}

export interface PortalLoadListResponse {
    items: PortalLoadItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface ClientProfile {
    id: string;
    tenant_id: string;
    user_id: string | null;
    client_type: string;
    company_name: string;
    contact_person: string | null;
    email: string | null;
    phone: string;
    address: string | null;
    city: string | null;
    state: string | null;
    pincode: string | null;
    is_active: boolean;
}

/** One of the shipper's carrier (tenant) relationships. */
export interface PortalCarrierLink {
    tenant_id: string;
    tenant_name: string;
    client: ClientProfile;
}

export interface PortalProfileResponse {
    carriers: PortalCarrierLink[];
}

export interface PortalShipmentCreate {
    /** Which carrier (tenant) this booking request is for. */
    tenant_id: string;
    origin: string;
    destination: string;
    pickup_date: string;
    pickup_time?: string;
    expected_delivery_date?: string;
    goods_type: string;
    goods_description?: string;
    weight_kg?: number;
    volume_cbm?: number;
    quantity?: number;
    distance_km?: number;
    freight_amount?: number;
    advance_amount?: number;
    truck_preference?: string;
    special_instructions?: string;
    notes?: string;
}

export interface ShipmentHistoryItem {
    id: string;
    load_id: string;
    from_status: string | null;
    to_status: string;
    changed_by: string | null;
    remarks: string | null;
    changed_at: string;
}

export interface ShipmentDocument {
    id: string;
    document_type: string;
    file_name: string;
    file_url: string | null;
    notes: string | null;
    created_at: string;
}

export interface ShipmentDocumentListResponse {
    items: ShipmentDocument[];
    total: number;
}

@Injectable({ providedIn: 'root' })
export class PortalService {
    private http = inject(HttpClient);
    private base = 'portal';

    getMyProfile(): Observable<PortalProfileResponse> {
        return this.http.get<PortalProfileResponse>(`${this.base}/me`);
    }

    getMyShipments(page = 1, size = 50, status?: string): Observable<PortalLoadListResponse> {
        let params = new HttpParams().set('page', page).set('size', size);
        if (status) params = params.set('status', status);
        return this.http.get<PortalLoadListResponse>(`${this.base}/loads`, { params });
    }

    createShipment(payload: PortalShipmentCreate): Observable<LoadItem> {
        return this.http.post<LoadItem>(`${this.base}/loads`, payload);
    }

    getShipment(id: string): Observable<LoadItem> {
        return this.http.get<LoadItem>(`${this.base}/loads/${id}`);
    }

    getShipmentHistory(id: string): Observable<ShipmentHistoryItem[]> {
        return this.http.get<ShipmentHistoryItem[]>(`${this.base}/loads/${id}/history`);
    }

    getShipmentDocuments(id: string): Observable<ShipmentDocumentListResponse> {
        return this.http.get<ShipmentDocumentListResponse>(`${this.base}/loads/${id}/documents`);
    }

    getMyInvoices(page = 1, size = 50, status?: InvoiceStatus): Observable<PortalInvoiceListResponse> {
        let params = new HttpParams().set('page', page).set('size', size);
        if (status) params = params.set('status', status);
        return this.http.get<PortalInvoiceListResponse>(`${this.base}/invoices`, { params });
    }

    downloadInvoicePdf(id: string): Observable<Blob> {
        return this.http.get(`${this.base}/invoices/${id}/pdf`, { responseType: 'blob' });
    }
}
