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
import { TenantFilterComponent } from '../../../../shared/components/tenant-filter/tenant-filter.component';
import { UserService, User, UserListResponse } from '../user.service';
import { Tenant } from '../../../../core/services/tenant.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { PermissionService } from '../../../../core/auth/permission.service';
import { UserForm } from '../user-form/user-form';

@Component({
  selector: 'app-user-list',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatDialogModule,
    TranslateModule,
    DataTableComponent,
    TenantFilterComponent
  ],
  templateUrl: './user-list.html',
  styleUrl: './user-list.scss',
})
export class UserList implements OnInit {
  private userService = inject(UserService);
  private dialog = inject(MatDialog);
  private notification = inject(NotificationService);
  private permissionService = inject(PermissionService);

  public loading = false;
  public users: User[] = [];
  public totalItems = 0;
  public pageSize = 10;
  public pageIndex = 0;

  // SuperAdmin sees users across all tenants and can filter/identify by tenant
  public isSuperAdmin = this.permissionService.hasRole('SuperAdmin');
  public tenants: Tenant[] = [];
  public selectedTenant: Tenant | null = null;

  public columns: TableColumn[] = [
    { def: 'avatar', header: '', type: 'avatar', avatarEntityType: 'users', avatarPlaceholderIcon: 'account_circle', sortable: false },
    { def: 'first_name', header: 'First Name', sortable: false },
    { def: 'last_name', header: 'Last Name', sortable: false },
    { def: 'email', header: 'Email', sortable: false },
    {
      def: 'roles',
      header: 'Roles',
      type: 'text',
      sortable: false
    },
    { def: 'is_active', header: 'COMMON.STATUS', type: 'text', sortable: false }
  ];

  public actions: TableAction[] = [
    { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
    {
      icon: 'check_circle',
      label: 'COMMON.ACTIVATE',
      action: 'activate',
      showIf: (row: any) => !row.is_active
    },
    {
      icon: 'cancel',
      label: 'COMMON.DEACTIVATE',
      action: 'deactivate',
      showIf: (row: any) => row.is_active
    },
    { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
  ];

  ngOnInit(): void {
    if (this.isSuperAdmin) {
      // Insert a Tenant column right after Email so results can be told apart
      this.columns.splice(3, 0, { def: 'tenant_name', header: 'Tenant', type: 'text', sortable: false });
    }

    this.loadUsers();
  }

  onTenantsLoaded(tenants: Tenant[]): void {
    this.tenants = tenants;
    // Re-map any already-loaded users now that tenant names are available
    if (this.users.length) {
      this.users = this.users.map(u => this.withTenantName(u));
    }
  }

  onTenantChange(tenant: Tenant | null): void {
    this.selectedTenant = tenant;
    this.pageIndex = 0;
    this.loadUsers();
  }

  private withTenantName(user: User): any {
    const tenant = this.tenants.find(t => t.id === user.tenant_id);
    return { ...user, tenant_name: tenant?.name ?? '—' };
  }

  loadUsers(): void {
    this.loading = true;
    this.userService.getUsers(this.pageIndex + 1, this.pageSize, undefined, undefined, this.selectedTenant?.id).subscribe({
      next: (res: UserListResponse) => {
        // Pre-process roles into a comma separated string for the data table
        this.users = res.items.map((u: User) => {
          const row: any = {
            ...u,
            // We bind the converted string to a virtual 'roles' property we define in the column
            roles_str: u.roles.map((r: any) => r.name).join(', ')
          };
          return this.isSuperAdmin ? this.withTenantName(row) : row;
        });

        // Need to update columns definition to use 'roles_str' instead
        const rolesColumn = this.columns.find(c => c.header === 'Roles');
        if (rolesColumn) rolesColumn.def = 'roles_str';

        this.totalItems = res.total;
        this.loading = false;
      },
      error: () => this.loading = false
    });
  }

  onPageChange(event: PageEvent): void {
    this.pageIndex = event.pageIndex;
    this.pageSize = event.pageSize;
    this.loadUsers();
  }

  onActionClicked(event: { action: string, row: any }): void {
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

  openFormDialog(user?: User): void {
    const dialogRef = this.dialog.open(UserForm, {
      width: '600px',
      disableClose: true,
      data: { user }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.loadUsers();
      }
    });
  }

  toggleStatus(id: string, activate: boolean): void {
    this.loading = true;
    const req = activate ? this.userService.activateUser(id) : this.userService.deactivateUser(id);
    req.subscribe(() => {
      this.notification.showSuccess(`User successfully ${activate ? 'activated' : 'deactivated'}.`);
      this.loadUsers();
    });
  }

  confirmDelete(user: User): void {
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      width: '400px',
      data: {
        title: 'Delete User',
        message: `Are you sure you want to delete ${user.email}?`,
        isDestructive: true
      }
    });

    dialogRef.afterClosed().subscribe(confirm => {
      if (confirm) {
        this.userService.deleteUser(user.id).subscribe(() => {
          this.notification.showSuccess('User deleted successfully.');
          this.loadUsers();
        });
      }
    });
  }
}
