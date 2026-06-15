import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatSelectModule } from '@angular/material/select';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { FormsModule } from '@angular/forms';

import { InvoiceService, InvoiceItem, InvoiceStatus } from '../services/invoice.service';
import { NotificationService } from '../../../core/services/notification.service';
import { PermissionService } from '../../../core/auth/permission.service';
import { Tenant } from '../../../core/services/tenant.service';
import { TenantFilterComponent } from '../../../shared/components/tenant-filter/tenant-filter.component';
import { downloadBlob } from '../../../shared/utils/download.util';

@Component({
    selector: 'app-invoice-list',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatTableModule,
        MatPaginatorModule,
        MatSelectModule,
        MatFormFieldModule,
        MatProgressSpinnerModule,
        TenantFilterComponent,
    ],
    templateUrl: './invoice-list.component.html',
    styleUrl: './invoice-list.component.scss',
})
export class InvoiceListComponent implements OnInit {
    private invoiceService = inject(InvoiceService);
    private router = inject(Router);
    private notification = inject(NotificationService);
    private permissionService = inject(PermissionService);

    invoices = signal<InvoiceItem[]>([]);
    total = signal(0);
    loading = signal(false);

    page = 1;
    pageSize = 50;
    statusFilter: InvoiceStatus | '' = '';

    // SuperAdmin sees invoices across all tenants and can filter/identify by tenant
    isSuperAdmin = this.permissionService.hasRole('SuperAdmin');
    tenants: Tenant[] = [];
    selectedTenant: Tenant | null = null;

    displayedColumns = ['invoice_no', 'client_name', 'load_no', 'issued_date', 'total_amount', 'paid_amount', 'outstanding_amount', 'status', 'actions'];

    readonly statusOptions: { value: InvoiceStatus | ''; label: string }[] = [
        { value: '', label: 'All' },
        { value: 'draft', label: 'Draft' },
        { value: 'sent', label: 'Sent' },
        { value: 'partial', label: 'Partial' },
        { value: 'paid', label: 'Paid' },
        { value: 'overdue', label: 'Overdue' },
        { value: 'cancelled', label: 'Cancelled' },
    ];

    ngOnInit(): void {
        if (this.isSuperAdmin) {
            // Insert a Tenant column right after the invoice number so results can be told apart
            this.displayedColumns.splice(1, 0, 'tenant_name');
        }

        this.load();
    }

    onTenantsLoaded(tenants: Tenant[]): void {
        this.tenants = tenants;
    }

    onTenantChange(tenant: Tenant | null): void {
        this.selectedTenant = tenant;
        this.page = 1;
        this.load();
    }

    /** Look up a tenant's display name for the SuperAdmin "Tenant" column. */
    tenantName(tenantId: string): string {
        return this.tenants.find(t => t.id === tenantId)?.name ?? '—';
    }

    load(): void {
        this.loading.set(true);
        this.invoiceService.getInvoices(this.page, this.pageSize, this.statusFilter || undefined, undefined, this.selectedTenant?.id).subscribe({
            next: (res) => {
                this.invoices.set(res.items);
                this.total.set(res.total);
                this.loading.set(false);
            },
            error: () => {
                this.notification.showError('Failed to load invoices');
                this.loading.set(false);
            },
        });
    }

    onPageChange(e: PageEvent): void {
        this.page = e.pageIndex + 1;
        this.pageSize = e.pageSize;
        this.load();
    }

    onStatusChange(): void {
        this.page = 1;
        this.load();
    }

    openDetail(inv: InvoiceItem): void {
        this.router.navigate(['/invoices', inv.id]);
    }

    downloadPdf(inv: InvoiceItem, event: Event): void {
        event.stopPropagation();
        this.invoiceService.downloadPdf(inv.id).subscribe({
            next: (blob) => downloadBlob(blob, `${inv.invoice_no}.pdf`),
            error: () => this.notification.showError('Failed to download invoice PDF'),
        });
    }

    formatCurrency(value: number): string {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    }

    statusClass(status: string): string {
        const map: Record<string, string> = {
            draft: 'status-draft', sent: 'status-sent', partial: 'status-partial',
            paid: 'status-paid', overdue: 'status-overdue', cancelled: 'status-cancelled',
        };
        return map[status] ?? '';
    }
}
