import { Injectable, signal } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class UIStore {
  private readonly _sidebarCollapsed = signal(false);
  private readonly _theme = signal<'dark' | 'light'>('dark');
  private readonly _isLoading = signal(false);
  private readonly _loadingMessage = signal<string>('');
  private readonly _isMobile = signal(false);

  readonly sidebarCollapsed = this._sidebarCollapsed.asReadonly();
  readonly theme = this._theme.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly loadingMessage = this._loadingMessage.asReadonly();
  readonly isMobile = this._isMobile.asReadonly();

  toggleSidebar(): void {
    this._sidebarCollapsed.set(!this._sidebarCollapsed());
  }

  setSidebarCollapsed(collapsed: boolean): void {
    this._sidebarCollapsed.set(collapsed);
  }

  setTheme(theme: 'dark' | 'light'): void {
    this._theme.set(theme);
  }

  setLoading(loading: boolean, message?: string): void {
    this._isLoading.set(loading);
    this._loadingMessage.set(message ?? '');
  }

  setMobile(isMobile: boolean): void {
    this._isMobile.set(isMobile);
  }
}
