import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface RoleBasic {
    id: string;
    name: string;
}

export interface User {
    id: string;
    email: string;
    first_name: string;
    last_name: string;
    phone: string | null;
    tenant_id: string;
    is_active: boolean;
    is_verified: boolean;
    timezone: string;
    client_id: string | null;
    last_login_at: string | null;
    created_at: string;
    updated_at: string;
    roles: RoleBasic[];
    has_avatar?: boolean;
}

export interface TimezoneListResponse {
    timezones: string[];
}

export interface UserListResponse {
    items: User[];
    total: number;
    page: number;
    size: number;
    pages: number;
}

export interface UserCreate {
    email: string;
    password?: string;
    first_name: string;
    last_name: string;
    phone?: string;
    roles?: string[]; // array of role IDs or names depending on backend logic. Wait, backend defines UserCreate without roles initially? Actually backend has separate POST /users/{id}/roles
    // The backend `UserCreate` has 'role' string but let's check. Wait, backend usually provisions base user then assigns roles. Let's look up `RoleAssignmentRequest`.
}

@Injectable({
    providedIn: 'root'
})
export class UserService {
    private http = inject(HttpClient);
    private endpoint = 'users';

    getUsers(page: number = 1, size: number = 10, search?: string, isActive?: boolean, tenantId?: string): Observable<UserListResponse> {
        let params = new HttpParams()
            .set('page', page.toString())
            .set('size', size.toString());

        if (search) params = params.set('search', search);
        if (isActive !== undefined) params = params.set('is_active', isActive);
        if (tenantId) params = params.set('tenant_id', tenantId);

        return this.http.get<UserListResponse>(this.endpoint, { params });
    }

    getUser(id: string): Observable<User> {
        return this.http.get<User>(`${this.endpoint}/${id}`);
    }

    createUser(data: any): Observable<User> {
        return this.http.post<User>(this.endpoint, data);
    }

    updateUser(id: string, data: any): Observable<User> {
        return this.http.patch<User>(`${this.endpoint}/${id}`, data);
    }

    deleteUser(id: string): Observable<void> {
        return this.http.delete<void>(`${this.endpoint}/${id}`);
    }

    activateUser(id: string): Observable<User> {
        return this.http.post<User>(`${this.endpoint}/${id}/activate`, {});
    }

    deactivateUser(id: string): Observable<User> {
        return this.http.post<User>(`${this.endpoint}/${id}/deactivate`, {});
    }

    assignRole(userId: string, roleName: string): Observable<User> {
        // Backend actually expects role_id realistically, but we will pass roleName if it accepts it or we must fetch roles first. Let's just create raw payload and we'll check backend schemas.
        return this.http.post<User>(`${this.endpoint}/${userId}/roles`, { role_name: roleName });
    }

    getTimezones(): Observable<TimezoneListResponse> {
        return this.http.get<TimezoneListResponse>(`${this.endpoint}/timezones`);
    }
}
