import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, OnDestroy, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { faqItems, heroHighlights, newsCards, serviceCards } from '../site-content';

type QuickServiceOption = {
  label: string;
  title: string;
  description: string;
  eta: string;
};

@Component({
  selector: 'app-home-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="page">
      <section class="hero">
        <div class="hero-copy">
          <p class="eyebrow">Servicio De Grúa</p>
          <h1>Auxilio mecánico con presencia, cobertura y atención inmediata.</h1>
          <p class="lead">
            Inspirado en la captura del sitio real, este hero pone al frente la asistencia vial,
            la identidad institucional y una imagen más fuerte de operación en carretera.
          </p>

          <div class="cta-row">
            <a class="button primary" routerLink="/contacto">Contáctanos</a>
            <a class="button secondary" routerLink="/servicios">Ver servicios</a>
          </div>

          <div class="hero-hotlines">
            <div>
              <span>Línea gratuita</span>
              <strong>800 16 3316</strong>
            </div>
            <div>
              <span>WhatsApp</span>
              <strong>777 95 636</strong>
            </div>
          </div>
        </div>

        <div class="hero-panel">
          <img class="hero-scene" src="/hero-grua-scene.svg" alt="Ilustración de grúas de auxilio" />
          <div class="hero-badge">
            <p>24/7</p>
            <span>Cobertura en ciudad, carretera y provincias</span>
          </div>
        </div>
      </section>

      <section class="mini-stats">
        <article>
          <strong>24/7</strong>
          <span>auxilio y atención</span>
        </article>
        <article>
          <strong>6+</strong>
          <span>vistas institucionales activas</span>
        </article>
        <article>
          <strong>100%</strong>
          <span>Angular moderno con Docker</span>
        </article>
      </section>

      <section class="section">
        <div class="section-head">
          <p class="eyebrow">Nuestros Servicios</p>
          <h2>Servicios pensados para acompañar cada trayecto</h2>
        </div>

        <div class="services-stage">
          <div class="services-stack">
            <article
              class="info-card service-card"
              *ngFor="let card of orderedServices"
            >
              <span class="service-index">0{{ card.index + 1 }}</span>
              <h3>{{ card.title }}</h3>
              <p>{{ card.description }}</p>
            </article>
          </div>

          <aside class="quote-shell" aria-label="Selección rápida de servicios">
            <p class="eyebrow quote-eyebrow">Elegí tu servicio</p>
            <h3>Obtén un presupuesto inmediato para la asistencia que necesitas.</h3>

            <label class="quote-label" for="service-selector">Selecciona el servicio</label>
            <select
              id="service-selector"
              class="service-selector"
              [value]="selectedQuickServiceLabel"
              (change)="selectQuickService($any($event.target).value)"
            >
              <option *ngFor="let option of quickServiceOptions" [value]="option.label">
                {{ option.label }}
              </option>
            </select>

            <article class="quote-preview">
              <span class="quote-chip">Respuesta inmediata</span>
              <h4>{{ selectedQuickService.title }}</h4>
              <p>{{ selectedQuickService.description }}</p>

              <div class="quote-meta">
                <div>
                  <span>Tiempo estimado</span>
                  <strong>{{ selectedQuickService.eta }}</strong>
                </div>
                <a class="button primary" routerLink="/contacto">Solicitar ahora</a>
              </div>
            </article>
          </aside>
        </div>
      </section>

      <section class="spotlight">
        <div>
          <p class="eyebrow">Historia</p>
          <h2>Una institución con memoria, deporte y comunidad.</h2>
          <p>
            El estilo de la referencia funciona mejor cuando mezcla autoridad institucional con una
            narrativa cercana. Por eso el bloque central no solo vende: también cuenta quiénes somos.
          </p>
        </div>

        <div class="quote-card">
          <p>
            “La experiencia se siente más sólida cuando servicios, noticias y legado comparten una
            identidad visual coherente.”
          </p>
          <strong>Propuesta de rediseño Angular</strong>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <p class="eyebrow">Últimas Noticias</p>
          <h2>Actualidad, campañas y acciones destacadas</h2>
        </div>

        <div class="card-grid">
          <article class="info-card accent" *ngFor="let card of news">
            <h3>{{ card.title }}</h3>
            <p>{{ card.description }}</p>
          </article>
        </div>
      </section>

      <section class="section faq-section">
        <div class="section-head">
          <p class="eyebrow">Preguntas Frecuentes</p>
          <h2>Información clara para decisiones rápidas</h2>
        </div>

        <div class="faq-list">
          <article class="faq-item" *ngFor="let item of faqs">
            <h3>{{ item.title }}</h3>
            <p>{{ item.description }}</p>
          </article>
        </div>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class HomePageComponent implements OnDestroy {
  private readonly http = inject(HttpClient);
  private readonly serviceLayouts = [
    [0, 1, 2, 3, 4, 5],
    [1, 0, 3, 2, 5, 4],
    [1, 3, 0, 5, 2, 4],
    [3, 1, 5, 0, 4, 2],
  ];
  private readonly servicesInterval = globalThis.setInterval(() => this.nextServiceLayout(), 2800);

  readonly highlights = heroHighlights;
  readonly services = serviceCards;
  readonly news = newsCards;
  readonly faqs = faqItems;
  readonly quickServiceOptions: QuickServiceOption[] = [
    {
      label: 'Traslado / Remolque',
      title: 'Traslado seguro de tu vehículo',
      description:
        'Coordinamos remolque y traslado con enfoque en rapidez, cuidado del vehículo y atención directa.',
      eta: '15 a 35 min',
    },
    {
      label: 'Asistencia Mecánica',
      title: 'Asistencia mecánica inmediata',
      description:
        'Diagnóstico rápido para fallas comunes, apoyo en ruta y acompañamiento técnico cuando más lo necesitas.',
      eta: '10 a 25 min',
    },
    {
      label: 'Falta de Combustible',
      title: 'Entrega de combustible de emergencia',
      description:
        'Respuesta ágil para que retomes tu trayecto con seguridad y sin quedar varado más tiempo del necesario.',
      eta: '15 a 30 min',
    },
    {
      label: 'Batería Descargada',
      title: 'Asistencia por batería descargada',
      description:
        'Soporte para encendido auxiliar y verificación inicial, ideal para emergencias urbanas y salidas rápidas.',
      eta: '10 a 20 min',
    },
    {
      label: 'Cambio de Neumático',
      title: 'Cambio de neumático en sitio',
      description:
        'Atención inmediata para pinchazos o llantas dañadas, con prioridad en seguridad y continuidad del viaje.',
      eta: '15 a 25 min',
    },
  ];

  apiStatus = 'Verificando disponibilidad...';
  selectedQuickServiceLabel = 'Asistencia Mecánica';
  currentServiceLayoutIndex = 0;

  constructor() {
    const hostname = globalThis.location?.hostname ?? 'localhost';
    const apiBaseUrl = `http://${hostname}:8000`;

    this.http
      .get<{ status: string; database: string }>(`${apiBaseUrl}/api/health`)
      .subscribe({
        next: (response) => {
          this.apiStatus = `API ${response.status} | DB ${response.database}`;
        },
        error: () => {
          this.apiStatus = 'Backend no disponible todavía';
        },
      });
  }

  ngOnDestroy(): void {
    globalThis.clearInterval(this.servicesInterval);
  }

  get orderedServices(): Array<(typeof serviceCards)[number] & { index: number }> {
    const layout = this.serviceLayouts[this.currentServiceLayoutIndex];

    return layout.map((serviceIndex) => ({
      ...this.services[serviceIndex],
      index: serviceIndex,
    }));
  }

  get selectedQuickService(): QuickServiceOption {
    return (
      this.quickServiceOptions.find((option) => option.label === this.selectedQuickServiceLabel) ??
      this.quickServiceOptions[0]
    );
  }

  selectQuickService(label: string): void {
    this.selectedQuickServiceLabel = label;
  }

  nextServiceLayout(): void {
    this.currentServiceLayoutIndex = (this.currentServiceLayoutIndex + 1) % this.serviceLayouts.length;
  }
}
