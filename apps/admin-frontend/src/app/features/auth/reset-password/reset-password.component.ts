import { Component, inject, OnInit, signal } from '@angular/core';
import { AbstractControl, FormBuilder, ValidationErrors, Validators, ReactiveFormsModule } from '@angular/forms';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { AuthService } from '../../../core/auth/auth.service';
import { NotificationService } from '../../../core/services/notification.service';

/** Validator: `confirm_password` must match `new_password`. */
function passwordsMatch(control: AbstractControl): ValidationErrors | null {
    const newPassword = control.get('new_password')?.value;
    const confirm = control.get('confirm_password')?.value;
    return newPassword === confirm ? null : { mismatch: true };
}

@Component({
    selector: 'app-reset-password',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        RouterLink,
        MatCardModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatProgressSpinnerModule,
        TranslateModule,
    ],
    templateUrl: './reset-password.component.html',
    styleUrls: ['./reset-password.component.scss'],
})
export class ResetPasswordComponent implements OnInit {
    private fb = inject(FormBuilder);
    private route = inject(ActivatedRoute);
    private router = inject(Router);
    private authService = inject(AuthService);
    private notification = inject(NotificationService);

    public isLoading = signal(false);
    public token = '';

    public form = this.fb.group({
        new_password: ['', [Validators.required, Validators.minLength(8)]],
        confirm_password: ['', Validators.required],
    }, { validators: passwordsMatch });

    ngOnInit(): void {
        this.token = this.route.snapshot.queryParamMap.get('token') ?? '';
        if (!this.token) {
            this.notification.showError('Missing or invalid reset link.');
        }
    }

    onSubmit(): void {
        if (this.form.invalid || !this.token) return;

        this.isLoading.set(true);
        this.authService.resetPassword(this.token, this.form.value.new_password!).subscribe({
            next: () => {
                this.isLoading.set(false);
                this.notification.showSuccess('Password reset successfully. Please log in with your new password.');
                this.router.navigate(['/auth/login']);
            },
            error: () => this.isLoading.set(false),
        });
    }
}
