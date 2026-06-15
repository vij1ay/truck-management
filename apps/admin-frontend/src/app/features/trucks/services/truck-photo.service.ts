import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';

export interface TruckPhoto {
    id: string;
    truck_id: string;
    position: number;
    created_at: string;
}

/**
 * Truck photo gallery (max 6 photos per truck). Photos are served via
 * authenticated `GET trucks/{truckId}/photos/{photoId}` endpoints — fetched
 * through HttpClient (auth interceptor) and rendered as `blob:` object URLs,
 * same pattern as AvatarService.
 */
@Injectable({ providedIn: 'root' })
export class TruckPhotoService {
    private http = inject(HttpClient);

    getPhotos(truckId: string): Observable<TruckPhoto[]> {
        return this.http.get<TruckPhoto[]>(`trucks/${truckId}/photos`);
    }

    uploadPhoto(truckId: string, blob: Blob): Observable<TruckPhoto> {
        const formData = new FormData();
        formData.append('file', blob, 'photo.jpg');
        return this.http.post<TruckPhoto>(`trucks/${truckId}/photos`, formData);
    }

    deletePhoto(truckId: string, photoId: string): Observable<void> {
        return this.http.delete<void>(`trucks/${truckId}/photos/${photoId}`);
    }

    /** Fetch a gallery photo and return a `blob:` object URL for `<img [src]>`. */
    getPhotoBlobUrl(truckId: string, photoId: string): Observable<string> {
        return this.http
            .get(`trucks/${truckId}/photos/${photoId}`, { responseType: 'blob' })
            .pipe(map((blob) => URL.createObjectURL(blob)));
    }
}
