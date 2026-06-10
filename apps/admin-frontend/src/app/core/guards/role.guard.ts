import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../auth/auth.service';
import { PermissionService } from '../auth/permission.service';

export const roleGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const permissionService = inject(PermissionService);
    const router = inject(Router);

    if (!authService.isAuthenticated()) {
        return router.createUrlTree(['/auth/login'], { queryParams: { returnUrl: state.url } });
    }

    // Get roles attached to the route data
    const expectedRoles = route.data['roles'] as Array<string>;

    if (!expectedRoles || expectedRoles.length === 0) {
        // If no specific roles required, allow access (fallback)
        return true;
    }

    // Check if current user has any of the required roles
    if (permissionService.hasAnyRole(expectedRoles)) {
        return true;
    }

    // Unauthorized for this specific route but logged in
    return router.createUrlTree(['/unauthorized']);
};
