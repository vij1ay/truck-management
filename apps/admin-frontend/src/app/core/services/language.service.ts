import { Injectable, signal, effect, inject } from '@angular/core';
import { TranslateService } from '@ngx-translate/core';

@Injectable({
    providedIn: 'root'
})
export class LanguageService {
    private readonly LANG_KEY = 'app-language';
    private translate = inject(TranslateService);

    public currentLang = signal<string>(this.getInitialLanguage());

    constructor() {
        this.translate.addLangs(['en']); // Add more locales here like 'es', 'fr'
        this.translate.setDefaultLang('en');

        // Effect updates translation service when signal changes
        effect(() => {
            const lang = this.currentLang();
            this.translate.use(lang);
            localStorage.setItem(this.LANG_KEY, lang);
        });
    }

    public setLanguage(lang: string): void {
        if (this.translate.getLangs().includes(lang)) {
            this.currentLang.set(lang);
        }
    }

    private getInitialLanguage(): string {
        const savedLang = localStorage.getItem(this.LANG_KEY);
        return savedLang || 'en';
    }
}
