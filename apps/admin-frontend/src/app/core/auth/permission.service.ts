import { Injectable, inject, computed } from '@angular/core';
import { AuthService } from './auth.service';

@Injectable({
    providedIn: 'root'
})
export class PermissionService {
    private authService = inject(AuthService);

    // A computed signal that re-evaluates automatically based on the current user roles
    public currentRoles = computed(() => {
        const user = this.authService.currentUser();
        // Backend returns roles as [{id, name}] objects — extract just the name strings
        const roles = user?.roles ?? [];
        return roles.map((r: any) => (typeof r === 'string' ? r : r.name)) as string[];
    });

    /**
     * Check if the logged-in user has the specific role
     * Use SuperAdmin as a wildcard override where applicable
     */
    public hasRole(roleName: string): boolean {
        const roles = this.currentRoles();
        return roles.includes('SuperAdmin') || roles.includes(roleName);
    }

    /**
     * Evaluates if user has ANY of the provided roles
     */
    public hasAnyRole(requiredRoles: string[]): boolean {
        if (!requiredRoles || requiredRoles.length === 0) return true;

        const roles = this.currentRoles();
        if (roles.includes('SuperAdmin')) return true;

        return requiredRoles.some(role => roles.includes(role));
    }

    /**
     * Evaluates if user has ALL of the provided roles
     */
    public hasAllRoles(requiredRoles: string[]): boolean {
        if (!requiredRoles || requiredRoles.length === 0) return true;

        const roles = this.currentRoles();
        if (roles.includes('SuperAdmin')) return true;

        return requiredRoles.every(role => roles.includes(role));
    }
}
