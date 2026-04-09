import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

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

              <button class="button primary login-clean-submit" type="submit">Ingresar</button>

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
  private readonly dialog = inject(MatDialog);
  private readonly router = inject(Router);

  selectedRole: 'socio' | 'admin' = 'socio';
  showPassword = false;
  submitMessage = '';

  form = {
    email: '',
    password: '',
    remember: true,
  };

  submitLogin(loginForm: NgForm): void {
    const missingFields = this.getMissingFields();

    if (missingFields.length > 0 || loginForm.invalid) {
      this.submitMessage = 'Completa el formulario para continuar.';
      this.openValidationDialog(missingFields);
      return;
    }

    this.submitMessage = '';
    void this.router.navigate(['/dashboard']);
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
}
