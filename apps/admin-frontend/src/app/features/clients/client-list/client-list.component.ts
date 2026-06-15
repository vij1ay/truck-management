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
import { ClientFormComponent } from '../client-form/client-form.component';
import { ClientService, Client } from '../services/client.service';
import { Tenant } from '../../../core/services/tenant.service';
import { NotificationService } from '../../../core/services/notification.service';
import { PermissionService } from '../../../core/auth/permission.service';

@Component({
    selector: 'app-client-list',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule, DataTableComponent, TenantFilterComponent],
    templateUrl: './client-list.component.html',
    styleUrls: ['./client-list.component.scss']
})
export class ClientListComponent implements OnInit {
    private clientService = inject(ClientService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);
    private permissionService = inject(PermissionService);

    public loading = false;
    public clients: Client[] = [];
    public totalItems = 0;
    public pageSize = 10;
    public pageIndex = 0;

    // SuperAdmin sees clients across all tenants and can filter/identify by tenant
    public isSuperAdmin = this.permissionService.hasRole('SuperAdmin');
    public tenants: Tenant[] = [];
    public selectedTenant: Tenant | null = null;

    public columns: TableColumn[] = [
        { def: 'avatar', header: '', type: 'avatar', avatarEntityType: 'clients', avatarPlaceholderIcon: 'business', sortable: false },
        { def: 'company_name', header: 'CLIENT.COMPANY_NAME', sortable: false },
        { def: 'contact_person', header: 'CLIENT.CONTACT_PERSON', sortable: false },
        { def: 'email', header: 'CLIENT.EMAIL', sortable: false },
        { def: 'gst_no', header: 'CLIENT.GST_NO', sortable: false },
        { def: 'status', header: 'COMMON.STATUS', type: 'text', sortable: false },
        { def: 'created_at', header: 'COMMON.CREATED_AT', type: 'datetime', sortable: false }
    ];

    public actions: TableAction[] = [
        { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
        { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
    ];

    ngOnInit(): void {
        if (this.isSuperAdmin) {
            // Insert a Tenant column right after the company name so results can be told apart
            this.columns.splice(1, 0, { def: 'tenant_name', header: 'Tenant', type: 'text', sortable: false });
        }

        this.loadClients();
    }

    onTenantsLoaded(tenants: Tenant[]): void {
        this.tenants = tenants;
        if (this.clients.length) {
            this.clients = this.clients.map(c => this.withTenantName(c));
        }
    }

    onTenantChange(tenant: Tenant | null): void {
        this.selectedTenant = tenant;
        this.pageIndex = 0;
        this.loadClients();
    }

    private withTenantName(c: Client): any {
        const tenant = this.tenants.find(t => t.id === c.tenant_id);
        return { ...c, tenant_name: tenant?.name ?? '—' };
    }

    loadClients(): void {
        this.loading = true;
        const page = this.pageIndex + 1;
        this.clientService.getClients(page, this.pageSize, undefined, this.selectedTenant?.id).subscribe({
            next: (res) => {
                const items = res.items ?? res.data ?? [];
                this.clients = this.isSuperAdmin ? items.map(c => this.withTenantName(c)) : items;
                this.totalItems = res.total;
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    onPageChange(event: PageEvent): void {
        this.pageIndex = event.pageIndex;
        this.pageSize = event.pageSize;
        this.loadClients();
    }

    onActionClicked(event: { action: string, row: Client }): void {
        switch (event.action) {
            case 'edit':
                this.openFormDialog(event.row);
                break;
            case 'delete':
                this.confirmDelete(event.row);
                break;
        }
    }

    openFormDialog(client?: Client): void {
        const dialogRef = this.dialog.open(ClientFormComponent, {
            width: '600px',
            disableClose: true,
            data: { client }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadClients();
            }
        });
    }

    confirmDelete(client: Client): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Delete Client',
                message: `Are you sure you want to delete client ${client.company_name}? This action cannot be entirely undone.`,
                isDestructive: true
            }
        });

        dialogRef.afterClosed().subscribe(confirm => {
            if (confirm) {
                this.clientService.deleteClient(client.id).subscribe(() => {
                    this.notification.showSuccess('Client deleted successfully.');
                    this.loadClients();
                });
            }
        });
    }
}
