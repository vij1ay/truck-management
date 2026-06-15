import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatSliderModule } from '@angular/material/slider';
import { TranslateModule } from '@ngx-translate/core';
import { ImageCroppedEvent, ImageCropperComponent, ImageTransform } from 'ngx-image-cropper';

export interface AvatarCropDialogData {
    imageFile: File;
    /** Crop frame aspect ratio (width / height). Defaults to 1 (square), used for
     * circular avatars. Pass e.g. 4/3 for non-circular gallery photos. */
    aspectRatio?: number;
    /** Whether the crop frame is circular. Defaults to true (avatars/logos);
     * pass false for rectangular gallery photos. */
    roundCropper?: boolean;
}

/**
 * Crop + zoom step shown after picking an image (profile picture, logo, or — with
 * `roundCropper: false`/`aspectRatio: 4/3` — a truck gallery photo). Returns a
 * cropped `Blob` (via `dialogRef.close(blob)`), or `undefined` if cancelled.
 */
@Component({
    selector: 'app-avatar-crop-dialog',
    standalone: true,
    imports: [CommonModule, FormsModule, MatDialogModule, MatButtonModule, MatIconModule, MatSliderModule, TranslateModule, ImageCropperComponent],
    templateUrl: './avatar-crop-dialog.component.html',
    styleUrl: './avatar-crop-dialog.component.scss',
})
export class AvatarCropDialogComponent {
    public zoom = 1;
    public transform: ImageTransform = { scale: this.zoom };
    public croppedBlob: Blob | null = null;

    public readonly aspectRatio: number;
    public readonly roundCropper: boolean;

    constructor(
        public dialogRef: MatDialogRef<AvatarCropDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: AvatarCropDialogData,
    ) {
        this.aspectRatio = data.aspectRatio ?? 1;
        this.roundCropper = data.roundCropper ?? true;
    }

    onZoomChange(value: number): void {
        this.zoom = value;
        this.transform = { ...this.transform, scale: this.zoom };
    }

    onImageCropped(event: ImageCroppedEvent): void {
        this.croppedBlob = event.blob ?? null;
    }

    onSave(): void {
        this.dialogRef.close(this.croppedBlob);
    }

    onCancel(): void {
        this.dialogRef.close();
    }
}
