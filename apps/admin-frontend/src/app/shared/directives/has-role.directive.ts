import { Directive, Input, TemplateRef, ViewContainerRef, inject, effect } from '@angular/core';
import { PermissionService } from '../../core/auth/permission.service';

@Directive({
    selector: '[appHasRole]',
    standalone: true
})
export class HasRoleDirective {
    private templateRef = inject(TemplateRef<any>);
    private viewContainer = inject(ViewContainerRef);
    private permissionService = inject(PermissionService);

    private requiredRoles: string[] = [];
    private hasView = false;

    @Input()
    set appHasRole(roles: string[]) {
        this.requiredRoles = roles;
        this.updateView();
    }

    constructor() {
        // Re-evaluate whenever current roles change
        effect(() => {
            // Accessing the signal ensures this effect re-runs when roles update
            this.permissionService.currentRoles();
            this.updateView();
        });
    }

    private updateView() {
        const hasAccess = this.permissionService.hasAnyRole(this.requiredRoles);

        if (hasAccess && !this.hasView) {
            this.viewContainer.createEmbeddedView(this.templateRef);
            this.hasView = true;
        } else if (!hasAccess && this.hasView) {
            this.viewContainer.clear();
            this.hasView = false;
        }
    }
}
