import { Component, Inject, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

import { DriverService, Driver } from '../services/driver.service';
import { TruckService, Truck } from '../../trucks/services/truck.service';
import { NotificationService } from '../../../core/services/notification.service';
import { DocumentManagerComponent } from '../../../shared/components/document-manager/document-manager.component';

export interface DriverFormDialogData {
    driver?: Driver;
}

@Component({
    selector: 'app-driver-form',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule,
        MatButtonModule,
        MatIconModule,
        MatDividerModule,
        MatProgressSpinnerModule,
        TranslateModule,
        DocumentManagerComponent
    ],
    templateUrl: './driver-form.component.html',
    styleUrls: ['./driver-form.component.scss']
})
export class DriverFormComponent implements OnInit {
    private fb = inject(FormBuilder);
    private driverService = inject(DriverService);
    private truckService = inject(TruckService);
    private notification = inject(NotificationService);

    public driverForm!: FormGroup;
    public loading = false;
    public availableTrucks: Truck[] = [];

    public get isEditMode(): boolean {
        return !!this.data?.driver;
    }

    // License classes — must match backend LicenseClass enum
    public licenseClasses = [
        { value: 'lmv', label: 'LMV – Light Motor Vehicle' },
        { value: 'hmv', label: 'HMV – Heavy Motor Vehicle' },
        { value: 'hgv', label: 'HGV – Heavy Goods Vehicle' },
        { value: 'other', label: 'Other' },
    ];

    constructor(
        public dialogRef: MatDialogRef<DriverFormComponent>,
        @Inject(MAT_DIALOG_DATA) public data: DriverFormDialogData
    ) { }

    ngOnInit(): void {
        const d = this.data?.driver;
        const existingDate = d?.license_expiry ? new Date(d.license_expiry) : null;
        const existingTruckIds = d?.assigned_trucks?.map(t => t.id) || [];

        this.driverForm = this.fb.group({
            // Identity
            first_name: [d?.first_name || '', Validators.required],
            last_name: [d?.last_name || '', Validators.required],
            phone: [d?.phone || '', [Validators.required, Validators.minLength(7)]],
            email: [d?.email || ''],
            employee_id: [d?.employee_id || ''],
            address: [d?.address || ''],

            // License
            license_no: [
                { value: d?.license_no || '', disabled: this.isEditMode },
                Validators.required
            ],
            license_class: [d?.license_class || 'hmv', Validators.required],
            license_expiry: [existingDate, Validators.required],

            // Location
            base_location: [d?.base_location || ''],

            // Truck mapping (multi-select)
            assigned_truck_ids: [existingTruckIds],

            // Emergency contact
            emergency_contact_name: [d?.emergency_contact_name || ''],
            emergency_contact_phone: [d?.emergency_contact_phone || ''],

            // Notes
            notes: [d?.notes || ''],
        });

        // Load available trucks for the multi-select
        this.truckService.getTrucks(0, 200).subscribe({
            next: (res: any) => this.availableTrucks = res.data || res.items || [],
            error: () => { }
        });
    }

    onSubmit(): void {
        if (this.driverForm.invalid) return;
        this.loading = true;

        const raw = this.driverForm.getRawValue();
        const expiryDate: string = (raw.license_expiry instanceof Date)
            ? raw.license_expiry.toISOString().split('T')[0]
            : raw.license_expiry;

        // Helper to omit empty strings/nulls from optional string fields
        const opt = (v: string | null | undefined) => (v && v.trim() !== '') ? v : undefined;

        if (this.isEditMode) {
            const payload: import('../services/driver.service').DriverUpdatePayload = {
                first_name: raw.first_name || undefined,
                last_name: raw.last_name || undefined,
                phone: raw.phone || undefined,
                email: opt(raw.email),
                employee_id: opt(raw.employee_id),
                address: opt(raw.address),
                license_expiry: expiryDate,
                base_location: opt(raw.base_location),
                assigned_truck_ids: raw.assigned_truck_ids?.length ? raw.assigned_truck_ids : undefined,
                emergency_contact_name: opt(raw.emergency_contact_name),
                emergency_contact_phone: opt(raw.emergency_contact_phone),
                notes: opt(raw.notes),
            };
            this.driverService.updateDriver(this.data.driver!.id, payload).subscribe({
                next: (res) => { this.notification.showSuccess('Driver updated.'); this.dialogRef.close(res); },
                error: () => this.loading = false
            });
        } else {
            const payload: import('../services/driver.service').DriverCreatePayload = {
                first_name: raw.first_name,
                last_name: raw.last_name,
                phone: raw.phone,
                email: opt(raw.email),
                employee_id: opt(raw.employee_id),
                address: opt(raw.address),
                license_no: raw.license_no,
                license_class: raw.license_class,
                license_expiry: expiryDate,
                base_location: opt(raw.base_location),
                assigned_truck_ids: raw.assigned_truck_ids?.length ? raw.assigned_truck_ids : undefined,
                emergency_contact_name: opt(raw.emergency_contact_name),
                emergency_contact_phone: opt(raw.emergency_contact_phone),
                notes: opt(raw.notes),
            };
            this.driverService.createDriver(payload).subscribe({
                next: (res) => { this.notification.showSuccess('Driver registered.'); this.dialogRef.close(res); },
                error: () => this.loading = false
            });
        }
    }
}

