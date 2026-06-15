import { Component, Input, OnDestroy, OnInit, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { TranslateModule } from '@ngx-translate/core';

import { TruckPhotoService, TruckPhoto } from '../../../features/trucks/services/truck-photo.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';
import { AvatarCropDialogComponent, AvatarCropDialogData } from '../avatar-crop-dialog/avatar-crop-dialog.component';

interface PhotoTile extends TruckPhoto {
    previewUrl: string | null;
}

/**
 * Truck photo gallery — up to 6 photos, each shown as a thumbnail with a delete
 * button, plus an "Add Photo" tile (hidden once the limit is reached). New photos
 * go through AvatarCropDialogComponent for crop/zoom (4:3, non-circular) before
 * upload.
 */
@Component({
    selector: 'app-photo-gallery',
    standalone: true,
    imports: [CommonModule, MatButtonModule, MatIconModule, MatDialogModule, MatProgressSpinnerModule, TranslateModule],
    templateUrl: './photo-gallery.component.html',
    styleUrl: './photo-gallery.component.scss',
})
export class PhotoGalleryComponent implements OnInit, OnDestroy {
    private truckPhotoService = inject(TruckPhotoService);
    private notification = inject(NotificationService);
    private dialog = inject(MatDialog);

    @Input({ required: true }) truckId!: string;

    public readonly maxPhotos = 6;
    public photos: PhotoTile[] = [];
    public loading = false;

    @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

    ngOnInit(): void {
        this.load();
    }

    ngOnDestroy(): void {
        this.revokeAll();
    }

    private revokeAll(): void {
        for (const p of this.photos) {
            if (p.previewUrl) URL.revokeObjectURL(p.previewUrl);
        }
    }

    load(): void {
        this.loading = true;
        this.truckPhotoService.getPhotos(this.truckId).subscribe({
            next: (photos) => {
                this.revokeAll();
                this.photos = photos.map(p => ({ ...p, previewUrl: null }));
                this.loading = false;
                for (const photo of this.photos) {
                    this.truckPhotoService.getPhotoBlobUrl(this.truckId, photo.id).subscribe({
                        next: (url) => photo.previewUrl = url,
                        error: () => { /* leave placeholder */ },
                    });
                }
            },
            error: () => {
                this.loading = false;
                this.notification.showError('Failed to load photos.');
            },
        });
    }

    triggerFileSelect(): void {
        this.fileInput.nativeElement.click();
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];
        input.value = '';
        if (!file) return;

        const dialogRef = this.dialog.open(AvatarCropDialogComponent, {
            width: '480px',
            data: { imageFile: file, aspectRatio: 4 / 3, roundCropper: false } as AvatarCropDialogData,
        });

        dialogRef.afterClosed().subscribe((blob: Blob | undefined) => {
            if (blob) this.upload(blob);
        });
    }

    private upload(blob: Blob): void {
        this.loading = true;
        this.truckPhotoService.uploadPhoto(this.truckId, blob).subscribe({
            next: () => {
                this.notification.showSuccess('Photo added.');
                this.load();
            },
            error: (err) => {
                this.loading = false;
                const message = err?.error?.message || 'Failed to upload photo.';
                this.notification.showError(message);
            },
        });
    }

    confirmRemove(photo: PhotoTile): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Remove Photo',
                message: 'Are you sure you want to remove this photo?',
                isDestructive: true,
            },
        });

        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
            if (confirmed) this.remove(photo);
        });
    }

    private remove(photo: PhotoTile): void {
        this.loading = true;
        this.truckPhotoService.deletePhoto(this.truckId, photo.id).subscribe({
            next: () => {
                this.notification.showSuccess('Photo removed.');
                this.load();
            },
            error: () => {
                this.loading = false;
                this.notification.showError('Failed to remove photo.');
            },
        });
    }
}
