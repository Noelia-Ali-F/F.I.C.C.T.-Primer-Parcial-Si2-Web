import { CommonModule } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { API_BASE_URL } from '../api-base';
import { clearStoredSession } from '../session';
import { ValidationDialogComponent } from './validation-dialog.component';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, RouterLink],
  template: `
    <main class="page login-clean-page">
      <section class="login-clean-shell">
        <div class="login-clean-card">
          <div class="login-clean-art">
            <img src="/hero-grua-scene.svg" alt="Escena ilustrada del taller" />
          </div>

          <article class="login-clean-form-card">
            <div class="login-clean-tabs">
              <button
                type="button"
                [class.is-active]="selectedRole === 'socio'"
                (click)="selectedRole = 'socio'"
              >
                Socio del Taller
              </button>
              <button
                type="button"
                [class.is-active]="selectedRole === 'admin'"
                (click)="selectedRole = 'admin'"
              >
                Administrador
              </button>
            </div>

            <h1>Inicio de Sesión</h1>

            <form class="login-clean-form" (ngSubmit)="submitLogin(loginForm)" #loginForm="ngForm">
              <label class="form-field">
                <span>Correo electrónico</span>
                <input
                  type="email"
                  name="email"
                  [(ngModel)]="form.email"
                  required
                  email
                  placeholder="ejemplo@talleracb.com"
                />
              </label>

              <label class="form-field">
                <span>Contraseña</span>
                <span class="password-field">
                  <input
                    [type]="showPassword ? 'text' : 'password'"
                    name="password"
                    [(ngModel)]="form.password"
                    required
                    placeholder="Ingresa tu contraseña"
                  />
                  <button
                    class="password-toggle"
                    type="button"
                    (click)="showPassword = !showPassword"
                    [attr.aria-label]="showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'"
                  >
                    {{ showPassword ? '🙈' : '👁' }}
                  </button>
                </span>
              </label>

              <p class="login-clean-feedback" *ngIf="submitMessage">{{ submitMessage }}</p>

              <button class="button primary login-clean-submit" type="submit" [disabled]="isSubmitting">
                {{ isSubmitting ? 'Ingresando...' : 'Ingresar' }}
              </button>

              <label class="login-clean-option is-checked">
                <input type="checkbox" name="remember" [(ngModel)]="form.remember" />
                <span>Mantener sesión iniciada</span>
              </label>

              <a class="login-clean-option" routerLink="/forgot-password">¿Olvidaste tu contraseña?</a>
            </form>
          </article>
        </div>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class LoginPageComponent {
  private readonly emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  private readonly http = inject(HttpClient);
  private readonly dialog = inject(MatDialog);
  private readonly router = inject(Router);
  private readonly loginApiUrl = `${API_BASE_URL}/auth/login`;
  private readonly appSessionStorageKey = 'acb_session';

  selectedRole: 'socio' | 'admin' = 'admin';
  showPassword = false;
  submitMessage = '';
  isSubmitting = false;

  form = {
    email: '',
    password: '',
    remember: true,
  };

  submitLogin(loginForm: NgForm): void {
    if (this.isSubmitting) {
      return;
    }

    const missingFields = this.getMissingFields();

    if (missingFields.length > 0 || loginForm.invalid) {
      this.submitMessage = 'Completa el formulario para continuar.';
      this.openValidationDialog(missingFields);
      return;
    }

    this.isSubmitting = true;
    this.submitMessage = '';
    clearStoredSession();

    this.http
      .post<LoginResponse>(this.loginApiUrl, {
        email: this.form.email.trim().toLowerCase(),
        password: this.form.password,
      })
      .subscribe({
        next: async (response) => {
          if (response.requires_password_change) {
            this.isSubmitting = false;
            this.submitMessage = '';
            void this.router.navigate(['/forgot-password'], {
              queryParams: {
                email: response.email || this.form.email.trim().toLowerCase(),
                source: 'workshop-initial-login',
              },
            });
            return;
          }

          const expectedRole = this.selectedRole === 'admin' ? 'admin' : 'workshop';

          if (response.role !== expectedRole) {
            this.isSubmitting = false;
            this.submitMessage =
              this.selectedRole === 'admin'
                ? 'Esta pantalla está reservada para la cuenta administradora.'
                : 'Este acceso corresponde a un usuario diferente.';
            return;
          }

          this.persistSession(response);
          this.isSubmitting = false;
          await this.router.navigate(['/dashboard']);
        },
        error: (error: HttpErrorResponse) => {
          this.isSubmitting = false;
          const detail = error.error?.detail;

          if (
            error.status === 403 &&
            detail &&
            typeof detail === 'object' &&
            detail.code === 'WORKSHOP_PASSWORD_CHANGE_REQUIRED'
          ) {
            this.submitMessage = '';
            void this.router.navigate(['/forgot-password'], {
              queryParams: {
                email: detail.email || this.form.email.trim().toLowerCase(),
                source: 'workshop-initial-login',
              },
            });
            return;
          }

          this.submitMessage =
            (typeof detail === 'string' ? detail : detail?.message) ||
            'No se pudo iniciar sesión. Inténtalo nuevamente.';
        },
      });
  }

  private getMissingFields(): string[] {
    const missingFields: string[] = [];

    const email = this.form.email.trim();

    if (!email) {
      missingFields.push('Correo Electrónico');
    } else if (!this.emailPattern.test(email)) {
      missingFields.push('Correo Electrónico válido');
    }

    if (!this.form.password.trim()) {
      missingFields.push('Contraseña');
    }

    return missingFields;
  }

  private openValidationDialog(missingFields: string[]): void {
    this.dialog.open(ValidationDialogComponent, {
      width: '26rem',
      maxWidth: 'calc(100vw - 2rem)',
      data: { missingFields },
    });
  }

  private persistSession(response: LoginResponse): void {
    const storage = this.form.remember ? window.localStorage : window.sessionStorage;
    const payload = JSON.stringify({
      id: response.id,
      email: response.email,
      fullName: response.full_name,
      phone: response.phone,
      role: response.role,
      status: response.status,
      accessToken: response.access_token,
      tokenType: response.token_type,
    });

    window.localStorage.removeItem(this.appSessionStorageKey);
    window.sessionStorage.removeItem(this.appSessionStorageKey);
    storage.setItem(this.appSessionStorageKey, payload);
  }
}

type LoginResponse = {
  id: number;
  email: string;
  full_name: string;
  phone: string;
  role: string;
  status: string;
  requires_password_change: boolean;
  access_token: string | null;
  token_type: string | null;
};
