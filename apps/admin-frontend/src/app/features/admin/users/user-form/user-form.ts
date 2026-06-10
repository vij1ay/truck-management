import { Component, Inject, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';
import { switchMap } from 'rxjs';

import { UserService, User } from '../user.service';
import { NotificationService } from '../../../../core/services/notification.service';

export interface UserFormDialogData {
  user?: User;
}

@Component({
  selector: 'app-user-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    TranslateModule
  ],
  templateUrl: './user-form.html',
  styleUrl: './user-form.scss',
})
export class UserForm implements OnInit {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private notification = inject(NotificationService);

  public userForm!: FormGroup;
  public loading = false;

  // Based on the system roles, Sub-admin can provision these normally
  public availableRoles = ['TransportAdmin', 'Accounts', 'Client', 'Driver'];

  public get isEditMode(): boolean {
    return !!this.data?.user;
  }

  constructor(
    public dialogRef: MatDialogRef<UserForm>,
    @Inject(MAT_DIALOG_DATA) public data: UserFormDialogData
  ) { }

  ngOnInit(): void {
    const existingRole = this.data?.user?.roles?.[0]?.name || '';

    this.userForm = this.fb.group({
      first_name: [this.data?.user?.first_name || '', Validators.required],
      last_name: [this.data?.user?.last_name || '', Validators.required],
      email: [
        { value: this.data?.user?.email || '', disabled: this.isEditMode },
        [Validators.required, Validators.email]
      ],
      phone: [this.data?.user?.phone || ''],
      // Role assignment is treated as a separate API call usually, but we capture it here.
      role: [{ value: existingRole, disabled: this.isEditMode }, Validators.required]
    });

    if (!this.isEditMode) {
      this.userForm.addControl('password', this.fb.control('password123', [Validators.required, Validators.minLength(6)]));
    }
  }

  onSubmit(): void {
    if (this.userForm.invalid) return;

    this.loading = true;
    const payload = this.userForm.getRawValue();

    if (this.isEditMode) {
      this.userService.updateUser(this.data.user!.id, {
        first_name: payload.first_name,
        last_name: payload.last_name,
        phone: payload.phone
      }).subscribe({
        next: (res) => {
          this.notification.showSuccess('User updated successfully.');
          this.dialogRef.close(res);
        },
        error: () => this.loading = false
      });
    } else {
      // Create user then assign role sequentially
      this.userService.createUser({
        first_name: payload.first_name,
        last_name: payload.last_name,
        email: payload.email,
        password: payload.password,
        phone: payload.phone
      }).pipe(
        switchMap(createdUser => this.userService.assignRole(createdUser.id, payload.role))
      ).subscribe({
        next: (res) => {
          this.notification.showSuccess('User created successfully.');
          this.dialogRef.close(res);
        },
        error: () => this.loading = false
      });
    }
  }
}
