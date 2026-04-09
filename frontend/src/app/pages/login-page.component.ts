import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
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

            <form class="login-clean-form">
              <label class="form-field">
                <span>Correo electrónico</span>
                <input
                  type="email"
                  name="email"
                  [(ngModel)]="form.email"
                  placeholder="ejemplo@talleracb.com"
                />
              </label>

              <label class="form-field">
                <span>Contraseña</span>
                <input
                  type="password"
                  name="password"
                  [(ngModel)]="form.password"
                  placeholder="Ingresa tu contraseña"
                />
              </label>

              <a class="button primary login-clean-submit" routerLink="/dashboard">Ingresar</a>

              <label class="login-clean-option is-checked">
                <input type="checkbox" name="remember" [(ngModel)]="form.remember" />
                <span>Mantener sesión iniciada</span>
              </label>

              <a class="login-clean-option" routerLink="/contacto">¿Olvidaste tu contraseña?</a>
            </form>
          </article>
        </div>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class LoginPageComponent {
  selectedRole: 'socio' | 'admin' = 'socio';

  form = {
    email: '',
    password: '',
    remember: true,
  };
}
