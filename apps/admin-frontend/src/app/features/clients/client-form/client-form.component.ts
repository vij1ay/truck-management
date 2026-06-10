import { Component, Inject, inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialogRef, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { CommonModule } from '@angular/common';
import { TranslateModule } from '@ngx-translate/core';

import { ClientService, Client } from '../services/client.service';
import { NotificationService } from '../../../core/services/notification.service';

export interface ClientFormDialogData {
    client?: Client;
}

@Component({
    selector: 'app-client-form',
    standalone: true,
    imports: [
        CommonModule,
        ReactiveFormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatIconModule,
        TranslateModule
    ],
    templateUrl: './client-form.component.html',
    styleUrls: ['./client-form.component.scss']
})
export class ClientFormComponent implements OnInit {
    private fb = inject(FormBuilder);
    private clientService = inject(ClientService);
    private notification = inject(NotificationService);

    public clientForm!: FormGroup;
    public loading = false;

    public get isEditMode(): boolean {
        return !!this.data?.client;
    }

    constructor(
        public dialogRef: MatDialogRef<ClientFormComponent>,
        @Inject(MAT_DIALOG_DATA) public data: ClientFormDialogData
    ) { }

    ngOnInit(): void {
        this.clientForm = this.fb.group({
            company_name: [this.data?.client?.company_name || '', Validators.required],
            contact_person: [this.data?.client?.contact_person || '', Validators.required],
            email: [
                this.data?.client?.email || '',
                [Validators.required, Validators.email]
            ],
            phone: [
                this.data?.client?.phone || '', 
                [Validators.required, Validators.pattern(/^\+?91[\s-]?\d{10}$|^\d{10}$/)]
            ],
            gst_no: [
                { value: this.data?.client?.gst_no || '', disabled: this.isEditMode },
                [Validators.required]
            ],
            address: [this.data?.client?.address || '', Validators.required]
        });
    }

    onSubmit(): void {
        if (this.clientForm.invalid) return;

        this.loading = true;
        const payload = this.clientForm.getRawValue();

        if (this.isEditMode) {
            this.clientService.updateClient(this.data.client!.id, {
                company_name: payload.company_name,
                contact_person: payload.contact_person,
                email: payload.email,
                phone: payload.phone,
                address: payload.address
            }).subscribe({
                next: (res) => {
                    this.notification.showSuccess('Client updated successfully.');
                    this.dialogRef.close(res);
                },
                error: () => this.loading = false
            });
        } else {
            this.clientService.createClient(payload).subscribe({
                next: (res) => {
                    this.notification.showSuccess('Client registered successfully.');
                    this.dialogRef.close(res);
                },
                error: () => this.loading = false
            });
        }
    }
}
