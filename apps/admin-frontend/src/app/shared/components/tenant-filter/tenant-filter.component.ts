import { Component, EventEmitter, Output, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormControl } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatAutocompleteModule, MatAutocompleteSelectedEvent } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { Observable } from 'rxjs';
import { map, startWith } from 'rxjs/operators';

import { TenantService, Tenant } from '../../../core/services/tenant.service';

/**
 * SuperAdmin-only searchable "Filter by Tenant" dropdown. Wrap usages in
 * `*ngIf="isSuperAdmin"` — this component doesn't gate itself.
 *
 * Emits `tenantsLoaded` once with the full tenant list (for building a
 * "Tenant" column lookup), and `tenantChange` whenever the selection changes
 * or is cleared.
 */
@Component({
    selector: 'app-tenant-filter',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatFormFieldModule,
        MatInputModule,
        MatAutocompleteModule,
        MatButtonModule,
        MatIconModule,
    ],
    templateUrl: './tenant-filter.component.html',
    styleUrl: './tenant-filter.component.scss',
})
export class TenantFilterComponent implements OnInit {
    private tenantService = inject(TenantService);

    @Output() tenantsLoaded = new EventEmitter<Tenant[]>();
    @Output() tenantChange = new EventEmitter<Tenant | null>();

    public tenants: Tenant[] = [];
    public tenantFilterCtrl = new FormControl('');
    public filteredTenants!: Observable<Tenant[]>;
    public selectedTenant: Tenant | null = null;

    ngOnInit(): void {
        // Fetch the full tenant list (100 is the API's max page size) to back the
        // searchable filter dropdown and the Tenant column.
        this.tenantService.getTenants(1, 100).subscribe({
            next: (res) => {
                this.tenants = res.items;
                this.tenantsLoaded.emit(this.tenants);
                this.filteredTenants = this.tenantFilterCtrl.valueChanges.pipe(
                    startWith(''),
                    map(value => this.filterTenants(value))
                );
            }
        });
    }

    private filterTenants(value: string | Tenant | null): Tenant[] {
        const name = typeof value === 'string' ? value : value?.name ?? '';
        const filterValue = name.toLowerCase();
        return this.tenants.filter(t => t.name.toLowerCase().includes(filterValue));
    }

    onTenantSelected(event: MatAutocompleteSelectedEvent): void {
        this.selectedTenant = event.option.value as Tenant;
        this.tenantChange.emit(this.selectedTenant);
    }

    clearFilter(): void {
        this.selectedTenant = null;
        this.tenantFilterCtrl.setValue('');
        this.tenantChange.emit(null);
    }

    displayTenant(tenant: Tenant): string {
        return tenant?.name ?? '';
    }
}
