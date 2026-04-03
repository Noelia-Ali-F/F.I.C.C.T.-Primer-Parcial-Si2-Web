import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-map-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="page">
      <section class="section-hero map-hero">
        <div>
          <p class="eyebrow">Mapa</p>
          <h1>Santa Cruz de la Sierra, Bolivia</h1>
          <p class="lead">
            Una vista dedicada para ubicar rápidamente la ciudad y reforzar presencia territorial
            dentro del sitio.
          </p>
        </div>

        <div class="map-hero-card">
          <span>Ubicación destacada</span>
          <strong>Centro urbano de Santa Cruz de la Sierra</strong>
          <p>Vista integrada con OpenStreetMap, lista para navegación y referencia visual.</p>
        </div>
      </section>

      <section class="map-layout">
        <div class="map-frame">
          <iframe
            title="Mapa de Santa Cruz de la Sierra, Bolivia"
            [src]="mapUrl"
            loading="lazy"
            referrerpolicy="no-referrer-when-downgrade"
          ></iframe>
        </div>

        <aside class="map-sidebar">
          <article class="map-note">
            <p class="eyebrow">Referencia</p>
            <h2>Punto geográfico principal</h2>
            <p>
              Santa Cruz de la Sierra es el centro de esta vista para que el usuario tenga un mapa
              claro, simple y útil dentro de la navegación del frontend.
            </p>
          </article>

          <article class="map-stat">
            <span>Ciudad</span>
            <strong>Santa Cruz de la Sierra</strong>
          </article>

          <article class="map-stat">
            <span>País</span>
            <strong>Bolivia</strong>
          </article>

          <article class="map-stat">
            <span>Acción</span>
            <a class="button primary" routerLink="/contacto">Solicitar asistencia</a>
          </article>
        </aside>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class MapPageComponent {
  private readonly sanitizer = inject(DomSanitizer);

  readonly mapUrl: SafeResourceUrl = this.sanitizer.bypassSecurityTrustResourceUrl(
    'https://www.openstreetmap.org/export/embed.html?bbox=-63.2300%2C-17.8600%2C-63.1200%2C-17.7300&layer=mapnik&marker=-17.7833%2C-63.1821',
  );
}
