import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { TranslateModule } from '@ngx-translate/core';
import { PageEvent } from '@angular/material/paginator';

import { DataTableComponent, TableColumn, TableAction } from '../../../../shared/components/data-table/data-table.component';
import { ConfirmDialogComponent } from '../../../../shared/components/confirm-dialog/confirm-dialog.component';
import { TenantService, Tenant } from '../../../../core/services/tenant.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { TenantForm } from '../tenant-form/tenant-form';

@Component({
  selector: 'app-tenant-list',
  standalone: true,
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule, DataTableComponent],
  templateUrl: './tenant-list.html',
  styleUrl: './tenant-list.scss',
})
export class TenantList implements OnInit {
  private tenantService = inject(TenantService);
  private dialog = inject(MatDialog);
  private notification = inject(NotificationService);

  public loading = false;
  public tenants: Tenant[] = [];
  public totalItems = 0;
  public pageSize = 10;
  public pageIndex = 0;

  public columns: TableColumn[] = [
    { def: 'avatar', header: '', type: 'avatar', avatarEntityType: 'tenants', avatarPlaceholderIcon: 'business', sortable: false },
    { def: 'name', header: 'Name', sortable: false },
    { def: 'domain', header: 'Domain', sortable: false },
    { def: 'subscription_tier', header: 'Tier', sortable: false },
    { def: 'max_users', header: 'User Quota', sortable: false },
    { def: 'is_active', header: 'COMMON.STATUS', type: 'text', sortable: false },
    { def: 'created_at', header: 'COMMON.CREATED_AT', type: 'datetime', sortable: false }
  ];

  public actions: TableAction[] = [
    { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
    { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
  ];

  ngOnInit(): void {
    this.loadTenants();
  }

  loadTenants(): void {
    this.loading = true;
    // Backend pagination is 1-indexed, Material is 0-indexed
    this.tenantService.getTenants(this.pageIndex + 1, this.pageSize).subscribe({
      next: (res) => {
        this.tenants = res.items;
        this.totalItems = res.total;
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.loadTenants();
  }

  onActionClicked(event: { action: string, row: Tenant }): void {
    switch (event.action) {
      case 'edit':
        this.openFormDialog(event.row);
        break;
      case 'delete':
        this.confirmDelete(event.row);
        break;
    }
  }

  openFormDialog(tenant?: Tenant): void {
    const dialogRef = this.dialog.open(TenantForm, {
      width: '600px',
      disableClose: true,
      data: { tenant }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadTenants();
      }
    });
  }

  confirmDelete(tenant: Tenant): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: 'Delete Tenant',
        message: `Are you sure you want to delete tenant ${tenant.name}? This will also delete all associated users and data.`,
        isDestructive: true
      }
    });

    dialogRef.afterClosed().subscribe(confirm => {
      if (confirm) {
        this.tenantService.deleteTenant(tenant.id).subscribe(() => {
          this.notification.showSuccess('Tenant deleted successfully.');
          this.loadTenants();
        });
      }
    });
  }
}
