import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export type AvatarEntityType = 'users' | 'trucks' | 'clients' | 'tenants';

export interface AvatarUploadResponse {
    has_avatar: boolean;
}

/**
 * Profile picture / logo upload, removal, and retrieval for Users, Trucks, Clients,
 * and Tenants. Avatars are served via authenticated `GET {entityType}/{id}/avatar`
 * endpoints (not plain static URLs) — fetched through HttpClient (so the auth
 * interceptor attaches the bearer token) and rendered as `blob:` object URLs.
 */
@Injectable({ providedIn: 'root' })
export class AvatarService {
    private http = inject(HttpClient);

    uploadAvatar(entityType: AvatarEntityType, id: string, blob: Blob): Observable<AvatarUploadResponse> {
        const formData = new FormData();
        formData.append('file', blob, 'avatar.jpg');
        return this.http.post<AvatarUploadResponse>(`${entityType}/${id}/avatar`, formData);
    }

    removeAvatar(entityType: AvatarEntityType, id: string): Observable<AvatarUploadResponse> {
        return this.http.delete<AvatarUploadResponse>(`${entityType}/${id}/avatar`);
    }

    /** Fetch the avatar image and return a `blob:` object URL for `<img [src]>`. */
    getAvatarBlobUrl(entityType: AvatarEntityType, id: string): Observable<string> {
        return this.http
            .get(`${entityType}/${id}/avatar`, { responseType: 'blob' })
            .pipe(map((blob) => URL.createObjectURL(blob)));
    }
}
