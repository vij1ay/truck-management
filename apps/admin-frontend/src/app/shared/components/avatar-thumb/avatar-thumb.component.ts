import { Component, Input, OnChanges, OnDestroy, SimpleChanges, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

import { AvatarService, AvatarEntityType } from '../../../core/services/avatar.service';

/**
 * Small circular avatar thumbnail for list rows — lazily fetches the image (via
 * AvatarService, authenticated) when `hasAvatar` is true, otherwise shows a
 * placeholder icon.
 */
@Component({
    selector: 'app-avatar-thumb',
    standalone: true,
    imports: [CommonModule, MatIconModule],
    templateUrl: './avatar-thumb.component.html',
    styleUrl: './avatar-thumb.component.scss',
})
export class AvatarThumbComponent implements OnChanges, OnDestroy {
    private avatarService = inject(AvatarService);

    @Input({ required: true }) entityType!: AvatarEntityType;
    @Input({ required: true }) entityId!: string;
    @Input() hasAvatar = false;
    @Input() placeholderIcon = 'account_circle';

    public previewUrl: string | null = null;

    ngOnChanges(changes: SimpleChanges): void {
        if ((changes['entityId'] || changes['hasAvatar']) && this.entityId && this.hasAvatar) {
            this.avatarService.getAvatarBlobUrl(this.entityType, this.entityId).subscribe({
                next: (url) => {
                    this.clear();
                    this.previewUrl = url;
                },
                error: () => { /* fall back to placeholder */ },
            });
        } else if (!this.hasAvatar) {
            this.clear();
        }
    }

    ngOnDestroy(): void {
        this.clear();
    }

    private clear(): void {
        if (this.previewUrl) {
            URL.revokeObjectURL(this.previewUrl);
            this.previewUrl = null;
        }
    }
}
