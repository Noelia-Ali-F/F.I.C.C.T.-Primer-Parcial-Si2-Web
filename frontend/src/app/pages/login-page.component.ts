import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <main class="page">
      <section class="login-layout single-login">
        <article class="login-panel">
          <p class="eyebrow">Acceso</p>
          <h1>Iniciar sesión</h1>
          <p class="lead">
            Accede a la plataforma para gestionar solicitudes, talleres asociados y servicios de
            auxilio dentro de la red.
          </p>

          <form class="login-form">
            <label class="form-field">
              <span>Correo electrónico</span>
              <input
                type="email"
                name="email"
                [(ngModel)]="form.email"
                placeholder="correo@ejemplo.com"
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

            <div class="login-actions">
              <label class="remember-row">
                <input type="checkbox" name="remember" [(ngModel)]="form.remember" />
                <span>Recordarme</span>
              </label>

              <a routerLink="/contacto">¿Olvidaste tu contraseña?</a>
            </div>

            <div class="form-actions">
              <a class="button secondary" routerLink="/suscripciones">Quiero asociarme</a>
              <a class="button primary" routerLink="/dashboard">Ingresar</a>
            </div>
          </form>
        </article>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class LoginPageComponent {
  form = {
    email: '',
    password: '',
    remember: false,
  };
}
