import { Component, Inject, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatDividerModule } from '@angular/material/divider';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

import { TenantService, Tenant } from '../../../../core/services/tenant.service';
import { NotificationService } from '../../../../core/services/notification.service';
import { AvatarUploadComponent } from '../../../../shared/components/avatar-upload/avatar-upload.component';

export interface TenantFormDialogData {
  tenant?: Tenant;
}

@Component({
  selector: 'app-tenant-form',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatDialogModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatDividerModule,
    TranslateModule,
    AvatarUploadComponent
  ],
  templateUrl: './tenant-form.html',
  styleUrl: './tenant-form.scss',
})
export class TenantForm implements OnInit {
  private fb = inject(FormBuilder);
  private tenantService = inject(TenantService);
  private notification = inject(NotificationService);

  public tenantForm!: FormGroup;
  public loading = false;

  public get isEditMode(): boolean {
    return !!this.data?.tenant;
  }

  onAvatarChanged(hasAvatar: boolean): void {
    if (this.data.tenant) {
      this.data.tenant.has_avatar = hasAvatar;
    }
  }

  public tiers = ['trial', 'basic', 'premium', 'enterprise'];

  constructor(
    public dialogRef: MatDialogRef<TenantForm>,
    @Inject(MAT_DIALOG_DATA) public data: TenantFormDialogData
  ) { }

  ngOnInit(): void {
    this.tenantForm = this.fb.group({
      name: [this.data?.tenant?.name || '', [Validators.required, Validators.minLength(2)]],
      domain: [this.data?.tenant?.domain || ''],
      subscription_tier: [this.data?.tenant?.subscription_tier || 'trial', Validators.required],
      max_users: [this.data?.tenant?.max_users || 10, [Validators.required, Validators.min(1)]]
    });

    // Add admin fields only for Create mode
    if (!this.isEditMode) {
      this.tenantForm.addControl('admin_first_name', this.fb.control('', Validators.required));
      this.tenantForm.addControl('admin_last_name', this.fb.control('', Validators.required));
      this.tenantForm.addControl('admin_email', this.fb.control('', [Validators.required, Validators.email]));
      this.tenantForm.addControl('admin_password', this.fb.control('password123', [Validators.required, Validators.minLength(6)]));
    }
  }

  onSubmit(): void {
    if (this.tenantForm.invalid) return;

    this.loading = true;
    const payload = this.tenantForm.getRawValue();

    if (this.isEditMode) {
      this.tenantService.updateTenant(this.data.tenant!.id, {
        name: payload.name,
        domain: payload.domain,
        subscription_tier: payload.subscription_tier,
        max_users: payload.max_users
      }).subscribe({
        next: (res) => {
          this.notification.showSuccess('Tenant updated successfully.');
          this.dialogRef.close(res);
        },
        error: () => this.loading = false
      });
    } else {
      this.tenantService.createTenant(payload).subscribe({
        next: (res) => {
          this.notification.showSuccess('Tenant and Admin User created successfully.');
          this.dialogRef.close(res);
        },
        error: () => this.loading = false
      });
    }
  }
}
