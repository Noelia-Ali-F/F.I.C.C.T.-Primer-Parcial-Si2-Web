import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

type DashboardStat = {
  label: string;
  value: string;
  detail: string;
};

type DashboardItem = {
  title: string;
  subtitle: string;
  meta: string;
};

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="dashboard-page">
      <aside class="dashboard-sidebar">
        <a class="dashboard-brand" routerLink="/">
          <span class="dashboard-brand-mark">ACB</span>
          <span>
            <strong>Taller ACB</strong>
            <small>Panel de control</small>
          </span>
        </a>

        <nav class="dashboard-menu">
          <a class="is-active" routerLink="/dashboard">Resumen</a>
          <a routerLink="/suscripciones">Suscripciones</a>
          <a routerLink="/planes">Planes</a>
          <a routerLink="/servicios">Servicios</a>
          <a routerLink="/contacto">Contacto</a>
        </nav>

        <a class="dashboard-exit" routerLink="/">Volver al sitio</a>
      </aside>

      <section class="dashboard-content">
        <header class="dashboard-topbar">
          <div>
            <p class="eyebrow">Dashboard</p>
            <h1>Panel principal</h1>
            <p class="lead">
              Una vista base para administrar talleres, solicitudes de auxilio y actividad de la red.
            </p>
          </div>

          <div class="dashboard-user-card">
            <span>Sesión activa</span>
            <strong>Administrador general</strong>
          </div>
        </header>

        <section class="dashboard-stats">
          <article class="dashboard-stat-card" *ngFor="let stat of stats">
            <span>{{ stat.label }}</span>
            <strong>{{ stat.value }}</strong>
            <p>{{ stat.detail }}</p>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="dashboard-panel">
            <div class="dashboard-panel-head">
              <h2>Solicitudes recientes</h2>
              <a routerLink="/servicios">Ver servicios</a>
            </div>

            <div class="dashboard-list">
              <article class="dashboard-list-item" *ngFor="let item of requests">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span>{{ item.meta }}</span>
              </article>
            </div>
          </article>

          <article class="dashboard-panel">
            <div class="dashboard-panel-head">
              <h2>Talleres socios</h2>
              <a routerLink="/suscripciones">Gestionar</a>
            </div>

            <div class="dashboard-list">
              <article class="dashboard-list-item" *ngFor="let item of workshops">
                <div>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span>{{ item.meta }}</span>
              </article>
            </div>
          </article>
        </section>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class DashboardPageComponent {
  readonly stats: DashboardStat[] = [
    { label: 'Solicitudes hoy', value: '18', detail: 'Auxilios y consultas registradas durante la jornada.' },
    { label: 'Talleres activos', value: '32', detail: 'Talleres socios con disponibilidad operativa.' },
    { label: 'Servicios urgentes', value: '7', detail: 'Casos con prioridad alta o atención inmediata.' },
    { label: 'Cobertura', value: '5 zonas', detail: 'Ciudad, periferia y rutas con respuesta coordinada.' },
  ];

  readonly requests: DashboardItem[] = [
    { title: 'Cambio de batería', subtitle: 'Cliente en Equipetrol, Santa Cruz', meta: 'Hace 8 min' },
    { title: 'Remolque urbano', subtitle: 'Vehículo detenido en Av. Banzer', meta: 'Hace 12 min' },
    { title: 'Falta de combustible', subtitle: 'Solicitud desde zona sur', meta: 'Hace 21 min' },
  ];

  readonly workshops: DashboardItem[] = [
    { title: 'Taller El Rápido', subtitle: 'Mecánica general y electricidad', meta: 'Disponible' },
    { title: 'Gruas del Oriente', subtitle: 'Remolque y auxilio móvil', meta: 'En ruta' },
    { title: 'Baterías Express', subtitle: 'Cambio e instalación en sitio', meta: 'Disponible' },
  ];
}
