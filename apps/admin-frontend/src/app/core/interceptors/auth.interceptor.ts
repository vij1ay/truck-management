import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, filter, take } from 'rxjs/operators';
import { throwError, BehaviorSubject, Observable } from 'rxjs';
import { AuthService } from '../auth/auth.service';

// Module-level variable to hold the refresh state across requests
let isRefreshing = false;
let refreshTokenSubject: BehaviorSubject<string | null> = new BehaviorSubject<string | null>(null);

export const authInterceptor: HttpInterceptorFn = (req, next) => {
    const authService = inject(AuthService);

    // If we are calling the refresh or login endpoints, do not intercept 401s
    if (req.url.includes('auth/login') || req.url.includes('auth/refresh')) {
        return next(req);
    }

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            if (error.status === 401) {
                return handle401Error(req, next, authService);
            }
            return throwError(() => error);
        })
    );
};

function handle401Error(req: any, next: any, authService: AuthService): Observable<any> {
    if (!isRefreshing) {
        isRefreshing = true;
        refreshTokenSubject.next(null);

        return authService.refreshToken().pipe(
            switchMap((tokenResponse: any) => {
                isRefreshing = false;
                refreshTokenSubject.next(tokenResponse.access_token);
                // Re-execute the request with the new token
                const newReq = req.clone({
                    headers: req.headers.set('Authorization', `Bearer ${tokenResponse.access_token}`)
                });
                return next(newReq);
            }),
            catchError((err) => {
                isRefreshing = false;
                authService.clearSession(); // Token fully invalid, clear local auth explicitly
                return throwError(() => err);
            })
        );
    } else {
        // Already refreshing, queue the pending requests until the token is updated
        return refreshTokenSubject.pipe(
            filter(token => token !== null),
            take(1),
            switchMap((token) => {
                const newReq = req.clone({
                    headers: req.headers.set('Authorization', `Bearer ${token}`)
                });
                return next(newReq);
            })
        );
    }
}
