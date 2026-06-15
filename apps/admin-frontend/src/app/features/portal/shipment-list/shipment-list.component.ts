import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { PortalService, PortalCarrierLink, PortalLoadItem } from '../services/portal.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
    selector: 'app-shipment-list',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatTableModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './shipment-list.component.html',
    styleUrl: './shipment-list.component.scss',
})
export class ShipmentListComponent implements OnInit {
    private portalService = inject(PortalService);
    private notification = inject(NotificationService);
    private router = inject(Router);
    private fb = inject(FormBuilder);

    public shipments = signal<PortalLoadItem[]>([]);
    public carriers = signal<PortalCarrierLink[]>([]);
    public loading = signal(false);
    public showBookingForm = signal(false);
    public bookingForm!: FormGroup;

    public readonly columns = ['load_no', 'carrier_name', 'origin', 'destination', 'pickup_date', 'goods_type', 'status', 'action'];
    public readonly goodsTypes = ['GENERAL', 'FRAGILE', 'HAZARDOUS', 'CHILLED', 'FROZEN', 'BULK', 'LIQUID', 'ELECTRONICS', 'FURNITURE', 'MACHINERY'];

    ngOnInit(): void {
        this.buildBookingForm();
        this.loadCarriers();
        this.loadShipments();
    }

    buildBookingForm(): void {
        this.bookingForm = this.fb.group({
            tenant_id: ['', Validators.required],
            origin: ['', [Validators.required, Validators.minLength(2)]],
            destination: ['', [Validators.required, Validators.minLength(2)]],
            pickup_date: ['', Validators.required],
            goods_type: ['GENERAL', Validators.required],
            goods_description: [''],
            weight_kg: [null],
            quantity: [null],
            truck_preference: [''],
            special_instructions: [''],
            notes: ['']
        });
    }

    /** My carrier relationships — used for the booking form's "Carrier" dropdown. */
    loadCarriers(): void {
        this.portalService.getMyProfile().subscribe({
            next: (res) => {
                this.carriers.set(res.carriers);
                // Default-select when there's only one carrier to book with.
                if (res.carriers.length === 1) {
                    this.bookingForm.patchValue({ tenant_id: res.carriers[0].tenant_id });
                }
            },
            error: () => this.carriers.set([]),
        });
    }

    loadShipments(): void {
        this.loading.set(true);
        this.portalService.getMyShipments(1, 50).subscribe({
            next: (res) => {
                this.shipments.set(res.items);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }

    submitBooking(): void {
        if (this.bookingForm.invalid) return;

        const payload = this.bookingForm.value;
        const pickupDate = new Date(payload.pickup_date);
        const dateStr = pickupDate.toISOString().split('T')[0];

        this.loading.set(true);
        this.portalService.createShipment({ ...payload, pickup_date: dateStr }).subscribe({
            next: () => {
                this.notification.showSuccess('Booking request submitted successfully!');
                this.bookingForm.reset({
                    goods_type: 'GENERAL',
                    tenant_id: this.carriers().length === 1 ? this.carriers()[0].tenant_id : '',
                });
                this.showBookingForm.set(false);
                this.loadShipments();
            },
            error: () => this.loading.set(false),
        });
    }

    openShipment(shipment: PortalLoadItem): void {
        this.router.navigate(['/portal/shipments', shipment.id]);
    }

    getStatusColor(status: string): string {
        const map: Record<string, string> = {
            'DRAFT': 'status-draft',
            'CONFIRMED': 'status-confirmed',
            'ALLOCATED': 'status-allocated',
            'IN_TRANSIT': 'status-transit',
            'DELIVERED': 'status-delivered',
            'CANCELLED': 'status-cancelled'
        };
        return map[status?.toUpperCase()] || 'status-default';
    }
}
