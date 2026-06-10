import { Component, Inject, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { LoadService, LoadItem } from '../services/load.service';
import { NotificationService } from '../../../core/services/notification.service';

export interface AllocateDialogData {
    load: LoadItem;
}

@Component({
    selector: 'app-allocate-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatProgressSpinnerModule
    ],
    template: `
<h2 mat-dialog-title>Assign Truck & Driver</h2>
<p class="dialog-subtitle" style="padding: 0 24px; margin: -8px 0 16px; color: rgba(0,0,0,.54)">
  Load: <strong>{{ data.load.load_no }}</strong> &nbsp;|&nbsp;
  {{ data.load.origin }} → {{ data.load.destination }} &nbsp;|&nbsp;
  {{ data.load.pickup_date | date:'mediumDate' }}
</p>

<mat-dialog-content>
  <form [formGroup]="form" style="display: flex; flex-direction: column; gap: 12px; min-width: 480px;">

    <mat-form-field appearance="outline">
      <mat-label>Select Truck</mat-label>
      <mat-select formControlName="truck_id">
        <mat-option *ngFor="let t of availableTrucks" [value]="t.id">
          {{ t.registration_no }} — {{ t.truck_type }} ({{ t.capacity_tons }}T)
        </mat-option>
        <mat-option *ngIf="availableTrucks.length === 0" disabled>No trucks available for this date</mat-option>
      </mat-select>
      <mat-error *ngIf="form.get('truck_id')?.hasError('required')">Required</mat-error>
    </mat-form-field>

    <mat-form-field appearance="outline">
      <mat-label>Select Driver</mat-label>
      <mat-select formControlName="driver_id">
        <mat-option *ngFor="let d of availableDrivers" [value]="d.id">
          {{ d.first_name }} {{ d.last_name }} — Lic: {{ d.license_class }}
        </mat-option>
        <mat-option *ngIf="availableDrivers.length === 0" disabled>No drivers available for this date</mat-option>
      </mat-select>
      <mat-error *ngIf="form.get('driver_id')?.hasError('required')">Required</mat-error>
    </mat-form-field>

    <mat-form-field appearance="outline">
      <mat-label>Notes (optional)</mat-label>
      <textarea matInput formControlName="notes" rows="2"></textarea>
    </mat-form-field>

  </form>
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button mat-dialog-close [disabled]="loading">Cancel</button>
  <button mat-raised-button color="primary" (click)="allocate()" [disabled]="form.invalid || loading">
    <span *ngIf="!loading">Assign & Dispatch</span>
    <mat-spinner *ngIf="loading" diameter="20" style="display: inline-block;"></mat-spinner>
  </button>
</mat-dialog-actions>
    `
})
export class AllocateDialogComponent implements OnInit {
    private loadService = inject(LoadService);
    private notification = inject(NotificationService);
    private fb = inject(FormBuilder);

    public form!: FormGroup;
    public loading = false;
    public availableTrucks: any[] = [];
    public availableDrivers: any[] = [];

    constructor(
        public dialogRef: MatDialogRef<AllocateDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: AllocateDialogData
    ) { }

    ngOnInit(): void {
        this.form = this.fb.group({
            truck_id: ['', Validators.required],
            driver_id: ['', Validators.required],
            notes: ['']
        });

        // Load availability for the load's pickup date
        const pickupDate = this.data.load.pickup_date;
        this.loadService.getAvailableTrucks(pickupDate).subscribe({
            next: (res) => this.availableTrucks = res.items || [],
            error: () => { }
        });
        this.loadService.getAvailableDrivers(pickupDate).subscribe({
            next: (res) => this.availableDrivers = res.items || [],
            error: () => { }
        });
    }

    allocate(): void {
        if (this.form.invalid) return;
        this.loading = true;

        this.loadService.allocate(this.data.load.id, {
            truck_id: this.form.value.truck_id,
            driver_id: this.form.value.driver_id,
            pickup_date: this.data.load.pickup_date,
            notes: this.form.value.notes
        }).subscribe({
            next: (res) => {
                this.notification.showSuccess(`Load ${res.load_no} allocated successfully!`);
                this.dialogRef.close(res);
            },
            error: () => this.loading = false
        });
    }
}
