import { Component, Input, Output, EventEmitter, ViewChild, AfterViewInit, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTableModule, MatTableDataSource } from '@angular/material/table';
import { MatPaginatorModule, MatPaginator, PageEvent } from '@angular/material/paginator';
import { MatSortModule, MatSort, Sort } from '@angular/material/sort';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { TranslateModule } from '@ngx-translate/core';
import { MatMenuModule } from '@angular/material/menu';
import { AvatarThumbComponent } from '../avatar-thumb/avatar-thumb.component';
import { AvatarEntityType } from '../../../core/services/avatar.service';

export interface TableColumn {
    def: string;      // The exact property string matching backend payload
    header: string;   // Translation key for the header
    type?: 'text' | 'date' | 'datetime' | 'badge' | 'action' | 'avatar'; // Determines renderer
    sortable?: boolean;
    /** Required when type === 'avatar' — which AvatarService entity type to fetch. */
    avatarEntityType?: AvatarEntityType;
    /** Placeholder icon for the 'avatar' renderer when the row has no photo. */
    avatarPlaceholderIcon?: string;
}

export interface TableAction {
    icon: string;
    label: string; // Translation key
    action: string; // Action identifier
    color?: string;
    showIf?: (row: any) => boolean; // Optional callback to hide/show action per row
}

@Component({
    selector: 'app-data-table',
    standalone: true,
    imports: [
        CommonModule,
        MatTableModule,
        MatPaginatorModule,
        MatSortModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatMenuModule,
        TranslateModule,
        AvatarThumbComponent
    ],
    templateUrl: './data-table.component.html',
    styleUrls: ['./data-table.component.scss']
})
export class DataTableComponent implements AfterViewInit, OnChanges {
    @Input({ required: true }) columns: TableColumn[] = [];
    @Input({ required: true }) data: any[] | null = [];
    @Input() totalItems: number = 0;
    @Input() pageSize: number = 10;
    @Input() pageIndex: number = 0;
    @Input() loading: boolean = false;
    @Input() actions: TableAction[] = [];

    @Output() pageChanged = new EventEmitter<PageEvent>();
    @Output() sortChanged = new EventEmitter<Sort>();
    @Output() actionClicked = new EventEmitter<{ action: string, row: any }>();

    public displayedColumns: string[] = [];
    public dataSource = new MatTableDataSource<any>([]);

    @ViewChild(MatPaginator) paginator!: MatPaginator;
    @ViewChild(MatSort) sort!: MatSort;

    ngOnChanges(changes: SimpleChanges): void {
        if (changes['columns']) {
            this.displayedColumns = this.columns.map(c => c.def);
            if (this.actions && this.actions.length > 0 && !this.displayedColumns.includes('actions')) {
                this.displayedColumns.push('actions');
            }
        }

        if (changes['data'] && this.data) {
            // In server-side pagination, we just replace the exact data frame
            this.dataSource.data = this.data;
        }
    }

    ngAfterViewInit(): void {
        // For purely client-side tables you'd attach these.
        // For server-side, we intercept the events manually via UI bindings instead.
    }

    public onPage(event: PageEvent) {
        this.pageChanged.emit(event);
    }

    public onSort(event: Sort) {
        this.sortChanged.emit(event);
    }

    public onAction(actionId: string, row: any) {
        this.actionClicked.emit({ action: actionId, row });
    }
}
