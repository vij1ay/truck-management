import { Component, Input, computed, signal } from '@angular/core';
import { CommonModule } from '@angular/common';

export type BadgeStatus = 'success' | 'warning' | 'error' | 'info' | 'default';

@Component({
    selector: 'app-status-badge',
    standalone: true,
    imports: [CommonModule],
    templateUrl: './status-badge.component.html',
    styleUrls: ['./status-badge.component.scss']
})
export class StatusBadgeComponent {

    // The raw enum/text value to display
    @Input({ required: true })
    set value(val: string) {
        this._value.set(val?.trim().toUpperCase() || '');
    }

    // Explicitly override the color status if needed, otherwise it auto-calculates
    @Input()
    set status(val: BadgeStatus) {
        this._explicitStatus.set(val);
    }

    private _value = signal<string>('');
    private _explicitStatus = signal<BadgeStatus | null>(null);

    // Expose signal for template
    public displayValue = this._value;

    public badgeClass = computed(() => {
        const explicit = this._explicitStatus();
        if (explicit) return `badge-${explicit}`;

        const val = this._value();

        // Auto-map common backend statuses to colors
        if (['AVAILABLE', 'ACTIVE', 'COMPLETED', 'DELIVERED', 'BOOKED'].includes(val)) {
            return 'badge-success';
        }
        if (['INACTIVE', 'EXPIRED', 'CANCELLED', 'FAILED', 'DELETED'].includes(val)) {
            return 'badge-error';
        }
        if (['MAINTENANCE', 'IN_TRANSIT', 'PENDING', 'ON_HOLD'].includes(val)) {
            return 'badge-warning';
        }

        return 'badge-default';
    });
}
