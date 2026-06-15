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
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

import { TruckService, Truck, TruckCreatePayload, TruckUpdatePayload } from '../services/truck.service';
import { NotificationService } from '../../../core/services/notification.service';
import { DocumentManagerComponent } from '../../../shared/components/document-manager/document-manager.component';
import { AvatarUploadComponent } from '../../../shared/components/avatar-upload/avatar-upload.component';
import { PhotoGalleryComponent } from '../../../shared/components/photo-gallery/photo-gallery.component';

export interface TruckFormDialogData {
    truck?: Truck;
}

@Component({
    selector: 'app-truck-form',
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
        TranslateModule,
        DocumentManagerComponent,
        AvatarUploadComponent,
        PhotoGalleryComponent
    ],
    templateUrl: './truck-form.component.html',
    styleUrls: ['./truck-form.component.scss']
})
export class TruckFormComponent implements OnInit {
    private fb = inject(FormBuilder);
    private truckService = inject(TruckService);
    private notification = inject(NotificationService);

    public truckForm!: FormGroup;
    public loading = false;

    public get isEditMode(): boolean { return !!this.data?.truck; }

    // Must match backend TruckType enum values
    public truckTypes = [
        { value: 'flatbed', label: 'Flatbed' },
        { value: 'container', label: 'Container' },
        { value: 'tanker', label: 'Tanker' },
        { value: 'refrigerated', label: 'Refrigerated' },
        { value: 'tipper', label: 'Tipper' },
        { value: 'lowbed', label: 'Low-Bed' },
        { value: 'other', label: 'Other' },
    ];

    // Must match backend OwnershipType enum values
    public ownershipTypes = [
        { value: 'owned', label: 'Owned' },
        { value: 'contract', label: 'Contract' },
        { value: 'leased', label: 'Leased' },
    ];

    public get ownershipType(): string {
        return this.truckForm?.get('ownership_type')?.value ?? '';
    }

    onAvatarChanged(hasAvatar: boolean): void {
        if (this.data.truck) {
            this.data.truck.has_avatar = hasAvatar;
        }
    }

    constructor(
        public dialogRef: MatDialogRef<TruckFormComponent>,
        @Inject(MAT_DIALOG_DATA) public data: TruckFormDialogData
    ) { }

    ngOnInit(): void {
        const t = this.data?.truck;
        this.truckForm = this.fb.group({
            // ── Core ──
            registration_no: [
                { value: t?.registration_no ?? '', disabled: this.isEditMode },
                [Validators.required, Validators.pattern(/^[A-Z0-9\- ]+$/i)]
            ],
            truck_type: [t?.truck_type ?? '', Validators.required],
            ownership_type: [t?.ownership_type ?? 'owned', Validators.required],
            capacity_tons: [t?.capacity_tons ?? null, [Validators.min(0.1), Validators.max(200)]],

            // ── Specs ──
            make: [t?.make ?? ''],
            model: [t?.model ?? ''],
            year: [t?.year ?? null, [Validators.min(1980), Validators.max(new Date().getFullYear() + 1)]],
            color: [t?.color ?? ''],

            // ── Owned ──
            owner_name: [t?.owner_name ?? ''],
            owner_contact: [t?.owner_contact ?? ''],

            // ── Contract ──
            contractor_name: [t?.contractor_name ?? ''],
            contractor_contact: [t?.contractor_contact ?? ''],
            contract_start_date: [t?.contract_start_date ?? ''],
            contract_end_date: [t?.contract_end_date ?? ''],

            // ── Leased ──
            lessor_name: [t?.lessor_name ?? ''],
            lessor_contact: [t?.lessor_contact ?? ''],
            lease_start_date: [t?.lease_start_date ?? ''],
            lease_end_date: [t?.lease_end_date ?? ''],

            notes: [t?.notes ?? ''],
        });
    }

    onSubmit(): void {
        if (this.truckForm.invalid) return;
        this.loading = true;

        const raw = this.truckForm.getRawValue();

        // Helper to format Date objects to YYYY-MM-DD strings
        const fmtDate = (val: any) => {
            if (!val) return undefined;
            if (val instanceof Date) return val.toISOString().split('T')[0];
            return typeof val === 'string' ? val.split('T')[0] : val;
        };

        // Only include fields relevant to the selected ownership type
        const ownerFields = (type: string) => {
            if (type === 'owned') return {
                owner_name: raw.owner_name || undefined,
                owner_contact: raw.owner_contact || undefined,
            };
            if (type === 'contract') return {
                contractor_name: raw.contractor_name || undefined,
                contractor_contact: raw.contractor_contact || undefined,
                contract_start_date: fmtDate(raw.contract_start_date),
                contract_end_date: fmtDate(raw.contract_end_date),
            };
            if (type === 'leased') return {
                lessor_name: raw.lessor_name || undefined,
                lessor_contact: raw.lessor_contact || undefined,
                lease_start_date: fmtDate(raw.lease_start_date),
                lease_end_date: fmtDate(raw.lease_end_date),
            };
            return {};
        };

        if (this.isEditMode) {
            const payload: TruckUpdatePayload = {
                truck_type: raw.truck_type,
                ownership_type: raw.ownership_type,
                capacity_tons: raw.capacity_tons || undefined,
                make: raw.make || undefined,
                model: raw.model || undefined,
                year: raw.year || undefined,
                color: raw.color || undefined,
                notes: raw.notes || undefined,
                ...ownerFields(raw.ownership_type),
            };
            this.truckService.updateTruck(this.data.truck!.id, payload).subscribe({
                next: (res) => { this.notification.showSuccess('Truck updated.'); this.dialogRef.close(res); },
                error: () => this.loading = false
            });
        } else {
            const payload: TruckCreatePayload = {
                registration_no: raw.registration_no,
                truck_type: raw.truck_type,
                ownership_type: raw.ownership_type,
                capacity_tons: raw.capacity_tons || undefined,
                make: raw.make || undefined,
                model: raw.model || undefined,
                year: raw.year || undefined,
                color: raw.color || undefined,
                notes: raw.notes || undefined,
                ...ownerFields(raw.ownership_type),
            };
            this.truckService.createTruck(payload).subscribe({
                next: (res) => { this.notification.showSuccess('Truck registered.'); this.dialogRef.close(res); },
                error: () => this.loading = false
            });
        }
    }
}
