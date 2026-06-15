import { Component, Inject, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { DocumentService } from '../../documents/services/document.service';
import { NotificationService } from '../../../core/services/notification.service';

export interface PodUploadDialogData {
    loadId: string;
    loadNo: string;
}

@Component({
    selector: 'app-pod-upload-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatProgressSpinnerModule,
    ],
    template: `
<h2 mat-dialog-title>Upload Proof of Delivery</h2>
<p class="dialog-subtitle" style="padding: 0 24px; margin: -8px 0 16px; color: rgba(0,0,0,.54)">
  Load: <strong>{{ data.loadNo }}</strong>
</p>

<mat-dialog-content>
  <form [formGroup]="form" style="display: flex; flex-direction: column; gap: 12px; min-width: 420px;">

    <mat-form-field appearance="outline">
      <mat-label>File Name</mat-label>
      <input matInput formControlName="file_name" placeholder="e.g. pod-signed.pdf">
      <mat-error *ngIf="form.get('file_name')?.hasError('required')">Required</mat-error>
    </mat-form-field>

    <mat-form-field appearance="outline">
      <mat-label>File URL</mat-label>
      <input matInput formControlName="file_url" placeholder="https://...">
      <mat-hint>Link to the uploaded POD document</mat-hint>
    </mat-form-field>

    <mat-form-field appearance="outline">
      <mat-label>Notes (optional)</mat-label>
      <textarea matInput formControlName="notes" rows="2"></textarea>
    </mat-form-field>

  </form>
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button mat-dialog-close [disabled]="loading">Cancel</button>
  <button mat-raised-button color="primary" (click)="upload()" [disabled]="form.invalid || loading">
    <span *ngIf="!loading">Upload</span>
    <mat-spinner *ngIf="loading" diameter="20" style="display: inline-block;"></mat-spinner>
  </button>
</mat-dialog-actions>
    `,
})
export class PodUploadDialogComponent {
    private documentService = inject(DocumentService);
    private notification = inject(NotificationService);
    private fb = inject(FormBuilder);

    public loading = false;
    public form: FormGroup = this.fb.group({
        file_name: ['', Validators.required],
        file_url: [''],
        notes: [''],
    });

    constructor(
        public dialogRef: MatDialogRef<PodUploadDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: PodUploadDialogData
    ) { }

    upload(): void {
        if (this.form.invalid) return;

        this.loading = true;
        const payload = {
            entity_type: 'load',
            entity_id: this.data.loadId,
            document_type: 'pod',
            file_name: this.form.value.file_name,
            file_url: this.form.value.file_url || undefined,
            notes: this.form.value.notes || undefined,
        } as any;

        this.documentService.addDocumentToEntity('loads', this.data.loadId, payload).subscribe({
            next: () => {
                this.notification.showSuccess('Proof of delivery uploaded.');
                this.dialogRef.close(true);
            },
            error: () => this.loading = false,
        });
    }
}
