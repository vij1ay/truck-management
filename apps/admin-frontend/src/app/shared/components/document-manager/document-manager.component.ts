import { Component, Input, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { TranslateModule } from '@ngx-translate/core';

import { DocumentService, Document } from '../../../features/documents/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';
import { ConfirmDialogComponent } from '../confirm-dialog/confirm-dialog.component';
import { StatusBadgeComponent } from '../status-badge/status-badge.component';

@Component({
    selector: 'app-document-manager',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDividerModule, MatDialogModule, TranslateModule, StatusBadgeComponent],
    templateUrl: './document-manager.component.html',
    styleUrls: ['./document-manager.component.scss']
})
export class DocumentManagerComponent implements OnInit {
    @Input({ required: true }) entityType!: 'TRUCK' | 'DRIVER' | 'CLIENT' | 'LOAD';
    @Input({ required: true }) entityId!: number | string;
    @Input({ required: true }) entityPlural!: 'trucks' | 'drivers' | 'clients';

    private documentService = inject(DocumentService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);

    public documents: Document[] = [];
    public loading = false;

    ngOnInit(): void {
        if (this.entityId) {
            this.loadDocuments();
        }
    }

    loadDocuments(): void {
        this.loading = true;
        this.documentService.getDocumentsByEntity(this.entityPlural, this.entityId).subscribe({
            next: (res) => {
                this.documents = res.data ?? [];
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    onUploadClicked(): void {
        // Scaffold for actual file upload dialog handling
        this.notification.showSuccess('Document upload simulation triggered.');

        // In actual implementation, we'd open a dialog that takes a File, uploads to S3, returns the URL,
        // and calls documentService.addDocumentToEntity with the resulting metadata.
    }

    onDelete(doc: Document): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Delete Document',
                message: `Are you sure you want to delete ${doc.file_name}?`,
                isDestructive: true
            }
        });

        dialogRef.afterClosed().subscribe(confirm => {
            if (confirm) {
                this.loading = true;
                this.documentService.deleteDocument(doc.id).subscribe({
                    next: () => {
                        this.notification.showSuccess('Document deleted successfully.');
                        this.loadDocuments();
                    },
                    error: () => this.loading = false
                });
            }
        });
    }
}
