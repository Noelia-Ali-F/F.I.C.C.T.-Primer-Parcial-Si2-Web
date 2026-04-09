import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

type HeroBenefit = {
  title: string;
  description: string;
  icon: string;
};

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="home-showcase">
      <section class="hero-banner">
        <div class="hero-overlay"></div>

        <div class="hero-grid">
          <div class="hero-copy">
            <p class="hero-kicker">Red nacional de talleres afiliados</p>
            <h1>¿QUIERES REGISTRAR TU TALLER EN NUESTRA RED?</h1>
            <p class="hero-intro">
              Impulsa tu taller con clientes verificados, solicitudes de auxilio en tiempo real y acompañamiento comercial desde el primer día.
            </p>
            <p class="hero-highlight">
              <span>Más clientes, más servicios,</span>
              <span>más oportunidades</span>
              <span class="light">para crecer</span>
            </p>

            <article class="register-card">
              <p class="card-eyebrow">Afiliación inmediata</p>
              <h2>Registra tu taller mecánico</h2>
              <p class="card-lead">
                Únete a nuestra red y aumenta tus ingresos atendiendo emergencias cerca de ti.
              </p>

              <form class="register-form">
                <label>
                  <span>Nombre del Taller</span>
                  <input type="text" placeholder="Nombre del Taller" />
                </label>

                <label>
                  <span>Nombre Responsable</span>
                  <input type="text" placeholder="Nombre Responsable" />
                </label>

                <label>
                  <span>Número Telefónico</span>
                  <input type="tel" placeholder="Número Telefónico" />
                </label>

                <label>
                  <span>Correo Electrónico</span>
                  <input type="email" placeholder="Correo Electrónico" />
                </label>

                <label>
                  <span>Dirección del Taller</span>
                  <select>
                    <option value="">Selecciona una zona</option>
                    <option *ngFor="let zone of workshopZones" [value]="zone">{{ zone }}</option>
                  </select>
                </label>

                <label>
                  <span>Tipo de Especialidades</span>
                  <select>
                    <option value="">Selecciona una especialidad</option>
                    <option *ngFor="let specialty of specialties" [value]="specialty">
                      {{ specialty }}
                    </option>
                  </select>
                </label>

                <label class="full-width">
                  <span>Comentarios (Opcional)</span>
                  <textarea rows="3" placeholder="Comentarios (Opcional)"></textarea>
                </label>

                <p class="terms-copy">
                  Al registrarte aceptas nuestros Términos y Condiciones y Política de Privacidad.
                </p>

                <div class="form-actions">
                  <a class="cta-primary" routerLink="/planes">Registrar taller</a>
                  <a class="cta-secondary" routerLink="/contacto">Solicitar asesoría</a>
                </div>
              </form>
            </article>
          </div>

          <div class="hero-side">
            <div class="mechanic-spotlight" aria-hidden="true">
              <div class="spotlight-halo"></div>
              <div class="mechanic-card">
                <div class="mechanic-tag">Servicio 24/7</div>
                <div class="mechanic-portrait"></div>
              </div>
            </div>

            <aside class="contact-card">
              <p class="contact-kicker">Atención inmediata</p>
              <h2>¿Tienes preguntas? ¡Contáctanos!</h2>

              <a class="contact-action phone" href="tel:800163316">
                <span class="icon">☎</span>
                <span class="contact-text">
                  <strong>800 16 3316</strong>
                  <small>Línea gratuita</small>
                </span>
              </a>

              <a class="contact-action whatsapp" href="https://wa.me/59177795636" target="_blank" rel="noreferrer">
                <span class="icon">W</span>
                <span class="contact-text">
                  <strong>777 95 636</strong>
                  <small>Por WhatsApp</small>
                </span>
              </a>
            </aside>
          </div>
        </div>
      </section>

      <section class="benefits-panel">
        <div class="benefits-head">
          <p class="benefits-kicker">Crecimiento para talleres aliados</p>
          <h2>Beneficios de unirte a nuestra red</h2>
        </div>

        <div class="benefits-grid">
          <article class="benefit-card" *ngFor="let benefit of benefits">
            <span class="benefit-icon">{{ benefit.icon }}</span>
            <div>
              <h3>{{ benefit.title }}</h3>
              <p>{{ benefit.description }}</p>
            </div>
          </article>
        </div>
      </section>
    </main>
  `,
  styleUrl: './home-page.component.css',
})
export class HomePageComponent {
  readonly workshopZones = [
    'Equipetrol',
    'Centro',
    'Plan Tres Mil',
    'Norte integrado',
    'Doble vía a La Guardia',
  ];

  readonly specialties = [
    'Auxilio mecánico',
    'Electricidad automotriz',
    'Baterías y arranque',
    'Cambio de neumáticos',
    'Grúa y remolque',
  ];

  readonly benefits: HeroBenefit[] = [
    {
      title: 'Oportunidades constantes',
      description: 'Recibe solicitudes de asistencia en tiempo real y mejora la ocupación diaria de tu taller.',
      icon: '◉',
    },
    {
      title: 'Acceso a IA avanzada',
      description: 'Diagnóstico rápido automatizado para evaluar emergencias y asignar prioridad.',
      icon: '◎',
    },
    {
      title: 'Expansión de clientes',
      description: 'Incrementa tu visibilidad y tu base de clientes con emergencias locales.',
      icon: '◌',
    },
  ];
}
