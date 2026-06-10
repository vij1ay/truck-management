import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';

import { InvoiceService, InvoiceItem, RecordPaymentPayload } from '../services/invoice.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
    selector: 'app-payment-dialog',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatSelectModule,
        MatButtonModule,
        MatDatepickerModule,
        MatNativeDateModule,
    ],
    template: `
    <h2 mat-dialog-title>Record Payment — {{ invoice.invoice_no }}</h2>
    <mat-dialog-content>
      <p class="outstanding">
        Outstanding: <strong>{{ formatCurrency(invoice.outstanding_amount) }}</strong>
      </p>
      <form [formGroup]="form" class="payment-form">
        <mat-form-field appearance="outline">
          <mat-label>Amount (₹)</mat-label>
          <input matInput type="number" formControlName="amount" min="0.01" step="0.01" />
          <mat-error *ngIf="form.get('amount')?.hasError('required')">Required</mat-error>
          <mat-error *ngIf="form.get('amount')?.hasError('min')">Must be > 0</mat-error>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Payment Date</mat-label>
          <input matInput [matDatepicker]="dp" formControlName="payment_date" />
          <mat-datepicker-toggle matIconSuffix [for]="dp"></mat-datepicker-toggle>
          <mat-datepicker #dp></mat-datepicker>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Payment Method</mat-label>
          <mat-select formControlName="payment_method">
            <mat-option value="dummy">Dummy (Test)</mat-option>
            <mat-option value="cash">Cash</mat-option>
            <mat-option value="bank_transfer">Bank Transfer</mat-option>
            <mat-option value="cheque">Cheque</mat-option>
          </mat-select>
        </mat-form-field>

        <mat-form-field appearance="outline">
          <mat-label>Notes (optional)</mat-label>
          <textarea matInput formControlName="notes" rows="2"></textarea>
        </mat-form-field>
      </form>
    </mat-dialog-content>
    <mat-dialog-actions align="end">
      <button mat-button (click)="dialogRef.close(false)">Cancel</button>
      <button mat-flat-button color="primary" [disabled]="form.invalid || saving" (click)="submit()">
        {{ saving ? 'Processing…' : 'Record Payment' }}
      </button>
    </mat-dialog-actions>
  `,
    styles: [`
    .outstanding { margin: 0 0 16px; font-size: 0.9rem; }
    .payment-form { display: flex; flex-direction: column; gap: 8px; min-width: 380px; }
  `],
})
export class PaymentDialogComponent {
    dialogRef = inject(MatDialogRef<PaymentDialogComponent>);
    invoice: InvoiceItem = inject(MAT_DIALOG_DATA);
    private invoiceService = inject(InvoiceService);
    private notification = inject(NotificationService);
    private fb = inject(FormBuilder);

    saving = false;

    form = this.fb.group({
        amount: [null as number | null, [Validators.required, Validators.min(0.01)]],
        payment_date: [new Date(), Validators.required],
        payment_method: ['dummy', Validators.required],
        notes: [''],
    });

    formatCurrency(value: number): string {
        return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 0 }).format(value);
    }

    submit(): void {
        if (this.form.invalid) return;
        this.saving = true;

        const d = this.form.value;
        const pd = d.payment_date instanceof Date ? d.payment_date : new Date(d.payment_date!);
        const payload: RecordPaymentPayload = {
            amount: d.amount!,
            payment_date: pd.toISOString().split('T')[0],
            payment_method: d.payment_method as any,
            notes: d.notes || undefined,
        };

        this.invoiceService.recordPayment(this.invoice.id, payload).subscribe({
            next: () => {
                this.notification.showSuccess('Payment recorded successfully');
                this.dialogRef.close(true);
            },
            error: () => {
                this.saving = false;
                this.notification.showError('Failed to record payment');
            },
        });
    }
}
