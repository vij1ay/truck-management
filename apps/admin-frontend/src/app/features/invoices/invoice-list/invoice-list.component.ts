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
    ],
    templateUrl: './invoice-list.component.html',
    styleUrl: './invoice-list.component.scss',
})
export class InvoiceListComponent implements OnInit {
    private invoiceService = inject(InvoiceService);
    private router = inject(Router);
    private notification = inject(NotificationService);

    invoices = signal<InvoiceItem[]>([]);
    total = signal(0);
    loading = signal(false);

    page = 1;
    pageSize = 50;
    statusFilter: InvoiceStatus | '' = '';

    readonly displayedColumns = ['invoice_no', 'client_name', 'load_no', 'issued_date', 'total_amount', 'paid_amount', 'outstanding_amount', 'status', 'actions'];

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
        this.load();
    }

    load(): void {
        this.loading.set(true);
        this.invoiceService.getInvoices(this.page, this.pageSize, this.statusFilter || undefined).subscribe({
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
