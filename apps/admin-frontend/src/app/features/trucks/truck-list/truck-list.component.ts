import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { TranslateModule } from '@ngx-translate/core';
import { PageEvent } from '@angular/material/paginator';

import { DataTableComponent, TableColumn, TableAction } from '../../../shared/components/data-table/data-table.component';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { TenantFilterComponent } from '../../../shared/components/tenant-filter/tenant-filter.component';
import { TruckFormComponent } from '../truck-form/truck-form.component';
import { TruckService, Truck } from '../services/truck.service';
import { Tenant } from '../../../core/services/tenant.service';
import { NotificationService } from '../../../core/services/notification.service';
import { PermissionService } from '../../../core/auth/permission.service';
import { StatusBadgeComponent } from '../../../shared/components/status-badge/status-badge.component';

@Component({
    selector: 'app-truck-list',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule, DataTableComponent, TenantFilterComponent],
    templateUrl: './truck-list.component.html',
    styleUrls: ['./truck-list.component.scss']
})
export class TruckListComponent implements OnInit {
    private truckService = inject(TruckService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);
    private permissionService = inject(PermissionService);

    public loading = false;
    public trucks: Truck[] = [];
    public totalItems = 0;
    public pageSize = 10;
    public pageIndex = 0;

    // SuperAdmin sees trucks across all tenants and can filter/identify by tenant
    public isSuperAdmin = this.permissionService.hasRole('SuperAdmin');
    public tenants: Tenant[] = [];
    public selectedTenant: Tenant | null = null;

    public columns: TableColumn[] = [
        { def: 'avatar', header: '', type: 'avatar', avatarEntityType: 'trucks', avatarPlaceholderIcon: 'local_shipping', sortable: false },
        { def: 'registration_no', header: 'TRUCK.REG_NO', sortable: false },
        { def: 'truck_type', header: 'TRUCK.TYPE', sortable: false },
        { def: 'capacity_tons', header: 'TRUCK.CAPACITY', sortable: false },
        { def: 'status', header: 'COMMON.STATUS', type: 'text', sortable: false },
        { def: 'created_at', header: 'COMMON.CREATED_AT', type: 'datetime', sortable: false }
    ];

    public actions: TableAction[] = [
        { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
        {
            icon: 'check_circle',
            label: 'COMMON.ACTIVATE',
            action: 'activate',
            showIf: (row: Truck) => row.status === 'INACTIVE'
        },
        {
            icon: 'cancel',
            label: 'COMMON.DEACTIVATE',
            action: 'deactivate',
            showIf: (row: Truck) => row.status === 'AVAILABLE' || row.status === 'MAINTENANCE'
        },
        { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
    ];

    ngOnInit(): void {
        if (this.isSuperAdmin) {
            // Insert a Tenant column right after the registration number so results can be told apart
            this.columns.splice(1, 0, { def: 'tenant_name', header: 'Tenant', type: 'text', sortable: false });
        }

        this.loadTrucks();
    }

    onTenantsLoaded(tenants: Tenant[]): void {
        this.tenants = tenants;
        if (this.trucks.length) {
            this.trucks = this.trucks.map(t => this.withTenantName(t));
        }
    }

    onTenantChange(tenant: Tenant | null): void {
        this.selectedTenant = tenant;
        this.pageIndex = 0;
        this.loadTrucks();
    }

    private withTenantName(truck: Truck): any {
        const tenant = this.tenants.find(t => t.id === truck.tenant_id);
        return { ...truck, tenant_name: tenant?.name ?? '—' };
    }

    loadTrucks(): void {
        this.loading = true;
        const skip = this.pageIndex * this.pageSize;
        this.truckService.getTrucks(skip, this.pageSize, undefined, this.selectedTenant?.id).subscribe({
            next: (res) => {
                const items = res.items ?? res.data ?? [];
                this.trucks = this.isSuperAdmin ? items.map(t => this.withTenantName(t)) : items;
                this.totalItems = res.total;
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    onPageChange(event: PageEvent): void {
        this.pageIndex = event.pageIndex;
        this.pageSize = event.pageSize;
        this.loadTrucks();
    }

    onActionClicked(event: { action: string, row: Truck }): void {
        switch (event.action) {
            case 'edit':
                this.openFormDialog(event.row);
                break;
            case 'activate':
                this.toggleStatus(event.row.id, true);
                break;
            case 'deactivate':
                this.toggleStatus(event.row.id, false);
                break;
            case 'delete':
                this.confirmDelete(event.row);
                break;
        }
    }

    openFormDialog(truck?: Truck): void {
        const dialogRef = this.dialog.open(TruckFormComponent, {
            width: '500px',
            disableClose: true,
            data: { truck }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadTrucks();
            }
        });
    }

    toggleStatus(id: string, activate: boolean): void {
        this.loading = true;
        const req = activate ? this.truckService.activateTruck(id) : this.truckService.deactivateTruck(id);
        req.subscribe(() => {
            this.notification.showSuccess(`Truck successfully ${activate ? 'activated' : 'deactivated'}.`);
            this.loadTrucks();
        });
    }

    confirmDelete(truck: Truck): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Delete Truck',
                message: `Are you sure you want to delete truck ${truck.registration_no}? This action cannot be entirely undone.`,
                isDestructive: true
            }
        });

        dialogRef.afterClosed().subscribe(confirm => {
            if (confirm) {
                this.truckService.deleteTruck(truck.id).subscribe(() => {
                    this.notification.showSuccess('Truck deleted successfully.');
                    this.loadTrucks();
                });
            }
        });
    }
}
