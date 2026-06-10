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
import { ClientFormComponent } from '../client-form/client-form.component';
import { ClientService, Client } from '../services/client.service';
import { NotificationService } from '../../../core/services/notification.service';

@Component({
    selector: 'app-client-list',
    standalone: true,
    imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule, MatDialogModule, TranslateModule, DataTableComponent],
    templateUrl: './client-list.component.html',
    styleUrls: ['./client-list.component.scss']
})
export class ClientListComponent implements OnInit {
    private clientService = inject(ClientService);
    private dialog = inject(MatDialog);
    private notification = inject(NotificationService);

    public loading = false;
    public clients: Client[] = [];
    public totalItems = 0;
    public pageSize = 10;
    public pageIndex = 0;

    public columns: TableColumn[] = [
        { def: 'company_name', header: 'CLIENT.COMPANY_NAME', sortable: false },
        { def: 'contact_person', header: 'CLIENT.CONTACT_PERSON', sortable: false },
        { def: 'email', header: 'CLIENT.EMAIL', sortable: false },
        { def: 'gst_no', header: 'CLIENT.GST_NO', sortable: false },
        { def: 'status', header: 'COMMON.STATUS', type: 'text', sortable: false },
        { def: 'created_at', header: 'COMMON.CREATED_AT', type: 'date', sortable: false }
    ];

    public actions: TableAction[] = [
        { icon: 'edit', label: 'COMMON.EDIT', action: 'edit' },
        { icon: 'delete', label: 'COMMON.DELETE', action: 'delete', color: 'warn' }
    ];

    ngOnInit(): void {
        this.loadClients();
    }

    loadClients(): void {
        this.loading = true;
        const page = this.pageIndex + 1;
        this.clientService.getClients(page, this.pageSize).subscribe({
            next: (res) => {
                this.clients = res.items ?? res.data ?? [];
                this.totalItems = res.total;
                this.loading = false;
            },
            error: () => this.loading = false
        });
    }

    onPageChange(event: PageEvent): void {
        this.pageIndex = event.pageIndex;
        this.pageSize = event.pageSize;
        this.loadClients();
    }

    onActionClicked(event: { action: string, row: Client }): void {
        switch (event.action) {
            case 'edit':
                this.openFormDialog(event.row);
                break;
            case 'delete':
                this.confirmDelete(event.row);
                break;
        }
    }

    openFormDialog(client?: Client): void {
        const dialogRef = this.dialog.open(ClientFormComponent, {
            width: '600px',
            disableClose: true,
            data: { client }
        });

        dialogRef.afterClosed().subscribe(result => {
            if (result) {
                this.loadClients();
            }
        });
    }

    confirmDelete(client: Client): void {
        const dialogRef = this.dialog.open(ConfirmDialogComponent, {
            width: '400px',
            data: {
                title: 'Delete Client',
                message: `Are you sure you want to delete client ${client.company_name}? This action cannot be entirely undone.`,
                isDestructive: true
            }
        });

        dialogRef.afterClosed().subscribe(confirm => {
            if (confirm) {
                this.clientService.deleteClient(client.id).subscribe(() => {
                    this.notification.showSuccess('Client deleted successfully.');
                    this.loadClients();
                });
            }
        });
    }
}
