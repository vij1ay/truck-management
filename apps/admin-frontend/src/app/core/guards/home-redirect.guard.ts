import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { PermissionService } from '../auth/permission.service';

/**
 * Sends Client-role users to the customer portal, everyone else to the load board.
 * Used on the root ('') route instead of a static redirectTo.
 */
export const homeRedirectGuard: CanActivateFn = () => {
    const permissionService = inject(PermissionService);
    const router = inject(Router);

    if (permissionService.hasAnyRole(['Client']) && !permissionService.hasAnyRole(['SuperAdmin', 'TenantAdmin', 'TransportAdmin', 'Accounts'])) {
        return router.createUrlTree(['/portal']);
    }

    return router.createUrlTree(['/loads']);
};
