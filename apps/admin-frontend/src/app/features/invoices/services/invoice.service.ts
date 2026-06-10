import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export type InvoiceStatus = 'draft' | 'sent' | 'partial' | 'paid' | 'overdue' | 'cancelled';
export type PaymentMethod = 'dummy' | 'cash' | 'bank_transfer' | 'cheque';

export interface PaymentItem {
    id: string;
    invoice_id: string;
    amount: number;
    payment_date: string;
    payment_method: PaymentMethod;
    reference_no: string | null;
    notes: string | null;
    recorded_by: string | null;
    created_at: string;
}

export interface InvoiceItem {
    id: string;
    tenant_id: string;
    load_id: string | null;
    client_id: string;
    invoice_no: string;
    status: InvoiceStatus;
    issued_date: string;
    due_date: string | null;
    subtotal: number;
    tax_rate: number;
    tax_amount: number;
    total_amount: number;
    paid_amount: number;
    outstanding_amount: number;
    notes: string | null;
    client_name: string | null;
    load_no: string | null;
    payments: PaymentItem[];
    created_at: string;
    updated_at: string;
}

export interface InvoiceListResponse {
    items: InvoiceItem[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface RecordPaymentPayload {
    amount: number;
    payment_date: string;
    payment_method: PaymentMethod;
    notes?: string;
}

@Injectable({ providedIn: 'root' })
export class InvoiceService {
    private http = inject(HttpClient);
    private base = 'invoices';

    getInvoices(page = 1, size = 50, status?: InvoiceStatus, clientId?: string): Observable<InvoiceListResponse> {
        let params = new HttpParams().set('page', page).set('size', size);
        if (status) params = params.set('status', status);
        if (clientId) params = params.set('client_id', clientId);
        return this.http.get<InvoiceListResponse>(this.base, { params });
    }

    getInvoice(id: string): Observable<InvoiceItem> {
        return this.http.get<InvoiceItem>(`${this.base}/${id}`);
    }

    sendInvoice(id: string): Observable<InvoiceItem> {
        return this.http.post<InvoiceItem>(`${this.base}/${id}/send`, {});
    }

    cancelInvoice(id: string): Observable<InvoiceItem> {
        return this.http.post<InvoiceItem>(`${this.base}/${id}/cancel`, {});
    }

    recordPayment(invoiceId: string, payload: RecordPaymentPayload): Observable<PaymentItem> {
        return this.http.post<PaymentItem>(`${this.base}/${invoiceId}/payments`, payload);
    }
}
