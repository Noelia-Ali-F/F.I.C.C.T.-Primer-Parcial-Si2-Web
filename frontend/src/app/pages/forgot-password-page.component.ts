import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';

import { ValidationDialogComponent } from './validation-dialog.component';

@Component({
  selector: 'app-forgot-password-page',
  standalone: true,
  imports: [CommonModule, FormsModule, MatDialogModule, RouterLink],
  template: `
    <main class="page login-clean-page forgot-password-page">
      <section class="login-clean-shell">
        <div class="login-clean-card">
          <div class="login-clean-art">
            <img src="/hero-grua-scene.svg" alt="Recuperación de contraseña" />
          </div>

          <article class="login-clean-form-card">
            <span class="forgot-password-eyebrow">Soporte de acceso</span>
            <h1>¿Olvidaste tu contraseña?</h1>
            <p class="forgot-password-copy">
              Ingresa tu correo electrónico y te enviaremos instrucciones para recuperar el acceso.
            </p>

            <form class="login-clean-form" (ngSubmit)="submitRecovery(recoveryForm)" #recoveryForm="ngForm">
              <label class="form-field">
                <span>Correo electrónico</span>
                <input
                  type="email"
                  name="email"
                  [(ngModel)]="email"
                  required
                  email
                  placeholder="ejemplo@talleracb.com"
                />
              </label>

              <p class="login-clean-feedback" *ngIf="submitMessage">{{ submitMessage }}</p>

              <button class="button primary login-clean-submit" type="submit">
                Enviar instrucciones
              </button>

              <a class="login-clean-option forgot-password-back" routerLink="/login">
                Volver al inicio de sesión
              </a>
            </form>
          </article>
        </div>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class ForgotPasswordPageComponent {
  private readonly dialog = inject(MatDialog);
  private readonly emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  email = '';
  submitMessage = '';

  submitRecovery(recoveryForm: NgForm): void {
    const missingFields: string[] = [];
    const normalizedEmail = this.email.trim();

    if (!normalizedEmail) {
      missingFields.push('Correo Electrónico');
    } else if (!this.emailPattern.test(normalizedEmail)) {
      missingFields.push('Correo Electrónico válido');
    }

    if (missingFields.length > 0 || recoveryForm.invalid) {
      this.submitMessage = 'Completa un correo electrónico válido para continuar.';
      this.dialog.open(ValidationDialogComponent, {
        width: '26rem',
        maxWidth: 'calc(100vw - 2rem)',
        data: { missingFields },
      });
      return;
    }

    this.submitMessage =
      'Te enviamos instrucciones de recuperación al correo registrado si existe en el sistema.';
    this.email = '';
    recoveryForm.resetForm();
  }
}
