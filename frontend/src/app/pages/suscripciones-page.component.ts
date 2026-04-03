import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-suscripciones-page',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  template: `
    <main class="page">
      <section class="section-hero subscriptions-hero">
        <div>
          <p class="eyebrow">Suscripciones</p>
          <h1>Afiliación de talleres socios</h1>
          <p class="lead">
            Registra tu taller con los datos mínimos recomendables para iniciar el proceso de
            afiliación dentro de la red de asistencia del proyecto.
          </p>
        </div>

        <div class="subscriptions-hero-card">
          <span>Mínimo recomendable</span>
          <strong>Primero contacto y capacidad operativa</strong>
          <p>La validación documental y los detalles adicionales pueden pedirse en una segunda etapa.</p>
        </div>
      </section>

      <section class="subscriptions-layout">
        <article class="subscriptions-panel">
          <div class="section-head compact-head">
            <p class="eyebrow">Campos clave para empezar</p>
            <h2>Formulario inicial de suscripción</h2>
          </div>

          <form class="subscription-form">
            <label class="form-field">
              <span>Nombre del taller</span>
              <input
                type="text"
                name="workshopName"
                [(ngModel)]="form.workshopName"
                placeholder="Ej. Taller El Rápido"
              />
            </label>

            <label class="form-field">
              <span>Propietario o responsable</span>
              <input
                type="text"
                name="ownerName"
                [(ngModel)]="form.ownerName"
                placeholder="Nombre completo del responsable"
              />
            </label>

            <label class="form-field">
              <span>Teléfono</span>
              <input
                type="tel"
                name="phone"
                [(ngModel)]="form.phone"
                placeholder="Ej. 3 3123456"
              />
            </label>

            <label class="form-field">
              <span>WhatsApp</span>
              <input
                type="tel"
                name="whatsapp"
                [(ngModel)]="form.whatsapp"
                placeholder="Ej. 77712345"
              />
            </label>

            <label class="form-field form-field-wide">
              <span>Dirección</span>
              <textarea
                name="address"
                [(ngModel)]="form.address"
                rows="3"
                placeholder="Zona, avenida, calle y referencias del taller"
              ></textarea>
            </label>

            <label class="form-field form-field-wide">
              <span>Servicios que ofrece</span>
              <textarea
                name="services"
                [(ngModel)]="form.services"
                rows="3"
                placeholder="Ej. mecánica general, electricidad, batería, remolque, cambio de neumático"
              ></textarea>
            </label>

            <label class="form-field">
              <span>Horario de atención</span>
              <input
                type="text"
                name="schedule"
                [(ngModel)]="form.schedule"
                placeholder="Ej. Lunes a sábado, 08:00 a 20:00"
              />
            </label>

            <label class="form-field">
              <span>¿Cuenta con grúa o auxilio móvil?</span>
              <select name="mobileAssistance" [(ngModel)]="form.mobileAssistance">
                <option value="">Selecciona una opción</option>
                <option value="grua">Sí, cuenta con grúa</option>
                <option value="auxilio">Sí, cuenta con auxilio móvil</option>
                <option value="ambos">Sí, cuenta con ambos</option>
                <option value="no">No por ahora</option>
              </select>
            </label>

            <div class="form-actions form-field-wide">
              <a class="button secondary" routerLink="/contacto">Necesito ayuda</a>
              <button type="button" class="button primary">Enviar solicitud</button>
            </div>
          </form>
        </article>

        <aside class="subscriptions-sidebar">
          <article class="quote-preview">
            <span class="quote-chip">Mínimo recomendable</span>
            <h4>Campos clave para empezar</h4>
            <p>
              Nombre del taller, propietario o responsable, teléfono, WhatsApp, dirección, servicios
              que ofrece, horario de atención y si cuenta con grúa o auxilio móvil.
            </p>
          </article>

          <article class="map-stat">
            <span>Consejo UX</span>
            <strong>No pidas demasiados datos al inicio</strong>
            <p>
              Primero captura contacto y capacidad operativa. Luego puedes completar validación y
              documentos en una segunda etapa.
            </p>
          </article>

          <article class="map-stat">
            <span>Siguiente paso</span>
            <strong>Armar formulario final</strong>
            <p>
              Después se puede ampliar con documentos, fotos del taller, cobertura geográfica y
              validación del servicio.
            </p>
          </article>
        </aside>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class SuscripcionesPageComponent {
  form = {
    workshopName: '',
    ownerName: '',
    phone: '',
    whatsapp: '',
    address: '',
    services: '',
    schedule: '',
    mobileAssistance: '',
  };
}
