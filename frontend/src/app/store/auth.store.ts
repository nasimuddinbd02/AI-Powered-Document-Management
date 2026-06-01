import { Injectable, signal, computed } from '@angular/core';
import { User } from '../core/models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthStore {
  private readonly _currentUser = signal<User | null>(null);
  private readonly _token = signal<string | null>(null);
  private readonly _isLoading = signal(false);
  private readonly _error = signal<string | null>(null);

  readonly currentUser = this._currentUser.asReadonly();
  readonly token = this._token.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly error = this._error.asReadonly();
  readonly isAuthenticated = computed(() => !!this._token() && !!this._currentUser());
  readonly userRole = computed(() => this._currentUser()?.role?.name ?? 'user');
  readonly userAvatar = computed(() => this._currentUser()?.avatar ?? '');
  readonly userName = computed(() => this._currentUser()?.name ?? 'User');

  setUser(user: User | null): void {
    this._currentUser.set(user);
  }

  setToken(token: string | null): void {
    this._token.set(token);
  }

  setLoading(loading: boolean): void {
    this._isLoading.set(loading);
  }

  setError(error: string | null): void {
    this._error.set(error);
  }

  clear(): void {
    this._currentUser.set(null);
    this._token.set(null);
    this._error.set(null);
    this._isLoading.set(false);
  }
}
