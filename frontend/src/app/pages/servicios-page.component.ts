import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { RouterLink } from '@angular/router';

type CustomerService = {
  name: string;
  price: string;
  summary: string;
  includes: string[];
  note?: string;
};

@Component({
  selector: 'app-servicios-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="page">
      <section class="section-hero services-hero">
        <div>
          <p class="eyebrow">Servicios</p>
          <h1>Auxilio vial y asistencia para clientes</h1>
          <p class="lead">
            Esta vista está pensada para clientes que necesitan ayuda inmediata. El objetivo es que
            entiendan rápido qué servicio pedir, cuánto puede costar y cuándo conviene solicitar grúa.
          </p>
        </div>

        <div class="services-hero-card">
          <span>Precios sugeridos</span>
          <strong>Tarifas referenciales para arrancar la propuesta comercial</strong>
          <p>
            Puedes usarlas como base inicial y luego ajustarlas por zona, tipo de vehículo, horario y
            distancia recorrida.
          </p>
        </div>
      </section>

      <section class="spotlight compact">
        <div>
          <h2>Cómo debería explicarse esta página</h2>
          <p>
            Un cliente con una emergencia no quiere leer demasiado. Lo más efectivo es mostrar
            servicios concretos, tiempos estimados, precios desde y una aclaración simple cuando la
            tarifa depende de distancia o complejidad.
          </p>
        </div>

        <div class="quote-card">
          <p>
            “Mientras más claro sea el servicio, más rápido decide el cliente y menos fricción hay en
            la llamada o en WhatsApp.”
          </p>
        </div>
      </section>

      <section class="section">
        <div class="section-head">
          <p class="eyebrow">Catálogo Base</p>
          <h2>Servicios sugeridos para asistencia inmediata</h2>
        </div>

        <div class="customer-services-grid">
          <article class="customer-service-card" *ngFor="let service of services">
            <span class="service-price">{{ service.price }}</span>
            <h3>{{ service.name }}</h3>
            <p class="service-summary">{{ service.summary }}</p>

            <ul class="service-includes">
              <li *ngFor="let item of service.includes">{{ item }}</li>
            </ul>

            <p class="service-note" *ngIf="service.note">{{ service.note }}</p>
            <a class="button primary" routerLink="/contacto">Solicitar servicio</a>
          </article>
        </div>
      </section>

      <section class="plans-layout">
        <article class="quote-preview">
          <span class="quote-chip">Sugerencia comercial</span>
          <h4>Qué conviene mostrar al cliente</h4>
          <p>
            Usa textos cortos como “desde Bs X”, “atención 24/7”, “servicio en ciudad y carretera”,
            “respuesta inmediata” y “cotización final según distancia” para que el cliente no dude.
          </p>
        </article>

        <article class="map-stat">
          <span>Contexto útil</span>
          <strong>Servicios más lógicos para empezar</strong>
          <p>
            Cambio de batería, suministro de combustible, cambio de neumático, asistencia mecánica
            básica y remolque con grúa. Son fáciles de entender y tienen demanda real.
          </p>
        </article>

        <article class="map-stat">
          <span>Siguiente paso</span>
          <strong>Definir tarifa urbana y carretera</strong>
          <p>
            Lo ideal es manejar al menos dos reglas: precio dentro de ciudad y cotización especial
            para carretera, provincias o trayectos largos.
          </p>
        </article>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class ServiciosPageComponent {
  readonly services: CustomerService[] = [
    {
      name: 'Cambio de batería',
      price: 'Desde Bs 60 + batería',
      summary: 'Atención para revisar, retirar y reemplazar batería descargada o dañada.',
      includes: [
        'Diagnóstico rápido de encendido',
        'Instalación básica en sitio',
        'Verificación inicial después del cambio',
      ],
      note: 'La batería se cobra aparte según marca, amperaje y garantía.',
    },
    {
      name: 'Suministro de combustible',
      price: 'Desde Bs 50 + combustible',
      summary: 'Entrega de combustible de emergencia para que el cliente pueda retomar el trayecto.',
      includes: [
        'Despacho al punto de auxilio',
        'Carga de emergencia',
        'Coordinación rápida por llamada o WhatsApp',
      ],
      note: 'El combustible se cobra aparte según cantidad y tipo requerido.',
    },
    {
      name: 'Cambio de neumático',
      price: 'Desde Bs 50',
      summary: 'Cambio de llanta o apoyo técnico cuando el vehículo sufre pinchazo o daño menor.',
      includes: [
        'Cambio con llanta de auxilio del cliente',
        'Ajuste básico y revisión rápida',
        'Atención en ciudad o rutas cercanas',
      ],
    },
    {
      name: 'Asistencia mecánica básica',
      price: 'Desde Bs 80',
      summary: 'Revisión rápida de fallas comunes que pueden resolverse sin traslado del vehículo.',
      includes: [
        'Diagnóstico inicial',
        'Paso de corriente o revisión básica',
        'Orientación sobre reparación posterior',
      ],
      note: 'Si se requiere repuesto o reparación mayor, se cotiza aparte.',
    },
    {
      name: 'Remolque con grúa en ciudad',
      price: 'Desde Bs 150',
      summary: 'Traslado del vehículo dentro del área urbana cuando ya no puede continuar circulando.',
      includes: [
        'Carga y aseguramiento del vehículo',
        'Traslado básico en zona urbana',
        'Coordinación con taller de destino',
      ],
      note: 'La tarifa final varía por distancia, horario y tipo de vehículo.',
    },
    {
      name: 'Remolque en carretera o provincias',
      price: 'Cotización',
      summary: 'Servicio de grúa para distancias largas, rutas, accidentes o traslados especiales.',
      includes: [
        'Evaluación del punto de auxilio',
        'Cotización según kilómetros',
        'Definición según peso y condiciones del vehículo',
      ],
      note: 'Conviene publicar “cotización inmediata” en vez de una tarifa fija única.',
    },
  ];
}
