import { Injectable } from '@angular/core';

export interface DecodedToken {
    sub: string;
    tenant_id: string;
    exp: number;
    [key: string]: any;
}

@Injectable({
    providedIn: 'root'
})
export class TokenService {
    private readonly ACCESS_TOKEN_KEY = 'access_token';
    private readonly REFRESH_TOKEN_KEY = 'refresh_token';

    /**
     * Storing Access and Refresh tokens
     */
    setTokens(accessToken: string, refreshToken?: string): void {
        localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken);
        if (refreshToken) {
            localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken);
        }
    }

    getAccessToken(): string | null {
        return localStorage.getItem(this.ACCESS_TOKEN_KEY);
    }

    getRefreshToken(): string | null {
        return localStorage.getItem(this.REFRESH_TOKEN_KEY);
    }

    clearTokens(): void {
        localStorage.removeItem(this.ACCESS_TOKEN_KEY);
        localStorage.removeItem(this.REFRESH_TOKEN_KEY);
    }

    /**
     * Decode the JWT to read payload
     */
    decodeToken(token: string): DecodedToken | null {
        if (!token) return null;
        try {
            const payload = token.split('.')[1];
            const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
            return JSON.parse(decoded);
        } catch (e) {
            console.error('Error decoding token', e);
            return null;
        }
    }

    /**
     * Validate token expiry locally before making API requests
     */
    isTokenExpired(token: string): boolean {
        const decoded = this.decodeToken(token);
        if (!decoded || !decoded.exp) return true;

        // Convert to milliseconds and compare with current time
        // Adding a 30s buffer before it officially expires
        const expiryTimeMs = decoded.exp * 1000;
        const isExpired = Date.now() >= (expiryTimeMs - 30000);

        return isExpired;
    }
}
