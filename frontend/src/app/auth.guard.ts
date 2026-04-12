import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

const APP_SESSION_STORAGE_KEY = 'acb_session';

export const authGuard: CanActivateFn = () => {
  const router = inject(Router);
  const rawSession =
    window.localStorage.getItem(APP_SESSION_STORAGE_KEY) ||
    window.sessionStorage.getItem(APP_SESSION_STORAGE_KEY);

  if (!rawSession) {
    return router.createUrlTree(['/login']);
  }

  try {
    JSON.parse(rawSession);
    return true;
  } catch {
    window.localStorage.removeItem(APP_SESSION_STORAGE_KEY);
    window.sessionStorage.removeItem(APP_SESSION_STORAGE_KEY);
    return router.createUrlTree(['/login']);
  }
};
