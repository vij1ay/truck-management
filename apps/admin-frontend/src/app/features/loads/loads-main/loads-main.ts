import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatTableModule } from '@angular/material/table';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatNativeDateModule } from '@angular/material/core';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { FormsModule } from '@angular/forms';
import { TranslateModule } from '@ngx-translate/core';
import { Subject, debounceTime, distinctUntilChanged } from 'rxjs';

import { PermissionService } from '../../../core/auth/permission.service';
import { NotificationService } from '../../../core/services/notification.service';
import { Tenant } from '../../../core/services/tenant.service';
import { LoadService, LoadItem } from '../services/load.service';
import { ClientService, Client } from '../../clients/services/client.service';
import { ConfirmDialogComponent } from '../../../shared/components/confirm-dialog/confirm-dialog.component';
import { TenantFilterComponent } from '../../../shared/components/tenant-filter/tenant-filter.component';
import { AllocateDialogComponent } from '../allocate-dialog/allocate-dialog.component';
import { PodUploadDialogComponent } from '../pod-upload-dialog/pod-upload-dialog.component';

@Component({
  selector: 'app-loads-main',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    MatTableModule,
    MatProgressSpinnerModule,
    MatTooltipModule,
    MatDividerModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatNativeDateModule,
    MatPaginatorModule,
    TranslateModule,
    TenantFilterComponent
  ],
  templateUrl: './loads-main.html',
  styleUrl: './loads-main.scss'
})
export class LoadsMain implements OnInit {
  private loadService = inject(LoadService);
  private permissionService = inject(PermissionService);
  private notification = inject(NotificationService);
  private clientService = inject(ClientService);
  private dialog = inject(MatDialog);

  // Role helpers
  public isAdmin = computed(() => this.permissionService.hasAnyRole(['TenantAdmin', 'TransportAdmin', 'SuperAdmin']));
  public isDriver = computed(() => this.permissionService.hasAnyRole(['Driver']) && !this.isAdmin());
  public isSuperAdmin = this.permissionService.hasRole('SuperAdmin');

  // State
  public loads = signal<LoadItem[]>([]);
  public loading = signal(false);

  // Admin board columns
  public adminColumns = ['load_no', 'origin', 'destination', 'pickup_date', 'goods_type', 'status', 'actions'];
  // Driver columns
  public driverColumns = ['load_no', 'origin', 'destination', 'pickup_date', 'status', 'action'];

  // ── Filters & pagination (Admin board only) ───────────────────────────────
  public readonly loadStatuses = ['draft', 'confirmed', 'allocated', 'in_transit', 'delivered', 'cancelled'];
  public clients = signal<Client[]>([]);

  // SuperAdmin tenant filter — see also `onTenantsLoaded`/`onTenantChange`
  public tenants = signal<Tenant[]>([]);
  public selectedTenant = signal<Tenant | null>(null);

  /** Bound to the search input directly (updates immediately as you type). */
  public searchInputValue = signal('');
  /** Debounced value actually sent to the API. */
  public searchTerm = signal('');
  public statusFilter = signal('');
  public clientFilter = signal('');
  public pickupFrom = signal<Date | null>(null);
  public pickupTo = signal<Date | null>(null);

  public pageIndex = signal(0);
  public pageSize = signal(10);
  public totalItems = signal(0);

  private searchInput$ = new Subject<string>();

  ngOnInit(): void {
    if (this.isAdmin()) {
      this.searchInput$.pipe(
        debounceTime(400),
        distinctUntilChanged()
      ).subscribe((term) => {
        this.searchTerm.set(term);
        this.onFilterChange();
      });

      this.clientService.getClients(1, 100, true).subscribe({
        next: (res) => this.clients.set(res.items ?? res.data ?? []),
        error: () => this.clients.set([]),
      });

      if (this.isSuperAdmin) {
        // Insert a Tenant column right after the load number so results can be told apart
        this.adminColumns.splice(1, 0, 'tenant_name');
      }
    }

    this.loadData();
  }

  onTenantsLoaded(tenants: Tenant[]): void {
    this.tenants.set(tenants);
  }

  onTenantChange(tenant: Tenant | null): void {
    this.selectedTenant.set(tenant);
    this.onFilterChange();
  }

  /** Map a load's tenant_id to its tenant name for the SuperAdmin "Tenant" column. */
  tenantName(tenantId: string): string {
    return this.tenants().find(t => t.id === tenantId)?.name ?? '—';
  }

  /** Helper for the date pickers — formats a Date as YYYY-MM-DD. */
  private toDateParam(d: Date | null): string | undefined {
    if (!d) return undefined;
    return d.toISOString().split('T')[0];
  }

  loadData(): void {
    this.loading.set(true);

    if (this.isDriver()) {
      // Drivers see only their allocated tasks (no filters/pagination on this view)
      this.loadService.getLoads({ status: 'allocated', size: 50 }).subscribe({
        next: (res) => {
          this.loads.set(res.items);
          this.loading.set(false);
        },
        error: () => this.loading.set(false)
      });
      return;
    }

    this.loadService.getLoads({
      page: this.pageIndex() + 1,
      size: this.pageSize(),
      status: this.statusFilter(),
      client_id: this.clientFilter(),
      pickup_date_from: this.toDateParam(this.pickupFrom()),
      pickup_date_to: this.toDateParam(this.pickupTo()),
      search: this.searchTerm(),
      tenant_id: this.selectedTenant()?.id,
    }).subscribe({
      next: (res) => {
        this.loads.set(res.items);
        this.totalItems.set(res.total);
        this.loading.set(false);
      },
      error: () => this.loading.set(false)
    });
  }

  // ADMIN: Search box (debounced)
  onSearchInput(value: string): void {
    this.searchInputValue.set(value);
    this.searchInput$.next(value);
  }

  // ADMIN: Any filter (status/client/date) changed — reset to page 1
  onFilterChange(): void {
    this.pageIndex.set(0);
    this.loadData();
  }

  // ADMIN: Paginator page/size changed
  onPageChange(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.loadData();
  }

  hasActiveFilters(): boolean {
    return !!(this.searchTerm() || this.statusFilter() || this.clientFilter() || this.pickupFrom() || this.pickupTo());
  }

  clearFilters(): void {
    this.searchInputValue.set('');
    this.searchTerm.set('');
    this.statusFilter.set('');
    this.clientFilter.set('');
    this.pickupFrom.set(null);
    this.pickupTo.set(null);
    this.onFilterChange();
  }

  // ADMIN: Approve (DRAFT → CONFIRMED)
  confirmLoad(load: LoadItem): void {
    this.loading.set(true);
    this.loadService.transitionStatus(load.id, { to_status: 'confirmed', remarks: 'Approved by admin' }).subscribe({
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

  // ADMIN: Upload Proof of Delivery for a delivered load
  uploadPod(load: LoadItem): void {
    const dialogRef = this.dialog.open(PodUploadDialogComponent, {
      width: '480px',
      disableClose: true,
      data: { loadId: load.id, loadNo: load.load_no }
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
      'draft': 'status-draft',
      'confirmed': 'status-confirmed',
      'allocated': 'status-allocated',
      'in_transit': 'status-transit',
      'delivered': 'status-delivered',
      'cancelled': 'status-cancelled'
    };
    return map[status?.toLowerCase()] || 'status-default';
  }
}
