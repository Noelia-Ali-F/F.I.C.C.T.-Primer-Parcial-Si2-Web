import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

type PlanCard = {
  name: string;
  tagline: string;
  target: string;
  benefits: string[];
  highlight?: string;
};

@Component({
  selector: 'app-planes-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="page">
      <section class="section-hero plans-hero">
        <div>
          <p class="eyebrow">Planes</p>
          <h1>Planes de afiliación para talleres socios</h1>
          <p class="lead">
            Esta vista está pensada para mostrar con claridad qué obtiene un taller al asociarse al
            proyecto y cómo puede crecer dentro de la red de asistencia.
          </p>
        </div>

        <div class="plans-hero-card">
          <span>Contexto recomendado</span>
          <strong>La promesa no debe ser solo “ser socio”, sino recibir más trabajo y más visibilidad.</strong>
          <p>Los talleres entienden mejor la propuesta cuando se habla de beneficios operativos reales.</p>
        </div>
      </section>

      <section class="spotlight compact">
        <div>
          <h2>Qué debería comunicar esta vista</h2>
          <p>
            Los planes deben explicar acceso a clientes, prioridad en derivaciones, presencia dentro
            de la plataforma, soporte comercial y pertenencia a una red confiable.
          </p>
        </div>

        <div class="quote-card">
          <p>
            “Un buen plan no vende solo membresía: vende flujo de trabajo, confianza y oportunidad de
            crecimiento para el taller.”
          </p>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <p class="eyebrow">Propuesta Base</p>
          <h2>Ideas de planes para talleres asociados</h2>
        </div>

        <div class="plans-grid">
          <article class="plan-card" *ngFor="let plan of plans" [class.plan-highlight]="plan.highlight">
            <span class="plan-badge" *ngIf="plan.highlight">{{ plan.highlight }}</span>
            <h3>{{ plan.name }}</h3>
            <p class="plan-tagline">{{ plan.tagline }}</p>
            <p class="plan-target">{{ plan.target }}</p>

            <ul class="plan-benefits">
              <li *ngFor="let benefit of plan.benefits">{{ benefit }}</li>
            </ul>

            <a class="button primary" routerLink="/suscripciones">Solicitar este plan</a>
          </article>
        </div>
      </section>

      <section class="plans-layout">
        <article class="quote-preview">
          <span class="quote-chip">Ideas de contenido</span>
          <h4>Mensajes que ayudan a vender mejor los planes</h4>
          <p>
            “Más visibilidad para tu taller”, “más oportunidades de servicio”, “prioridad en
            asignación”, “presencia en mapa y red de asistencia”, y “respaldo de una plataforma
            confiable”.
          </p>
        </article>

        <article class="map-stat">
          <span>Sugerencia comercial</span>
          <strong>No compitas solo por precio</strong>
          <p>
            Diferencia los planes por nivel de exposición, prioridad, soporte y beneficios
            operativos, no solo por una tarifa de membresía.
          </p>
        </article>

        <article class="map-stat">
          <span>Siguiente paso</span>
          <strong>Definir precios y condiciones</strong>
          <p>
            Cuando quieras, te ayudo a convertir estos planes en una tabla final con precios,
            comisiones y reglas de afiliación.
          </p>
        </article>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class PlanesPageComponent {
  readonly plans: PlanCard[] = [
    {
      name: 'Plan Base',
      tagline: 'Ingreso simple a la red de talleres socios.',
      target: 'Ideal para talleres pequeños que quieren empezar a recibir visibilidad y contactos.',
      benefits: [
        'Perfil dentro de la plataforma',
        'Presencia básica en directorio',
        'Recepción de consultas y derivaciones',
        'Acceso inicial a la red de talleres asociados',
      ],
    },
    {
      name: 'Plan Profesional',
      tagline: 'Mayor exposición y prioridad en asignaciones.',
      target: 'Pensado para talleres con más capacidad operativa y atención más constante.',
      benefits: [
        'Mayor prioridad frente al plan base',
        'Mejor posicionamiento dentro de la plataforma',
        'Recepción preferente de solicitudes',
        'Destacado comercial dentro de campañas y secciones clave',
      ],
      highlight: 'Recomendado',
    },
    {
      name: 'Plan Aliado 24/7',
      tagline: 'Para talleres y operadores con respuesta rápida o cobertura ampliada.',
      target: 'Enfocado en talleres con capacidad de urgencias, auxilio móvil o atención extendida.',
      benefits: [
        'Etiqueta de atención prioritaria',
        'Mayor visibilidad en urgencias o auxilio',
        'Posibilidad de operar en horarios extendidos',
        'Participación en la red de asistencia inmediata',
      ],
    },
  ];
}
