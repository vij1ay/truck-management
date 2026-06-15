import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatTableModule } from '@angular/material/table';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { InvoiceService, InvoiceItem } from '../services/invoice.service';
import { PaymentDialogComponent } from '../payment-dialog/payment-dialog.component';
import { NotificationService } from '../../../core/services/notification.service';
import { downloadBlob } from '../../../shared/utils/download.util';

@Component({
    selector: 'app-invoice-detail',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatChipsModule,
        MatDividerModule,
        MatTableModule,
        MatDialogModule,
        MatProgressSpinnerModule,
    ],
    templateUrl: './invoice-detail.component.html',
    styleUrl: './invoice-detail.component.scss',
})
export class InvoiceDetailComponent implements OnInit {
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private invoiceService = inject(InvoiceService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);

    invoice = signal<InvoiceItem | null>(null);
    loading = signal(true);

    readonly paymentColumns = ['payment_date', 'payment_method', 'reference_no', 'amount'];

    ngOnInit(): void {
        const id = this.route.snapshot.paramMap.get('id')!;
        this.load(id);
    }

    load(id: string): void {
        this.loading.set(true);
        this.invoiceService.getInvoice(id).subscribe({
            next: (inv) => { this.invoice.set(inv); this.loading.set(false); },
            error: () => { this.notification.showError('Failed to load invoice'); this.loading.set(false); },
        });
    }

    sendInvoice(): void {
        const inv = this.invoice()!;
        this.invoiceService.sendInvoice(inv.id).subscribe({
            next: (updated) => { this.invoice.set(updated); this.notification.showSuccess('Invoice marked as sent'); },
            error: () => this.notification.showError('Failed to send invoice'),
        });
    }

    openPaymentDialog(): void {
        const inv = this.invoice()!;
        const ref = this.dialog.open(PaymentDialogComponent, {
            width: '480px',
            disableClose: true,
            data: inv,
        });
        ref.afterClosed().subscribe(result => {
            if (result) this.load(inv.id);
        });
    }

    back(): void {
        this.router.navigate(['/invoices']);
    }

    downloadPdf(): void {
        const inv = this.invoice()!;
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
            draft: 'status-draft',
            sent: 'status-sent',
            partial: 'status-partial',
            paid: 'status-paid',
            overdue: 'status-overdue',
            cancelled: 'status-cancelled',
        };
        return map[status] ?? '';
    }
}
