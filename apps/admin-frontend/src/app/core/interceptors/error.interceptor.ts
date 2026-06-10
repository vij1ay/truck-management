import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError } from 'rxjs/operators';
import { throwError } from 'rxjs';
import { NotificationService } from '../services/notification.service';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
    const notificationService = inject(NotificationService);

    return next(req).pipe(
        catchError((error: HttpErrorResponse) => {
            let errorMsg = 'An unknown error occurred';

            if (error.error instanceof ErrorEvent) {
                // Client-side or Network Error
                errorMsg = error.error.message || '{"isTrusted": true, "reason": "Network Error or CORS"}';
            } else {
                // Server-side error
                if (Array.isArray(error.error?.detail)) {
                    // FastAPI validation errors -> Transform to requested structured format
                    const fieldErrors: { [key: string]: string } = {};
                    error.error.detail.forEach((e: any) => {
                        const loc = e.loc && e.loc.length > 1 ? e.loc[e.loc.length - 1] : 'unknown_field';
                        fieldErrors[loc] = e.msg;
                    });

                    const structuredError = {
                        status: "failure",
                        data: fieldErrors
                    };
                    errorMsg = JSON.stringify(structuredError, null, 2);
                } else if (typeof error.error?.detail === 'string') {
                    errorMsg = error.error.detail;
                } else if (error.error?.message) {
                    errorMsg = error.error.message;
                } else if (error.error) {
                    errorMsg = JSON.stringify(error.error, null, 2);
                } else {
                    errorMsg = error.message || `HTTP ${error.status}`;
                }
            }

            notificationService.showError(errorMsg);
            return throwError(() => error);
        })
    );
};
