import { Component, OnInit, inject, signal, computed } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet, RouterModule } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { TranslateModule } from '@ngx-translate/core';

import { ThemeService } from '../../core/services/theme.service';
import { AuthService } from '../../core/auth/auth.service';
import { PortalService, PortalCarrierLink } from '../../features/portal/services/portal.service';

@Component({
    selector: 'app-portal-layout',
    standalone: true,
    imports: [
        CommonModule,
        RouterModule,
        RouterOutlet,
        MatToolbarModule,
        MatButtonModule,
        MatIconModule,
        MatMenuModule,
        TranslateModule,
    ],
    templateUrl: './portal-layout.component.html',
    styleUrl: './portal-layout.component.scss',
})
export class PortalLayoutComponent implements OnInit {
    public themeService = inject(ThemeService);
    public authService = inject(AuthService);
    private portalService = inject(PortalService);

    public carriers = signal<PortalCarrierLink[]>([]);

    /** Brand title — the shipper's company name (from the first linked carrier
     * relationship), or a generic fallback when the link can't be resolved. */
    public companyName = computed(() => this.carriers()[0]?.client?.company_name ?? 'Customer Portal');

    ngOnInit(): void {
        this.portalService.getMyProfile().subscribe({
            next: (res) => this.carriers.set(res.carriers),
            error: () => this.carriers.set([]),
        });
    }

    toggleTheme(): void {
        this.themeService.toggleTheme();
    }

    logout(): void {
        this.authService.logout();
    }
}
