import { CanActivateFn, Router } from '@angular/router';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const roleGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const requiredRoles = route.data?.['roles'] as string[] | undefined;

  if (!authService.isAuthenticated()) {
    router.navigate(['/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }

  if (!requiredRoles || requiredRoles.length === 0) {
    return true;
  }

  const hasRole = requiredRoles.some(role => authService.hasRole(role));

  if (!hasRole) {
    router.navigate(['/dashboard']);
    return false;
  }

  return true;
};
