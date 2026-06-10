import { Component, inject, OnInit, signal, computed } from '@angular/core';
import { CommonModule, DecimalPipe, PercentPipe } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTableModule } from '@angular/material/table';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

import {
    ReportService,
    ReportSummary,
    LoadTrendPoint,
    ClientRevenueItem,
    DriverPerformanceItem,
    TruckUtilizationItem,
} from '../services/report.service';
import { NotificationService } from '../../../core/services/notification.service';

interface StatusBar {
    label: string;
    key: keyof ReportSummary['loads_by_status'];
    color: string;
}

@Component({
    selector: 'app-reports-dashboard',
    standalone: true,
    imports: [
        CommonModule,
        DecimalPipe,
        PercentPipe,
        MatCardModule,
        MatIconModule,
        MatTabsModule,
        MatTableModule,
        MatProgressBarModule,
        MatProgressSpinnerModule,
        MatDividerModule,
        MatChipsModule,
    ],
    templateUrl: './reports-dashboard.component.html',
    styleUrl: './reports-dashboard.component.scss',
})
export class ReportsDashboardComponent implements OnInit {
    private reportService = inject(ReportService);
    private notification = inject(NotificationService);

    summary = signal<ReportSummary | null>(null);
    trend = signal<LoadTrendPoint[]>([]);
    revenue = signal<ClientRevenueItem[]>([]);
    revenueTotal = signal({ total_freight: 0, total_advance: 0, total_outstanding: 0 });
    drivers = signal<DriverPerformanceItem[]>([]);
    trucks = signal<TruckUtilizationItem[]>([]);
    truckByStatus = signal<Record<string, number>>({});

    loading = signal(true);

    readonly statusBars: StatusBar[] = [
        { label: 'Delivered', key: 'delivered', color: 'accent' },
        { label: 'In Transit', key: 'in_transit', color: 'primary' },
        { label: 'Confirmed', key: 'confirmed', color: 'primary' },
        { label: 'Allocated', key: 'allocated', color: 'primary' },
        { label: 'Draft', key: 'draft', color: 'primary' },
        { label: 'Cancelled', key: 'cancelled', color: 'warn' },
    ];

    readonly trendColumns = ['period', 'total', 'delivered', 'cancelled'];
    readonly revenueColumns = ['client_name', 'load_count', 'total_freight', 'total_advance', 'total_outstanding'];
    readonly driverColumns = ['driver_name', 'total_trips', 'trips_completed', 'trips_cancelled', 'on_time_deliveries'];
    readonly truckColumns = ['registration_no', 'status', 'trips_completed'];

    statusPercent = computed((): Record<string, number | undefined> => {
        const s = this.summary();
        if (!s || s.total_loads === 0) return {};
        const total = s.total_loads;
        const map: Record<string, number> = {};
        for (const bar of this.statusBars) {
            map[bar.key] = (s.loads_by_status[bar.key] / total) * 100;
        }
        return map;
    });

    statusCount = computed((): Record<string, number | undefined> => {
        const s = this.summary();
        if (!s) return {};
        return s.loads_by_status as unknown as Record<string, number>;
    });

    ngOnInit(): void {
        this.loadAll();
    }

    loadAll(): void {
        this.loading.set(true);

        this.reportService.getSummary().subscribe({
            next: (data) => this.summary.set(data),
            error: () => this.notification.showError('Failed to load summary'),
        });

        this.reportService.getLoadTrend(12).subscribe({
            next: (res) => this.trend.set(res.data),
            error: () => {},
        });

        this.reportService.getRevenue().subscribe({
            next: (res) => {
                this.revenue.set(res.by_client);
                this.revenueTotal.set({
                    total_freight: res.total_freight,
                    total_advance: res.total_advance,
                    total_outstanding: res.total_outstanding,
                });
            },
            error: () => {},
        });

        this.reportService.getDriverPerformance().subscribe({
            next: (res) => this.drivers.set(res.drivers),
            error: () => {},
        });

        this.reportService.getTruckUtilization().subscribe({
            next: (res) => {
                this.trucks.set(res.trucks);
                this.truckByStatus.set(res.by_status);
                this.loading.set(false);
            },
            error: () => this.loading.set(false),
        });
    }

    formatCurrency(value: number): string {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0,
        }).format(value);
    }

    truckStatusEntries(): Array<{ status: string; count: number }> {
        return Object.entries(this.truckByStatus()).map(([status, count]) => ({ status, count }));
    }

    onTimeRate(d: DriverPerformanceItem): number {
        if (d.trips_completed === 0) return 0;
        return d.on_time_deliveries / d.trips_completed;
    }
}
