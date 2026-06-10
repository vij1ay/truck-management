import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../auth/auth.service';
import { TokenService } from '../auth/token.service';

export const authGuard: CanActivateFn = (route, state) => {
    const authService = inject(AuthService);
    const tokenService = inject(TokenService);
    const router = inject(Router);

    // If there is an access token in localStorage, assume authenticated for routing purposes.
    // The HTTP interceptors will handle 401s and token refreshes asynchronously.
    if (tokenService.getAccessToken()) {
        return true;
    }

    // Not authenticated, redirect to login page with the return url
    return router.createUrlTree(['/auth/login'], { queryParams: { returnUrl: state.url } });
};
