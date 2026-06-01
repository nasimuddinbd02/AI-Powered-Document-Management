import { Injectable, signal, computed } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap, catchError, throwError, BehaviorSubject } from 'rxjs';
import { environment } from '../../../environments/environment';
import { User, LoginRequest, LoginResponse, RegisterRequest } from '../models/user.model';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly apiUrl = `${environment.apiUrl}/auth`;

  private readonly _currentUser = signal<User | null>(null);
  private readonly _token = signal<string | null>(null);
  private readonly _isLoading = signal(false);

  readonly currentUser = this._currentUser.asReadonly();
  readonly token = this._token.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly isAuthenticated = computed(() => !!this._token() && !!this._currentUser());

  private refreshTokenTimeout: any;

  constructor(private http: HttpClient, private router: Router) {
    this.loadStoredAuth();
  }

  private loadStoredAuth(): void {
    const token = localStorage.getItem('access_token') || sessionStorage.getItem('access_token');
    const userStr = localStorage.getItem('user') || sessionStorage.getItem('user');

    if (token && userStr) {
      try {
        const user = JSON.parse(userStr);
        this._token.set(token);
        this._currentUser.set(user);
      } catch {
        this.clearStorage();
      }
    }
  }

  login(request: LoginRequest): Observable<LoginResponse> {
    this._isLoading.set(true);
    return this.http.post<LoginResponse>(`${this.apiUrl}/login/`, request).pipe(
      tap(response => {
        this.handleAuthResponse(response, request.rememberMe);
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        return throwError(() => error);
      })
    );
  }

  register(request: RegisterRequest): Observable<LoginResponse> {
    this._isLoading.set(true);
    const backendPayload = {
      email: request.email,
      username: request.email.split('@')[0],
      first_name: request.name.split(' ')[0],
      last_name: request.name.split(' ').slice(1).join(' '),
      password: request.password,
      password_confirm: request.confirmPassword,
      department: request.department || ''
    };
    return this.http.post<LoginResponse>(`${this.apiUrl}/register/`, backendPayload).pipe(
      tap(response => {
        this.handleAuthResponse(response, false);
        this._isLoading.set(false);
      }),
      catchError(error => {
        this._isLoading.set(false);
        return throwError(() => error);
      })
    );
  }

  refreshToken(): Observable<LoginResponse> {
    const refreshToken = localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
    return this.http.post<LoginResponse>(`${this.apiUrl}/refresh/`, { refresh: refreshToken }).pipe(
      tap(response => this.handleAuthResponse(response, !!localStorage.getItem('refresh_token'))),
      catchError(error => {
        this.logout();
        return throwError(() => error);
      })
    );
  }

  logout(): void {
    const token = this._token();
    if (token) {
      this.http.post(`${this.apiUrl}/logout/`, {}).subscribe({ error: () => {} });
    }
    this.clearStorage();
    this._currentUser.set(null);
    this._token.set(null);
    if (this.refreshTokenTimeout) {
      clearTimeout(this.refreshTokenTimeout);
    }
    this.router.navigate(['/login']);
  }

  getCurrentUser(): Observable<User> {
    return this.http.get<User>(`${this.apiUrl}/me/`).pipe(
      tap(user => this._currentUser.set(user))
    );
  }

  getToken(): string | null {
    return this._token();
  }

  hasRole(roleName: string): boolean {
    const user = this._currentUser();
    return user?.role?.name === roleName;
  }

  hasPermission(resource: string, action: string): boolean {
    const user = this._currentUser();
    if (!user?.role?.permissions) return false;
    return user.role.permissions.some(p => p.resource === resource && p.action === action);
  }

  private handleAuthResponse(response: any, rememberMe?: boolean): void {
    const data = response.data || response;
    const tokens = data.tokens || data;
    const access = tokens.access || response.accessToken;
    const refresh = tokens.refresh || response.refreshToken;
    const user = data.user || response.user;

    const storage = rememberMe ? localStorage : sessionStorage;
    storage.setItem('access_token', access);
    storage.setItem('refresh_token', refresh);
    storage.setItem('user', JSON.stringify(user));

    this._token.set(access);
    this._currentUser.set(user);

    // Schedule token refresh 55 minutes later
    const expiresInMs = 55 * 60 * 1000;
    this.refreshTokenTimeout = setTimeout(() => {
      this.refreshToken().subscribe();
    }, expiresInMs);
  }

  private clearStorage(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    sessionStorage.removeItem('access_token');
    sessionStorage.removeItem('refresh_token');
    sessionStorage.removeItem('user');
  }
}
