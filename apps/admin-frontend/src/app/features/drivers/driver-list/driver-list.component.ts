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
import { DriverFormComponent } from '../driver-form/driver-form.component';
import { DriverService, Driver } from '../services/driver.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
    selector: 'app-driver-list',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule, DataTableComponent],
    templateUrl: './driver-list.component.html',
    styleUrls: ['./driver-list.component.scss']
})
export class DriverListComponent implements OnInit {
    private driverService = inject(DriverService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);

    public loading = false;
    public drivers: Driver[] = [];
    public totalItems = 0;
    public pageSize = 10;
    public pageIndex = 0;

    public columns: TableColumn[] = [
        { def: 'full_name', header: 'DRIVER.NAME', sortable: false },
        { def: 'phone', header: 'DRIVER.PHONE', sortable: false },
        { def: 'license_no', header: 'DRIVER.LICENSE', sortable: false },
        { def: 'license_class', header: 'DRIVER.CLASS', sortable: false },
        { def: 'license_expiry', header: 'DRIVER.EXPIRY', type: 'date', sortable: false },
        { def: 'base_location', header: 'DRIVER.BASE_LOC', sortable: false },
        { def: 'status', header: 'COMMON.STATUS', type: 'text', sortable: false }
    ];

    public actions: TableAction[] = [
        { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
        {
            icon: 'check_circle',
            label: 'COMMON.MARK_AVAILABLE',
            action: 'available',
            showIf: (row: Driver) => row.status === 'INACTIVE'
        },
        {
            icon: 'cancel',
            label: 'COMMON.MARK_UNAVAILABLE',
            action: 'unavailable',
            showIf: (row: Driver) => row.status === 'AVAILABLE'
        },
        { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
    ];

    ngOnInit(): void {
        this.loadDrivers();
    }

    loadDrivers(): void {
        this.loading = true;
        const page = this.pageIndex + 1;
        this.driverService.getDrivers(page, this.pageSize).subscribe({
            next: (res) => {
                this.drivers = res.items;
                this.totalItems = res.total;
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    onPageChange(event: PageEvent): void {
        this.pageIndex = event.pageIndex;
        this.pageSize = event.pageSize;
        this.loadDrivers();
    }

    onActionClicked(event: { action: string, row: Driver }): void {
        switch (event.action) {
            case 'edit':
                this.openFormDialog(event.row);
                break;
            case 'available':
                this.toggleStatus(event.row.id, true);
                break;
            case 'unavailable':
                this.toggleStatus(event.row.id, false);
                break;
            case 'delete':
                this.confirmDelete(event.row);
                break;
        }
    }

    openFormDialog(driver?: Driver): void {
        const dialogRef = this.dialog.open(DriverFormComponent, {
            width: '640px',
            maxHeight: '90vh',
            disableClose: true,
            data: { driver }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadDrivers();
            }
        });
    }

    toggleStatus(id: string, makeAvailable: boolean): void {
        this.loading = true;
        this.driverService.toggleAvailability(id, makeAvailable).subscribe(() => {
            this.notification.showSuccess(`Driver marked as ${makeAvailable ? 'available' : 'unavailable'}.`);
            this.loadDrivers();
        });
    }

    confirmDelete(driver: Driver): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Delete Driver',
                message: `Are you sure you want to delete driver ${driver.first_name} ${driver.last_name}?`,
                isDestructive: true
            }
        });

        dialogRef.afterClosed().subscribe(confirm => {
            if (confirm) {
                this.driverService.deleteDriver(driver.id).subscribe(() => {
                    this.notification.showSuccess('Driver deleted successfully.');
                    this.loadDrivers();
                });
            }
        });
    }
}
