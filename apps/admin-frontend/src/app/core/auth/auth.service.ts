import { Injectable, signal, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, of, throwError, switchMap, map } from 'rxjs';
import { TokenService } from './token.service';

export interface AuthResponse {
    access_token: string;
    refresh_token: string;
    token_type: string;
}

export interface RoleBasic {
    id: string;
    name: string;
}

export interface UserProfile {
    id: number;
    email: string;
    first_name: string;
    last_name: string;
    tenant_id: string;
    roles: RoleBasic[];  // Backend returns [{id, name}] objects
}

export interface ForgotPasswordResponse {
    message: string;
    /** Only set when the backend is running with DEBUG=true (no email service yet). */
    reset_token?: string | null;
}

@Injectable({
    providedIn: 'root'
})
export class AuthService {
    private http = inject(HttpClient);
    private tokenService = inject(TokenService);
    private router = inject(Router);

    // Signals for reactive UI state
    public currentUser = signal<UserProfile | null>(null);
    public isAuthenticated = signal<boolean>(false);

    // Call on app initialization or explicit login
    public loadProfile(): Observable<UserProfile | null> {
        const token = this.tokenService.getAccessToken();
        if (!token || this.tokenService.isTokenExpired(token)) {
            this.clearSession();
            return of(null);
        }

        return this.http.get<UserProfile>('users/me').pipe(
            tap(profile => {
                this.currentUser.set(profile);
                this.isAuthenticated.set(true);
            }),
            catchError(() => {
                this.clearSession();
                return of(null);
            })
        );
    }

    public login(credentials: any): Observable<AuthResponse> {
        return this.http.post<AuthResponse>('auth/login', {
            email: credentials.email,
            password: credentials.password
        }).pipe(
            switchMap(res => {
                this.tokenService.setTokens(res.access_token, res.refresh_token);
                return this.loadProfile().pipe(
                    map(() => res) // Yield original token response to caller
                );
            })
        );
    }

    // Uses Refresh Token to get a new Access Token
    public refreshToken(): Observable<AuthResponse> {
        const refreshToken = this.tokenService.getRefreshToken();
        if (!refreshToken) {
            return throwError(() => new Error('No refresh token available.'));
        }

        return this.http.post<AuthResponse>('auth/refresh', { refresh_token: refreshToken }).pipe(
            tap(res => {
                // Store the new tokens
                this.tokenService.setTokens(res.access_token, res.refresh_token);
            }),
            catchError(err => {
                this.logout();
                return throwError(() => err);
            })
        );
    }

    // Log the user out from Backend & Frontend
    public logout(): void {
        this.http.post('auth/logout', {}).pipe(
            catchError(() => of(null)) // Ignore backend errors on logout (e.g. if token already invalid)
        ).subscribe(() => {
            this.clearSession();
            this.router.navigate(['/auth/login']);
        });
    }

    // Clear local state
    public clearSession(): void {
        this.tokenService.clearTokens();
        this.currentUser.set(null);
        this.isAuthenticated.set(false);
    }

    public forgotPassword(email: string): Observable<ForgotPasswordResponse> {
        return this.http.post<ForgotPasswordResponse>('auth/forgot-password', { email });
    }

    public resetPassword(token: string, newPassword: string): Observable<{ message: string }> {
        return this.http.post<{ message: string }>('auth/reset-password', {
            token,
            new_password: newPassword,
        });
    }
}
