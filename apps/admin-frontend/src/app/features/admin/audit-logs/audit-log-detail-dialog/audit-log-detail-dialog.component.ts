import { Component, Inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MAT_DIALOG_DATA, MatDialogModule } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatDividerModule } from '@angular/material/divider';

import { AuditLogItem } from '../audit-log.service';

@Component({
    selector: 'app-audit-log-detail-dialog',
    standalone: true,
    imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule, MatDividerModule],
    template: `
<h2 mat-dialog-title>
  <mat-icon>history</mat-icon>
  {{ data.event_type }}
</h2>

<mat-dialog-content class="dialog-content">
  <div class="info-row"><span class="info-label">When</span><span>{{ data.created_at }}</span></div>
  <div class="info-row"><span class="info-label">Category</span><span>{{ data.event_category }}</span></div>
  <div class="info-row"><span class="info-label">User</span><span>{{ data.user_email ?? '—' }}</span></div>
  <div class="info-row" *ngIf="data.resource_type">
    <span class="info-label">Resource</span><span>{{ data.resource_type }} {{ data.resource_id }}</span>
  </div>
  <div class="info-row" *ngIf="data.ip_address">
    <span class="info-label">IP Address</span><span>{{ data.ip_address }}</span>
  </div>
  <div class="info-row" *ngIf="data.user_agent">
    <span class="info-label">User Agent</span><span class="ua">{{ data.user_agent }}</span>
  </div>

  <ng-container *ngIf="data.old_value">
    <mat-divider class="mt-3"></mat-divider>
    <h4>Old Value</h4>
    <pre>{{ data.old_value | json }}</pre>
  </ng-container>

  <ng-container *ngIf="data.new_value">
    <mat-divider class="mt-3"></mat-divider>
    <h4>New Value</h4>
    <pre>{{ data.new_value | json }}</pre>
  </ng-container>

  <ng-container *ngIf="hasExtraData()">
    <mat-divider class="mt-3"></mat-divider>
    <h4>Extra Data</h4>
    <pre>{{ data.extra_data | json }}</pre>
  </ng-container>
</mat-dialog-content>

<mat-dialog-actions align="end">
  <button mat-button mat-dialog-close>Close</button>
</mat-dialog-actions>
    `,
    styles: [`
        .dialog-content { min-width: 420px; max-width: 600px; }
        .info-row {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            padding: 6px 0;
            border-bottom: 1px solid rgba(0,0,0,0.06);
            font-size: 0.9rem;
        }
        .info-row:last-of-type { border-bottom: none; }
        .info-label { opacity: 0.6; font-weight: 500; flex-shrink: 0; }
        .ua { text-align: right; word-break: break-all; }
        .mt-3 { margin-top: 12px; }
        h4 { margin: 12px 0 4px; font-size: 0.85rem; opacity: 0.7; }
        pre {
            background: rgba(0,0,0,0.04);
            border-radius: 6px;
            padding: 8px;
            font-size: 0.8rem;
            overflow-x: auto;
            white-space: pre-wrap;
            word-break: break-word;
        }
    `],
})
export class AuditLogDetailDialogComponent {
    constructor(@Inject(MAT_DIALOG_DATA) public data: AuditLogItem) {}

    hasExtraData(): boolean {
        return !!this.data.extra_data && Object.keys(this.data.extra_data).length > 0;
    }
}
