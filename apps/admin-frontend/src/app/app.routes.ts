import { Routes } from '@angular/router';
import { AdminLayoutComponent } from './layouts/admin-layout/admin-layout.component';
import { AuthLayoutComponent } from './layouts/auth-layout/auth-layout.component';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';
import { homeRedirectGuard } from './core/guards/home-redirect.guard';

export const routes: Routes = [
    {
        path: '',
        component: AdminLayoutComponent,
        canActivate: [authGuard],
        children: [
            { path: '', pathMatch: 'full', canActivate: [homeRedirectGuard], children: [] },
            {
                path: 'loads',
                canActivate: [roleGuard],
                data: { roles: ['SuperAdmin', 'TenantAdmin', 'TransportAdmin', 'Accounts', 'Driver'] },
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
                path: 'audit-logs',
                canActivate: [roleGuard],
                data: { roles: ['SuperAdmin', 'TenantAdmin'] },
                loadComponent: () => import('./features/admin/audit-logs/audit-log-list/audit-log-list.component').then(m => m.AuditLogListComponent)
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
        path: 'portal',
        loadComponent: () => import('./layouts/portal-layout/portal-layout.component').then(m => m.PortalLayoutComponent),
        canActivate: [authGuard, roleGuard],
        data: { roles: ['Client'] },
        children: [
            { path: '', redirectTo: 'shipments', pathMatch: 'full' },
            {
                path: 'shipments',
                loadComponent: () => import('./features/portal/shipment-list/shipment-list.component').then(m => m.ShipmentListComponent)
            },
            {
                path: 'shipments/:id',
                loadComponent: () => import('./features/portal/shipment-detail/shipment-detail.component').then(m => m.ShipmentDetailComponent)
            },
            {
                path: 'invoices',
                loadComponent: () => import('./features/portal/invoice-list/invoice-list.component').then(m => m.PortalInvoiceListComponent)
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
            {
                path: 'forgot-password',
                loadComponent: () => import('./features/auth/forgot-password/forgot-password.component').then(m => m.ForgotPasswordComponent)
            },
            {
                path: 'reset-password',
                loadComponent: () => import('./features/auth/reset-password/reset-password.component').then(m => m.ResetPasswordComponent)
            },
            { path: '', redirectTo: 'login', pathMatch: 'full' }
        ]
    },
    { path: '**', redirectTo: '' }
];
