import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { TranslateModule } from '@ngx-translate/core';
import { PageEvent } from '@angular/material/paginator';

import { DataTableComponent, TableColumn, TableAction } from '../../../../shared/components/data-table/data-table.component';
import { TenantFilterComponent } from '../../../../shared/components/tenant-filter/tenant-filter.component';
import { AuditLogService, AuditLogItem, EventCategory } from '../audit-log.service';
import { AuditLogDetailDialogComponent } from '../audit-log-detail-dialog/audit-log-detail-dialog.component';
import { NotificationService } from '../../../../core/services/notification.service';
import { PermissionService } from '../../../../core/auth/permission.service';
import { Tenant } from '../../../../core/services/tenant.service';

@Component({
    selector: 'app-audit-log-list',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatDatepickerModule,
        MatNativeDateModule,
        TranslateModule,
        DataTableComponent,
        TenantFilterComponent,
    ],
    templateUrl: './audit-log-list.component.html',
    styleUrl: './audit-log-list.component.scss',
})
export class AuditLogListComponent implements OnInit {
    private auditLogService = inject(AuditLogService);
    private notification = inject(NotificationService);
    private dialog = inject(MatDialog);
    private permissionService = inject(PermissionService);

    public loading = false;
    public logs: AuditLogItem[] = [];
    public totalItems = 0;
    public pageSize = 25;
    public pageIndex = 0;

    // Filters
    public eventCategory: EventCategory | '' = '';
    public eventType = '';
    public startDate: Date | null = null;
    public endDate: Date | null = null;

    // SuperAdmin sees logs across all tenants and can filter/identify by tenant
    public isSuperAdmin = this.permissionService.hasRole('SuperAdmin');
    public tenants: Tenant[] = [];
    public selectedTenant: Tenant | null = null;

    public readonly categoryOptions: { value: EventCategory | ''; label: string }[] = [
        { value: '', label: 'All Categories' },
        { value: 'auth', label: 'Auth' },
        { value: 'user_mgmt', label: 'User Management' },
        { value: 'role_mgmt', label: 'Role Management' },
        { value: 'tenant_mgmt', label: 'Tenant Management' },
    ];

    public columns: TableColumn[] = [
        { def: 'created_at', header: 'Time', type: 'datetime', sortable: false },
        { def: 'user_email', header: 'User', sortable: false },
        { def: 'event_type', header: 'Event', sortable: false },
        { def: 'event_category', header: 'Category', sortable: false },
        { def: 'resource_type', header: 'Resource', sortable: false },
        { def: 'resource_id', header: 'Resource ID', sortable: false },
    ];

    public actions: TableAction[] = [
        { icon: 'visibility', label: 'View Details', action: 'view' },
    ];

    ngOnInit(): void {
        if (this.isSuperAdmin) {
            // Insert a Tenant column right after the timestamp so results can be told apart
            this.columns.splice(1, 0, { def: 'tenant_name', header: 'Tenant', type: 'text', sortable: false });
        }

        this.load();
    }

    onTenantsLoaded(tenants: Tenant[]): void {
        this.tenants = tenants;
        if (this.logs.length) {
            this.logs = this.logs.map(l => this.withTenantName(l));
        }
    }

    onTenantChange(tenant: Tenant | null): void {
        this.selectedTenant = tenant;
        this.pageIndex = 0;
        this.load();
    }

    private withTenantName(log: AuditLogItem): any {
        const tenant = this.tenants.find(t => t.id === log.tenant_id);
        return { ...log, tenant_name: tenant?.name ?? '—' };
    }

    load(): void {
        this.loading = true;
        this.auditLogService.getLogs(this.pageIndex + 1, this.pageSize, {
            event_category: this.eventCategory || undefined,
            event_type: this.eventType || undefined,
            start_date: this.toIsoStart(this.startDate),
            end_date: this.toIsoEnd(this.endDate),
            tenant_id: this.selectedTenant?.id,
        }).subscribe({
            next: (res) => {
                this.logs = this.isSuperAdmin ? res.items.map(l => this.withTenantName(l)) : res.items;
                this.totalItems = res.total;
                this.loading = false;
            },
            error: () => {
                this.notification.showError('Failed to load audit logs');
                this.loading = false;
            },
        });
    }

    onPageChange(event: PageEvent): void {
        this.pageIndex = event.pageIndex;
        this.pageSize = event.pageSize;
        this.load();
    }

    onFilterChange(): void {
        this.pageIndex = 0;
        this.load();
    }

    hasActiveFilters(): boolean {
        return !!(this.eventCategory || this.eventType || this.startDate || this.endDate);
    }

    clearFilters(): void {
        this.eventCategory = '';
        this.eventType = '';
        this.startDate = null;
        this.endDate = null;
        this.onFilterChange();
    }

    onActionClicked(event: { action: string; row: AuditLogItem }): void {
        if (event.action === 'view') {
            this.dialog.open(AuditLogDetailDialogComponent, {
                width: '600px',
                data: event.row,
            });
        }
    }

    /** Start-of-day ISO string for the "From" date filter. */
    private toIsoStart(d: Date | null): string | undefined {
        if (!d) return undefined;
        const start = new Date(d);
        start.setHours(0, 0, 0, 0);
        return start.toISOString();
    }

    /** End-of-day ISO string for the "To" date filter. */
    private toIsoEnd(d: Date | null): string | undefined {
        if (!d) return undefined;
        const end = new Date(d);
        end.setHours(23, 59, 59, 999);
        return end.toISOString();
    }
}
