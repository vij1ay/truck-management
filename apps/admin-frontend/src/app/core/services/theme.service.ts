import { Injectable, signal, effect } from '@angular/core';

@Injectable({
    providedIn: 'root'
})
export class ThemeService {
    private readonly THEME_KEY = 'app-theme-preference';

    // Signal to hold the current theme state
    public isDarkTheme = signal<boolean>(this.getInitialThemePreference());

    constructor() {
        // Effect runs whenever the signal value changes
        effect(() => {
            const isDark = this.isDarkTheme();
            this.applyTheme(isDark);
            this.saveThemePreference(isDark);
        });
    }

    public toggleTheme(): void {
        this.isDarkTheme.set(!this.isDarkTheme());
    }

    private getInitialThemePreference(): boolean {
        const savedTheme = localStorage.getItem(this.THEME_KEY);
        if (savedTheme) {
            return savedTheme === 'dark';
        }
        // Fallback to system preference
        return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }

    private applyTheme(isDark: boolean): void {
        if (isDark) {
            document.body.classList.add('dark-theme');
        } else {
            document.body.classList.remove('dark-theme');
        }
    }

    private saveThemePreference(isDark: boolean): void {
        localStorage.setItem(this.THEME_KEY, isDark ? 'dark' : 'light');
    }
}
