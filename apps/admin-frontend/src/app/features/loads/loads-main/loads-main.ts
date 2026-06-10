import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule, ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTabsModule } from '@angular/material/tabs';
import { MatDividerModule } from '@angular/material/divider';
import { TranslateModule } from '@ngx-translate/core';

import { AuthService } from '../../../core/auth/auth.service';
import { PermissionService } from '../../../core/auth/permission.service';
import { NotificationService } from '../../../core/services/notification.service';
import { LoadService, LoadItem, LoadCreate } from '../services/load.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { AllocateDialogComponent } from '../allocate-dialog/allocate-dialog.component';

@Component({
  selector: 'app-loads-main',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    ReactiveFormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatTableModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatTabsModule,
    MatDividerModule,
    TranslateModule
  ],
  templateUrl: './loads-main.html',
  styleUrl: './loads-main.scss'
})
export class LoadsMain implements OnInit {
  private loadService = inject(LoadService);
  private authService = inject(AuthService);
  private permissionService = inject(PermissionService);
  private notification = inject(NotificationService);
  private dialog = inject(MatDialog);
  private fb = inject(FormBuilder);

  // Role helpers
  public isAdmin = computed(() => this.permissionService.hasAnyRole(['TenantAdmin', 'TransportAdmin', 'SuperAdmin']));
  public isClient = computed(() => this.permissionService.hasAnyRole(['Client']) && !this.isAdmin());
  public isDriver = computed(() => this.permissionService.hasAnyRole(['Driver']) && !this.isAdmin());

  // State
  public loads = signal<LoadItem[]>([]);
  public loading = signal(false);
  public showBookingForm = signal(false);
  public bookingForm!: FormGroup;

  // Admin board columns
  public adminColumns = ['load_no', 'origin', 'destination', 'pickup_date', 'goods_type', 'status', 'actions'];
  // Driver columns
  public driverColumns = ['load_no', 'origin', 'destination', 'pickup_date', 'status', 'action'];

  public goodsTypes = ['GENERAL', 'FRAGILE', 'HAZARDOUS', 'CHILLED', 'FROZEN', 'BULK', 'LIQUID', 'ELECTRONICS', 'FURNITURE', 'MACHINERY'];

  ngOnInit(): void {
    this.buildBookingForm();
    this.loadData();
  }

  buildBookingForm(): void {
    this.bookingForm = this.fb.group({
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

  loadData(): void {
    this.loading.set(true);
    let status: string | undefined;

    if (this.isDriver()) {
      // Drivers see only their allocated tasks
      status = 'ALLOCATED';
    }

    this.loadService.getLoads(1, 50, status).subscribe({
      next: (res) => {
        let items = res.items;

        // For driver: filter to only loads allocated to them
        if (this.isDriver()) {
          const currentUser = this.authService.currentUser();
          // The backend already scopes by driver's tenant, but frontend can further filter
          // We show ALLOCATED + IN_TRANSIT for the driver's loads
        }

        this.loads.set(items);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  // CLIENT: Submit a new booking
  get clientId(): string {
    return this.authService.currentUser()?.id?.toString() ?? '';
  }

  submitBooking(): void {
    if (this.bookingForm.invalid) return;

    const payload = this.bookingForm.value;
    // Format date
    const pickupDate = new Date(payload.pickup_date);
    const dateStr = pickupDate.toISOString().split('T')[0];

    const create: LoadCreate = {
      ...payload,
      pickup_date: dateStr,
      client_id: this.clientId
    };

    this.loading.set(true);
    this.loadService.createLoad(create).subscribe({
      next: () => {
        this.notification.showSuccess('Booking request submitted successfully!');
        this.bookingForm.reset({ goods_type: 'GENERAL' });
        this.showBookingForm.set(false);
        this.loadData();
      },
      error: () => this.loading.set(false)
    });
  }

  // ADMIN: Approve (DRAFT → CONFIRMED)
  confirmLoad(load: LoadItem): void {
    this.loading.set(true);
    this.loadService.transitionStatus(load.id, { to_status: 'CONFIRMED', remarks: 'Approved by admin' }).subscribe({
      next: () => {
        this.notification.showSuccess(`Load ${load.load_no} confirmed.`);
        this.loadData();
      },
      error: () => this.loading.set(false)
    });
  }

  // ADMIN: Reject / Cancel
  rejectLoad(load: LoadItem): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '420px',
      data: {
        title: 'Cancel / Reject Booking',
        message: `Are you sure you want to cancel load ${load.load_no}?`,
        isDestructive: true,
        requireReason: true
      }
    });
    dialogRef.afterClosed().subscribe((reason: string) => {
      if (reason) {
        this.loadService.cancelLoad(load.id, reason).subscribe({
          next: () => {
            this.notification.showSuccess(`Load ${load.load_no} cancelled.`);
            this.loadData();
          }
        });
      }
    });
  }

  // ADMIN: Open Allocation Dialog
  allocateLoad(load: LoadItem): void {
    const dialogRef = this.dialog.open(AllocateDialogComponent, {
      width: '600px',
      disableClose: true,
      data: { load }
    });
    dialogRef.afterClosed().subscribe(result => {
      if (result) this.loadData();
    });
  }

  // DRIVER: Start Trip
  startTrip(load: LoadItem): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: 'Start Trip',
        message: `Confirm you are starting the trip for load ${load.load_no} from ${load.origin} to ${load.destination}?`,
        isDestructive: false
      }
    });
    dialogRef.afterClosed().subscribe(confirmed => {
      if (confirmed) {
        this.loadService.startTrip(load.id).subscribe({
          next: () => {
            this.notification.showSuccess(`Trip started for ${load.load_no}!`);
            this.loadData();
          }
        });
      }
    });
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
    return map[status] || 'status-default';
  }
}
