import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { FormsModule, NgForm } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
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

            <p class="login-clean-feedback" *ngIf="showWorkshopResetMessage">
              Detectamos un ingreso con contraseña temporal. Antes de acceder al sistema, debes registrar una nueva contraseña para el correo indicado.
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
  private readonly route = inject(ActivatedRoute);
  private readonly emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

  email = '';
  submitMessage = '';
  showWorkshopResetMessage = false;

  constructor() {
    this.route.queryParamMap.subscribe((params) => {
      this.email = params.get('email')?.trim() ?? '';
      this.showWorkshopResetMessage = params.get('source') === 'workshop-initial-login';
    });
  }

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
    recoveryForm.resetForm({
      email: this.email,
    });
  }
}
