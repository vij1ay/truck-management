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
import { ClientService } from '../../../clients/services/client.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { AvatarUploadComponent } from '../../../../shared/components/avatar-upload/avatar-upload.component';

const DEFAULT_TIMEZONE = 'Asia/Kolkata';

export interface UserFormDialogData {
  user?: User;
}

interface ClientOption {
  id: string;
  company_name: string;
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
    TranslateModule,
    AvatarUploadComponent
  ],
  templateUrl: './user-form.html',
  styleUrl: './user-form.scss',
})
export class UserForm implements OnInit {
  private fb = inject(FormBuilder);
  private userService = inject(UserService);
  private clientService = inject(ClientService);
  private notification = inject(NotificationService);

  public userForm!: FormGroup;
  public loading = false;

  // Based on the system roles, Sub-admin can provision these normally
  public availableRoles = ['TransportAdmin', 'Accounts', 'Client', 'Driver'];

  // Populated from GET /users/timezones (pytz.common_timezones)
  public timezones: string[] = [];

  // Populated from GET /clients — used to link a portal login to a Client (company)
  public clients: ClientOption[] = [];

  public get isEditMode(): boolean {
    return !!this.data?.user;
  }

  onAvatarChanged(hasAvatar: boolean): void {
    if (this.data.user) {
      this.data.user.has_avatar = hasAvatar;
    }
  }

  /** Whether the "Linked Client" dropdown should be shown (role = Client). */
  public isClientRole(): boolean {
    if (this.isEditMode) {
      return this.data?.user?.roles?.[0]?.name === 'Client';
    }
    return this.userForm?.get('role')?.value === 'Client';
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
      role: [{ value: existingRole, disabled: this.isEditMode }, Validators.required],
      timezone: [this.data?.user?.timezone || DEFAULT_TIMEZONE, Validators.required],
      // Linked Client (company) record — only meaningful when role = Client
      client_id: [this.data?.user?.client_id ?? null]
    });

    if (!this.isEditMode) {
      this.userForm.addControl('password', this.fb.control('password123', [Validators.required, Validators.minLength(6)]));
    }

    this.userService.getTimezones().subscribe({
      next: (res) => this.timezones = res.timezones,
      error: () => this.timezones = [this.userForm.get('timezone')!.value],
    });

    // Clients dropdown for "Linked Client" — fetch a generous page so the list is complete
    this.clientService.getClients(1, 100).subscribe({
      next: (res) => this.clients = ((res.items ?? res.data ?? []) as unknown as ClientOption[]),
      error: () => this.clients = [],
    });
  }

  onSubmit(): void {
    if (this.userForm.invalid) return;

    this.loading = true;
    const payload = this.userForm.getRawValue();

    if (this.isEditMode) {
      const update: any = {
        first_name: payload.first_name,
        last_name: payload.last_name,
        phone: payload.phone,
        timezone: payload.timezone
      };
      if (this.isClientRole()) {
        update.client_id = payload.client_id;
      }
      this.userService.updateUser(this.data.user!.id, update).subscribe({
        next: (res) => {
          this.notification.showSuccess('User updated successfully.');
          this.dialogRef.close(res);
        },
        error: () => this.loading = false
      });
    } else {
      // Create user then assign role sequentially
      const create: any = {
        first_name: payload.first_name,
        last_name: payload.last_name,
        email: payload.email,
        password: payload.password,
        phone: payload.phone,
        timezone: payload.timezone
      };
      if (this.isClientRole()) {
        create.client_id = payload.client_id;
      }
      this.userService.createUser(create).pipe(
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
