import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { PaginatedResponse } from '../../trucks/services/truck.service';

export interface Document {
    id: string; // UUID
    tenant_id: string;
    entity_type: 'TRUCK' | 'DRIVER' | 'CLIENT' | 'LOAD';
    entity_id: string;
    document_type: string;
    document_status: 'ACTIVE' | 'EXPIRED' | 'REJECTED' | 'PENDING_VERIFICATION';
    file_name: string;
    file_url?: string;
    file_size_bytes?: number;
    mime_type?: string;
    issue_date?: string;
    expiry_date?: string;
    is_expired: boolean;
    days_until_expiry?: number;
    notes?: string;
    created_at: string;
}

export interface DocumentCreatePayload {
    entity_type: 'TRUCK' | 'DRIVER' | 'CLIENT' | 'LOAD';
    entity_id: string; // or number depending on entity
    document_type: string;
    file_name: string;
    file_url?: string;
    file_size_bytes?: number;
    mime_type?: string;
    issue_date?: string;
    expiry_date?: string;
    notes?: string;
}

@Injectable({
    providedIn: 'root',
})
export class DocumentService {
    private http = inject(HttpClient);

    getDocumentsByEntity(entityPlural: 'trucks' | 'drivers' | 'clients' | 'loads', entityId: number | string): Observable<PaginatedResponse<Document>> {
        return this.http.get<PaginatedResponse<Document>>(`${entityPlural}/${entityId}/documents`);
    }

    addDocumentToEntity(entityPlural: 'trucks' | 'drivers' | 'clients' | 'loads', entityId: number | string, payload: DocumentCreatePayload): Observable<Document> {
        return this.http.post<Document>(`${entityPlural}/${entityId}/documents`, payload);
    }

    deleteDocument(documentId: string): Observable<any> {
        return this.http.delete(`documents/${documentId}`);
    }
}
