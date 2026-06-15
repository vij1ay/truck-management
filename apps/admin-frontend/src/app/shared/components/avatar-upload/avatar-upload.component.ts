import { Component, EventEmitter, Input, OnChanges, OnDestroy, Output, SimpleChanges, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { TranslateModule } from '@ngx-translate/core';

import { AvatarService, AvatarEntityType } from '../../../core/services/avatar.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';
import { AvatarCropDialogComponent, AvatarCropDialogData } from '../avatar-crop-dialog/avatar-crop-dialog.component';

/**
 * Profile picture / logo upload widget — shows a circular preview (or placeholder
 * icon), and "Upload"/"Remove" actions. Only usable once the record has been saved
 * (i.e. `entityId` is set) since avatars are attached to an existing record by ID.
 */
@Component({
    selector: 'app-avatar-upload',
    standalone: true,
    imports: [CommonModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule],
    templateUrl: './avatar-upload.component.html',
    styleUrl: './avatar-upload.component.scss',
})
export class AvatarUploadComponent implements OnChanges, OnDestroy {
    private avatarService = inject(AvatarService);
    private notification = inject(NotificationService);
    private dialog = inject(MatDialog);

    @Input({ required: true }) entityType!: AvatarEntityType;
    @Input() entityId: string | null = null;
    @Input() hasAvatar = false;
    /** Placeholder icon shown when there's no avatar (e.g. 'account_circle', 'local_shipping', 'business'). */
    @Input() placeholderIcon = 'account_circle';
    @Input() label = 'Profile Picture';

    @Output() avatarChanged = new EventEmitter<boolean>();

    @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

    public previewUrl: string | null = null;
    public loading = false;

    ngOnChanges(changes: SimpleChanges): void {
        if ((changes['entityId'] || changes['hasAvatar']) && this.entityId && this.hasAvatar) {
            this.loadPreview();
        } else if (changes['hasAvatar'] && !this.hasAvatar) {
            this.clearPreview();
        }
    }

    ngOnDestroy(): void {
        this.clearPreview();
    }

    private loadPreview(): void {
        if (!this.entityId) return;
        this.avatarService.getAvatarBlobUrl(this.entityType, this.entityId).subscribe({
            next: (url) => {
                this.clearPreview();
                this.previewUrl = url;
            },
            error: () => { /* leave placeholder if it can't be fetched */ },
        });
    }

    private clearPreview(): void {
        if (this.previewUrl) {
            URL.revokeObjectURL(this.previewUrl);
            this.previewUrl = null;
        }
    }

    triggerFileSelect(): void {
        this.fileInput.nativeElement.click();
    }

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        const file = input.files?.[0];
        input.value = ''; // allow re-selecting the same file later
        if (!file || !this.entityId) return;

        const dialogRef = this.dialog.open(AvatarCropDialogComponent, {
            width: '420px',
            data: { imageFile: file } as AvatarCropDialogData,
        });

        dialogRef.afterClosed().subscribe((blob: Blob | undefined) => {
            if (blob) {
                this.upload(blob);
            }
        });
    }

    private upload(blob: Blob): void {
        if (!this.entityId) return;
        this.loading = true;
        this.avatarService.uploadAvatar(this.entityType, this.entityId, blob).subscribe({
            next: () => {
                this.hasAvatar = true;
                this.loadPreview();
                this.loading = false;
                this.avatarChanged.emit(true);
                this.notification.showSuccess('Photo updated.');
            },
            error: () => {
                this.loading = false;
                this.notification.showError('Failed to upload photo.');
            },
        });
    }

    confirmRemove(): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Remove Photo',
                message: 'Are you sure you want to remove this photo?',
                isDestructive: true,
            },
        });

        dialogRef.afterClosed().subscribe((confirmed: boolean) => {
            if (confirmed) {
                this.remove();
            }
        });
    }

    private remove(): void {
        if (!this.entityId) return;
        this.loading = true;
        this.avatarService.removeAvatar(this.entityType, this.entityId).subscribe({
            next: () => {
                this.hasAvatar = false;
                this.clearPreview();
                this.loading = false;
                this.avatarChanged.emit(false);
                this.notification.showSuccess('Photo removed.');
            },
            error: () => {
                this.loading = false;
                this.notification.showError('Failed to remove photo.');
            },
        });
    }
}
