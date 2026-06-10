import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { environment } from '../../../environments/environment';
import { TokenService } from '../auth/token.service';

export const apiInterceptor: HttpInterceptorFn = (req, next) => {
    // Pass through if requesting local assets like i18n
    if (req.url.startsWith('/assets/') || req.url.startsWith('./assets/')) {
        return next(req);
    }

    const tokenService = inject(TokenService);
    const token = tokenService.getAccessToken();

    let headers = req.headers;
    if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
    }

    const apiReq = req.clone({
        url: `${environment.apiUrl}${req.url.startsWith('/') ? req.url : '/' + req.url}`,
        headers
    });

    return next(apiReq);
};
