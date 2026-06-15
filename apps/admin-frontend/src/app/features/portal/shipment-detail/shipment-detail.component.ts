import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { LoadItem } from '../../loads/services/load.service';
import { PortalService, ShipmentHistoryItem, ShipmentDocument } from '../services/portal.service';
import { NotificationService } from '../../../core/services/notification.service';

const DEFAULT_CARRIER_NAME = '—';

@Component({
    selector: 'app-shipment-detail',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatDividerModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './shipment-detail.component.html',
    styleUrl: './shipment-detail.component.scss',
})
export class ShipmentDetailComponent implements OnInit {
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private portalService = inject(PortalService);
    private notification = inject(NotificationService);

    public shipment = signal<LoadItem | null>(null);
    public history = signal<ShipmentHistoryItem[]>([]);
    public documents = signal<ShipmentDocument[]>([]);
    public loading = signal(true);

    /** tenant_id -> carrier (tenant) name, from /portal/me */
    private carrierNames = new Map<string, string>();
    public carrierName = signal<string>(DEFAULT_CARRIER_NAME);

    ngOnInit(): void {
        const id = this.route.snapshot.paramMap.get('id')!;
        this.portalService.getMyProfile().subscribe({
            next: (res) => {
                this.carrierNames = new Map(res.carriers.map(c => [c.tenant_id, c.tenant_name]));
                this.updateCarrierName();
            },
            error: () => {},
        });
        this.load(id);
    }

    private updateCarrierName(): void {
        const tenantId = this.shipment()?.tenant_id;
        this.carrierName.set((tenantId && this.carrierNames.get(tenantId)) || DEFAULT_CARRIER_NAME);
    }

    load(id: string): void {
        this.loading.set(true);
        this.portalService.getShipment(id).subscribe({
            next: (shipment) => {
                this.shipment.set(shipment);
                this.updateCarrierName();
                this.portalService.getShipmentHistory(id).subscribe({
                    next: (history) => {
                        this.history.set(history);
                        this.loading.set(false);
                    },
                    error: () => this.loading.set(false),
                });
                this.portalService.getShipmentDocuments(id).subscribe({
                    next: (res) => this.documents.set(res.items),
                    error: () => this.documents.set([]),
                });
            },
            error: () => {
                this.notification.showError('Failed to load shipment');
                this.loading.set(false);
            },
        });
    }

    back(): void {
        this.router.navigate(['/portal/shipments']);
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
