import { Component, inject, signal } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { AuthService } from '../../../core/auth/auth.service';

@Component({
    selector: 'app-forgot-password',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        RouterLink,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        TranslateModule,
    ],
    templateUrl: './forgot-password.component.html',
    styleUrls: ['./forgot-password.component.scss'],
})
export class ForgotPasswordComponent {
    private fb = inject(FormBuilder);
    private authService = inject(AuthService);

    public isLoading = signal(false);
    public submitted = signal(false);
    /** Dev-only: present when the backend returns DEBUG=true (no email service yet). */
    public resetToken = signal<string | null>(null);

    public form = this.fb.group({
        email: ['', [Validators.required, Validators.email]],
    });

    onSubmit(): void {
        if (this.form.invalid) return;

        this.isLoading.set(true);
        const email = this.form.value.email!;

        this.authService.forgotPassword(email).subscribe({
            next: (res) => {
                this.isLoading.set(false);
                this.submitted.set(true);
                this.resetToken.set(res.reset_token ?? null);
            },
            error: () => {
                this.isLoading.set(false);
                // Error intercepted globally by errorInterceptor (e.g. network issue).
            },
        });
    }
}
