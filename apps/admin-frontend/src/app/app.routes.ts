import { Routes } from '@angular/router';
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout.component';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: '', redirectTo: 'loads', pathMatch: 'full' },
            {
                path: 'loads',
                loadComponent: () => import('./features/loads/loads-main/loads-main').then(m => m.LoadsMain)
            },
            {
                path: 'trucks',
                loadComponent: () => import('./features/trucks/truck-list/truck-list.component').then(m => m.TruckListComponent)
            },
            {
                path: 'drivers',
                loadComponent: () => import('./features/drivers/driver-list/driver-list.component').then(m => m.DriverListComponent)
            },
            {
                path: 'clients',
                loadComponent: () => import('./features/clients/client-list/client-list.component').then(m => m.ClientListComponent)
            },
            {
                path: 'tenants',
                loadComponent: () => import('./features/admin/tenants/tenant-list/tenant-list').then(m => m.TenantList)
            },
            {
                path: 'users',
                loadComponent: () => import('./features/admin/users/user-list/user-list').then(m => m.UserList)
            },
            {
                path: 'reports',
                loadComponent: () => import('./features/reports/reports-dashboard/reports-dashboard.component').then(m => m.ReportsDashboardComponent)
            },
            {
                path: 'invoices',
                loadComponent: () => import('./features/invoices/invoice-list/invoice-list.component').then(m => m.InvoiceListComponent)
            },
            {
                path: 'invoices/:id',
                loadComponent: () => import('./features/invoices/invoice-detail/invoice-detail.component').then(m => m.InvoiceDetailComponent)
            }
        ]
    },
    {
        path: 'auth',
        component: AuthLayoutComponent,
        children: [
            {
                path: 'login',
                loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
            },
            { path: '', redirectTo: 'login', pathMatch: 'full' }
        ]
    },
    { path: '**', redirectTo: '' }
];
