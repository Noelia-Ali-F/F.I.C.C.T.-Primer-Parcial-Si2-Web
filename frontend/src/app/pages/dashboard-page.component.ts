import { CommonModule, DatePipe } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

type DashboardSection = 'dashboard' | 'workshops' | 'technicians' | 'clients';
type TechnicianStatus = 'disponible' | 'ocupado' | 'fuera_de_servicio';
type TechnicianFilter = 'activos' | 'todos' | 'historial';
type WorkshopApprovalStatus = 'pendiente' | 'aprobada' | 'rechazada';
type ClientStatus = 'active' | 'suspended';

type DashboardStat = {
  label: string;
  value: string;
  detail: string;
  trend: string;
  tone: 'gold' | 'blue' | 'teal' | 'slate';
};

type DashboardItem = {
  title: string;
  subtitle: string;
  meta: string;
  priority: 'Alta' | 'Media' | 'Seguimiento';
};

type WorkshopRegistration = {
  id: number;
  workshop_name: string;
  contact_name: string;
  phone: string;
  email: string;
  zone: string;
  specialty: string;
  latitude: number | null;
  longitude: number | null;
  timezone: string | null;
  utc_offset_minutes: number | null;
  created_at: string;
};

type WorkshopDisplayItem = WorkshopRegistration & {
  approval_status: WorkshopApprovalStatus;
};

type Technician = {
  id: number;
  full_name: string;
  phone: string;
  email: string;
  specialty: string;
  status: TechnicianStatus;
  created_at: string;
  updated_at: string;
};

type TechnicianFormModel = {
  full_name: string;
  phone: string;
  email: string;
  specialty: string;
  status: TechnicianStatus;
};

type Client = {
  id: number;
  identity_card: string;
  full_name: string;
  email: string;
  phone: string;
  role: string;
  status: ClientStatus;
  accepted_terms: boolean;
  created_at: string;
  updated_at: string;
};

type ClientFormModel = {
  identity_card: string;
  full_name: string;
  email: string;
  phone: string;
  role: string;
  status: ClientStatus;
  accepted_terms: boolean;
};

type WorkshopFormModel = {
  workshop_name: string;
  contact_name: string;
  phone: string;
  email: string;
  zone: string;
  specialty: string;
};

@Component({
  selector: 'app-dashboard-page',
  standalone: true,
  imports: [CommonModule, DatePipe, FormsModule, RouterLink],
  template: `
    <main class="dashboard-page" [class.is-sidebar-collapsed]="isSidebarCollapsed">
      <aside class="dashboard-sidebar" [class.is-collapsed]="isSidebarCollapsed">
        <a class="dashboard-brand" routerLink="/">
          <span class="dashboard-brand-mark">
            <img src="/favicon.svg" alt="Logo ACB" />
          </span>
          <span>
            <strong>Taller ACB</strong>
            <small>Centro de operaciones</small>
          </span>
        </a>

        <nav class="dashboard-menu">
          <div class="dashboard-menu-group">
            <button
              class="dashboard-menu-link"
              type="button"
              [class.is-active]="selectedSection === 'dashboard'"
              (click)="selectSection('dashboard')"
            >
              <span class="dashboard-menu-icon">⌂</span>
              <span>Dashboard</span>
            </button>
          </div>

          <div class="dashboard-menu-group">
            <button
              class="dashboard-menu-link"
              type="button"
              [class.is-active]="selectedSection === 'workshops'"
              (click)="selectSection('workshops')"
            >
              <span class="dashboard-menu-icon">◫</span>
              <span>Solicitudes</span>
              <span class="dashboard-menu-badge">Live</span>
            </button>

            <div class="dashboard-submenu">
              <button
                class="dashboard-submenu-item"
                type="button"
                [class.is-active]="selectedSection === 'workshops'"
                (click)="selectSection('workshops')"
              >
                <span class="dashboard-submenu-bullet"></span>
                <span>Taller</span>
                <strong>{{ displayWorkshops.length | number: '2.0-0' }}</strong>
              </button>
            </div>
          </div>

          <div class="dashboard-menu-group">
            <button
              class="dashboard-menu-link"
              type="button"
              [class.is-active]="selectedSection === 'technicians'"
              (click)="selectSection('technicians')"
            >
              <span class="dashboard-menu-icon">◔</span>
              <span>Tecnicos</span>
            </button>

            <div class="dashboard-submenu">
              <button
                class="dashboard-submenu-item"
                type="button"
                [class.is-active]="selectedSection === 'technicians'"
                (click)="selectSection('technicians')"
              >
                <span class="dashboard-submenu-bullet"></span>
                <span>Lista de Tecnicos</span>
                <strong>{{ technicians.length | number: '2.0-0' }}</strong>
              </button>
            </div>
          </div>

          <div class="dashboard-menu-group">
            <button
              class="dashboard-menu-link"
              type="button"
              [class.is-active]="selectedSection === 'clients'"
              (click)="selectSection('clients')"
            >
              <span class="dashboard-menu-icon">◉</span>
              <span>Clientes</span>
            </button>

            <div class="dashboard-submenu">
              <button
                class="dashboard-submenu-item"
                type="button"
                [class.is-active]="selectedSection === 'clients'"
                (click)="selectSection('clients')"
              >
                <span class="dashboard-submenu-bullet"></span>
                <span>Lista de Clientes</span>
                <strong>{{ clients.length | number: '2.0-0' }}</strong>
              </button>
            </div>
          </div>

          <div class="dashboard-menu-group">
            <button class="dashboard-menu-link" type="button">
              <span class="dashboard-menu-icon">⚙</span>
              <span>Mantenimiento</span>
            </button>
          </div>

          <div class="dashboard-menu-group">
            <button class="dashboard-menu-link" type="button">
              <span class="dashboard-menu-icon">⬒</span>
              <span>Emergencias</span>
              <span class="dashboard-menu-badge">24/7</span>
            </button>
          </div>

          <div class="dashboard-menu-group">
            <button class="dashboard-menu-link" type="button">
              <span class="dashboard-menu-icon">▥</span>
              <span>Reportes</span>
            </button>
          </div>

          <div class="dashboard-menu-group">
            <button class="dashboard-menu-link" type="button">
              <span class="dashboard-menu-icon">▣</span>
              <span>Bitacora</span>
            </button>
          </div>
        </nav>

        <section class="dashboard-sidebar-card">
          <span>Turno activo</span>
          <strong>Administración general</strong>
          <p>Supervisión de afiliaciones, validación de talleres y control del panel comercial.</p>
        </section>
      </aside>

      <section class="dashboard-content">
        <header class="dashboard-topbar">
          <div class="dashboard-topbar-copy">
            <button
              class="dashboard-sidebar-toggle"
              type="button"
              (click)="toggleSidebar()"
              [attr.aria-label]="isSidebarCollapsed ? 'Expandir menu lateral' : 'Contraer menu lateral'"
            >
              ☰
            </button>
            <span class="dashboard-topbar-kicker">Panel interno</span>
            <strong>{{ sectionTitle }}</strong>
          </div>

          <div class="dashboard-topbar-actions">
            <div class="dashboard-user-pill">
              <span class="dashboard-user-avatar">JF</span>
              <span class="dashboard-user-name">Jhasmany Fernandez</span>
            </div>

            <button class="dashboard-topbar-icon" type="button" aria-label="Notificaciones">
              🔔
            </button>

            <a class="dashboard-topbar-icon dashboard-topbar-logout" routerLink="/login" aria-label="Cerrar sesion">
              ⎋
            </a>
          </div>
        </header>

        <section
          class="dashboard-stats"
          *ngIf="selectedSection === 'dashboard' || selectedSection === 'technicians' || selectedSection === 'clients'"
          [class.is-compact]="selectedSection === 'technicians' || selectedSection === 'clients'"
        >
          <article class="dashboard-stat-card" *ngFor="let stat of stats" [attr.data-tone]="stat.tone">
            <div class="dashboard-stat-top">
              <span>{{ stat.label }}</span>
              <small>{{ stat.trend }}</small>
            </div>
            <strong>{{ stat.value }}</strong>
            <p>{{ stat.detail }}</p>
          </article>
        </section>

        <section class="dashboard-grid">
          <article class="dashboard-panel dashboard-panel-accent" *ngIf="selectedSection === 'dashboard'">
            <div class="dashboard-panel-head">
              <div>
                <p class="dashboard-panel-kicker">Actividad prioritaria</p>
                <h2>Solicitudes recientes</h2>
              </div>
              <a routerLink="/servicios">Ver servicios</a>
            </div>

            <div class="dashboard-list">
              <article class="dashboard-list-item" *ngFor="let item of requests">
                <div class="dashboard-list-copy">
                  <span class="dashboard-list-priority">{{ item.priority }}</span>
                  <strong>{{ item.title }}</strong>
                  <p>{{ item.subtitle }}</p>
                </div>
                <span class="dashboard-list-meta">{{ item.meta }}</span>
              </article>
            </div>
          </article>

          <article class="dashboard-panel" *ngIf="selectedSection === 'dashboard'">
            <div class="dashboard-panel-head">
              <div>
                <p class="dashboard-panel-kicker">Resumen rápido</p>
                <h2>Radar de cobertura</h2>
              </div>
            </div>

            <div class="dashboard-coverage">
              <article class="dashboard-coverage-card">
                <span>Zonas activas</span>
                <strong>{{ uniqueZonesCount }}</strong>
                <p>Áreas distintas con talleres registrados desde el formulario.</p>
              </article>

              <article class="dashboard-coverage-card dashboard-coverage-card-highlight">
                <span>Último ingreso</span>
                <strong>{{ latestWorkshopLabel }}</strong>
                <p>{{ latestWorkshopDetail }}</p>
              </article>
            </div>

            <div class="dashboard-mini-list" *ngIf="recentWorkshops.length">
              <article class="dashboard-mini-item" *ngFor="let workshop of recentWorkshops">
                <div>
                  <strong>{{ workshop.workshop_name }}</strong>
                  <p>{{ workshop.zone }} · {{ workshop.specialty }}</p>
                </div>
                <span>{{ workshop.created_at | date: 'shortTime' }}</span>
              </article>
            </div>
          </article>

          <article class="dashboard-panel dashboard-panel-wide" *ngIf="selectedSection === 'workshops'">
            <div class="dashboard-panel-head">
              <div>
                <p class="dashboard-panel-kicker">Registros recibidos</p>
                <h2>Registra tu taller mecánico</h2>
              </div>
              <div class="dashboard-toolbar">
                <span class="dashboard-toolbar-note">{{ displayWorkshops.length }} registros cargados</span>
                <button class="dashboard-refresh-button" type="button" (click)="loadWorkshops()">
                  Actualizar
                </button>
              </div>
            </div>

            <p class="dashboard-loading" *ngIf="isLoading">Cargando talleres registrados...</p>
            <p class="dashboard-empty" *ngIf="!isLoading && !displayWorkshops.length">
              Aún no hay talleres registrados.
            </p>

            <div class="dashboard-table-wrap" *ngIf="!isLoading && displayWorkshops.length">
              <table class="dashboard-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Taller</th>
                    <th>Responsable</th>
                    <th>Contacto</th>
                    <th>Zona</th>
                    <th>Especialidad</th>
                    <th>Registro</th>
                    <th>Aprobación</th>
                    <th>Opciones</th>
                  </tr>
                </thead>
                <tbody>
                  <tr *ngFor="let workshop of paginatedWorkshops">
                    <td data-label="ID">
                      <span class="dashboard-id-chip">#{{ workshop.id }}</span>
                    </td>
                    <td data-label="Taller">
                      <div class="dashboard-table-primary">
                        <strong>{{ workshop.workshop_name }}</strong>
                        <span>{{ getWorkshopStatus(workshop.created_at) }}</span>
                      </div>
                    </td>
                    <td data-label="Responsable">{{ workshop.contact_name }}</td>
                    <td data-label="Contacto">
                      <div class="dashboard-table-contact">
                        <strong>{{ workshop.phone }}</strong>
                        <span>{{ workshop.email }}</span>
                      </div>
                    </td>
                    <td data-label="Zona">{{ workshop.zone }}</td>
                    <td data-label="Especialidad">{{ workshop.specialty }}</td>
                    <td data-label="Registro">{{ workshop.created_at | date: 'short' }}</td>
                    <td data-label="Aprobación">
                      <button
                        class="dashboard-status-pill dashboard-status-button"
                        type="button"
                        [attr.data-status]="workshop.approval_status"
                        (click)="cycleWorkshopApproval(workshop)"
                        [attr.aria-label]="'Cambiar aprobación de ' + workshop.workshop_name"
                      >
                        <span class="dashboard-status-dot"></span>
                        {{ workshopApprovalLabel(workshop.approval_status) }}
                      </button>
                    </td>
                    <td data-label="Opciones">
                      <div class="workshop-actions">
                        <button
                          class="technician-icon-button"
                          type="button"
                          (click)="editWorkshop(workshop)"
                          [attr.aria-label]="'Editar ' + workshop.workshop_name"
                          title="Editar"
                        >
                          ✎
                        </button>
                        <button
                          class="technician-icon-button workshop-delete-button"
                          type="button"
                          (click)="deleteWorkshop(workshop)"
                          [attr.aria-label]="'Eliminar ' + workshop.workshop_name"
                          title="Eliminar"
                        >
                          🗑
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div class="dashboard-pagination" *ngIf="!isLoading && displayWorkshops.length > workshopsPageSize">
              <p class="dashboard-pagination-info">
                Mostrando {{ workshopsRangeStart }}-{{ workshopsRangeEnd }} de {{ displayWorkshops.length }} registros
              </p>

              <div class="dashboard-pagination-actions">
                <button
                  class="dashboard-secondary-button"
                  type="button"
                  (click)="goToPreviousWorkshopsPage()"
                  [disabled]="workshopsPage === 1"
                >
                  Anterior
                </button>
                <span class="dashboard-pagination-page">Página {{ workshopsPage }} / {{ workshopsTotalPages }}</span>
                <button
                  class="dashboard-secondary-button"
                  type="button"
                  (click)="goToNextWorkshopsPage()"
                  [disabled]="workshopsPage === workshopsTotalPages"
                >
                  Siguiente
                </button>
              </div>
            </div>
          </article>

          <article class="dashboard-panel dashboard-panel-wide" *ngIf="selectedSection === 'technicians'">
            <div class="technician-crud">
              <div class="technician-crud-head">
                <div>
                  <p class="dashboard-panel-kicker">Gestion del equipo</p>
                  <h2>Gestionar Tecnicos</h2>
                </div>
                <button class="technician-create-button" type="button" (click)="startCreate()">
                  <span>+</span>
                  <span>{{ showTechnicianForm ? (editingTechnicianId ? 'Editar Tecnico' : 'Crear Tecnico') : 'Crear Tecnico' }}</span>
                </button>
              </div>

              <div class="technician-filter-tabs">
                <button
                  type="button"
                  class="technician-filter-tab"
                  [class.is-active]="technicianFilter === 'activos'"
                  (click)="technicianFilter = 'activos'"
                >
                  Activos
                </button>
                <button
                  type="button"
                  class="technician-filter-tab"
                  [class.is-active]="technicianFilter === 'todos'"
                  (click)="technicianFilter = 'todos'"
                >
                  Todos
                </button>
                <button
                  type="button"
                  class="technician-filter-tab"
                  [class.is-active]="technicianFilter === 'historial'"
                  (click)="technicianFilter = 'historial'"
                >
                  Historial
                </button>
              </div>

              <section class="technician-form-card" *ngIf="showTechnicianForm">
                <div class="technician-form-head">
                  <div>
                    <p class="dashboard-panel-kicker">Formulario</p>
                    <h3>{{ editingTechnicianId ? 'Editar tecnico' : 'Agregar tecnico' }}</h3>
                  </div>
                  <button class="dashboard-secondary-button" type="button" (click)="cancelTechnicianForm()">
                    Cerrar
                  </button>
                </div>

                <form class="technician-form technician-form-grid" (ngSubmit)="submitTechnician()">
                  <label class="technician-field">
                    <span>Nombre</span>
                    <input type="text" name="full_name" [(ngModel)]="technicianForm.full_name" required minlength="3" placeholder="Ej. Carlos Ramirez" />
                  </label>

                  <label class="technician-field">
                    <span>Telefono</span>
                    <input type="text" name="phone" [(ngModel)]="technicianForm.phone" required minlength="7" placeholder="Ej. 76324511" />
                  </label>

                  <label class="technician-field">
                    <span>Email</span>
                    <input type="email" name="email" [(ngModel)]="technicianForm.email" required placeholder="Ej. tecnico@correo.com" />
                  </label>

                  <label class="technician-field">
                    <span>Especialidad</span>
                    <input type="text" name="specialty" [(ngModel)]="technicianForm.specialty" required minlength="2" placeholder="Ej. Electricidad automotriz" />
                  </label>

                  <label class="technician-field technician-field-wide">
                    <span>Estado del tecnico</span>
                    <select name="status" [(ngModel)]="technicianForm.status" required>
                      <option value="disponible">Disponible</option>
                      <option value="ocupado">Ocupado</option>
                      <option value="fuera_de_servicio">Fuera de servicio</option>
                    </select>
                  </label>

                  <p class="technician-form-feedback technician-field-wide" *ngIf="technicianFeedback">
                    {{ technicianFeedback }}
                  </p>

                  <div class="technician-form-actions technician-field-wide">
                    <button class="dashboard-refresh-button" type="submit" [disabled]="isSavingTechnician">
                      {{ isSavingTechnician ? 'Guardando...' : editingTechnicianId ? 'Guardar cambios' : 'Agregar Tecnico' }}
                    </button>
                    <button class="dashboard-secondary-button" type="button" (click)="resetTechnicianForm()">
                      Limpiar
                    </button>
                  </div>
                </form>
              </section>

              <section class="technician-table-card">
                <p class="dashboard-loading" *ngIf="isTechniciansLoading">Cargando tecnicos...</p>
                <p class="dashboard-empty" *ngIf="!isTechniciansLoading && !filteredTechnicians.length">
                  No hay tecnicos para el filtro seleccionado.
                </p>

                <div class="dashboard-table-wrap technician-table-wrap" *ngIf="!isTechniciansLoading && filteredTechnicians.length">
                  <table class="dashboard-table dashboard-table-technicians">
                    <thead>
                      <tr>
                        <th>Nombre</th>
                        <th>Telefono</th>
                        <th>Email</th>
                        <th>Especialidad</th>
                        <th>Estado</th>
                        <th>Acciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let technician of filteredTechnicians">
                        <td data-label="Nombre">
                          <div class="dashboard-table-primary">
                            <strong>{{ technician.full_name }}</strong>
                            <span>Actualizado {{ technician.updated_at | date: 'shortDate' }}</span>
                          </div>
                        </td>
                        <td data-label="Telefono">{{ technician.phone }}</td>
                        <td data-label="Email">{{ technician.email }}</td>
                        <td data-label="Especialidad">{{ technician.specialty }}</td>
                        <td data-label="Estado">
                          <span class="dashboard-status-pill" [attr.data-status]="technician.status">
                            <span class="dashboard-status-dot"></span>
                            {{ statusLabel(technician.status) }}
                          </span>
                        </td>
                        <td data-label="Acciones">
                          <div class="technician-actions">
                            <button class="technician-inline-button" type="button" (click)="editTechnician(technician)">
                              Editar
                            </button>
                            <button class="technician-icon-button" type="button" (click)="deleteTechnician(technician)" aria-label="Eliminar tecnico">
                              🗑
                            </button>
                            <button class="technician-icon-button" type="button" (click)="toggleTechnicianStatus(technician)" aria-label="Cambiar estado">
                              ☰
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </article>

          <article class="dashboard-panel dashboard-panel-wide" *ngIf="selectedSection === 'clients'">
            <div class="technician-crud">
              <div class="technician-crud-head">
                <div>
                  <p class="dashboard-panel-kicker">Usuarios registrados</p>
                  <h2>Lista de Clientes</h2>
                </div>
                <button class="dashboard-refresh-button" type="button" (click)="loadClients()">
                  Actualizar
                </button>
              </div>

              <section class="technician-table-card">
                <p class="dashboard-loading" *ngIf="isClientsLoading">Cargando clientes...</p>
                <p class="dashboard-empty" *ngIf="!isClientsLoading && !clients.length">
                  No hay clientes registrados.
                </p>

                <div class="dashboard-table-wrap technician-table-wrap" *ngIf="!isClientsLoading && clients.length">
                  <table class="dashboard-table dashboard-table-technicians">
                    <thead>
                      <tr>
                        <th>ID</th>
                        <th>Cliente</th>
                        <th>Carnet</th>
                        <th>Correo</th>
                        <th>Telefono</th>
                        <th>Rol</th>
                        <th>Estado</th>
                        <th>Registro</th>
                        <th>Opciones</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr *ngFor="let client of clients">
                        <td data-label="ID">
                          <span class="dashboard-id-chip">#{{ client.id }}</span>
                        </td>
                        <td data-label="Cliente">
                          <div class="dashboard-table-primary">
                            <strong>{{ client.full_name }}</strong>
                            <span>{{ client.accepted_terms ? 'Terminos aceptados' : 'Pendiente de terminos' }}</span>
                          </div>
                        </td>
                        <td data-label="Carnet">{{ client.identity_card }}</td>
                        <td data-label="Correo">{{ client.email }}</td>
                        <td data-label="Telefono">{{ client.phone }}</td>
                        <td data-label="Rol">{{ client.role }}</td>
                        <td data-label="Estado">
                          <button
                            class="dashboard-status-pill dashboard-status-button"
                            type="button"
                            [attr.data-status]="client.status"
                            [attr.aria-label]="'Cambiar estado de ' + client.full_name"
                            (click)="toggleClientStatus(client)"
                          >
                            <span class="dashboard-status-dot"></span>
                            {{ clientStatusLabel(client.status) }}
                          </button>
                        </td>
                        <td data-label="Registro">{{ client.created_at | date: 'short' }}</td>
                        <td data-label="Opciones">
                          <div class="workshop-actions">
                            <button
                              class="technician-icon-button"
                              type="button"
                              (click)="editClient(client)"
                              [attr.aria-label]="'Editar ' + client.full_name"
                              title="Editar"
                            >
                              ✎
                            </button>
                            <button
                              class="technician-icon-button workshop-delete-button"
                              type="button"
                              (click)="deleteClient(client)"
                              [attr.aria-label]="'Eliminar ' + client.full_name"
                              title="Eliminar"
                            >
                              🗑
                            </button>
                          </div>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>
            </div>
          </article>
        </section>
      </section>

      <div class="dashboard-modal-backdrop" *ngIf="showWorkshopEditModal" (click)="cancelWorkshopEdit()">
        <section class="dashboard-modal-card" (click)="$event.stopPropagation()">
          <div class="dashboard-modal-head">
            <div>
              <p class="dashboard-panel-kicker">Edición de registro</p>
              <h3>Actualizar taller</h3>
            </div>
          </div>

          <form class="workshop-edit-form" (ngSubmit)="submitWorkshopEdit()">
            <label class="workshop-edit-field">
              <span>Taller</span>
              <input
                type="text"
                name="workshop_name"
                [(ngModel)]="workshopForm.workshop_name"
                required
                minlength="3"
              />
            </label>

            <label class="workshop-edit-field">
              <span>Responsable</span>
              <input
                type="text"
                name="contact_name"
                [(ngModel)]="workshopForm.contact_name"
                required
                minlength="3"
              />
            </label>

            <label class="workshop-edit-field">
              <span>Contacto</span>
              <input
                type="text"
                name="phone"
                [(ngModel)]="workshopForm.phone"
                required
                minlength="7"
              />
            </label>

            <label class="workshop-edit-field">
              <span>Zona</span>
              <input type="text" name="zone" [(ngModel)]="workshopForm.zone" required minlength="2" />
            </label>

            <label class="workshop-edit-field workshop-edit-field-wide">
              <span>Especialidad</span>
              <input
                type="text"
                name="specialty"
                [(ngModel)]="workshopForm.specialty"
                required
                minlength="2"
              />
            </label>

            <p class="workshop-edit-feedback" *ngIf="workshopEditFeedback">
              {{ workshopEditFeedback }}
            </p>

            <div class="workshop-edit-actions">
              <button class="dashboard-refresh-button" type="submit" [disabled]="isSavingWorkshop">
                {{ isSavingWorkshop ? 'Actualizando...' : 'Actualizar' }}
              </button>
              <button class="dashboard-secondary-button" type="button" (click)="cancelWorkshopEdit()">
                Cancelar
              </button>
            </div>
          </form>
        </section>
      </div>

      <div class="dashboard-modal-backdrop" *ngIf="showClientEditModal" (click)="cancelClientEdit()">
        <section class="dashboard-modal-card" (click)="$event.stopPropagation()">
          <div class="dashboard-modal-head">
            <div>
              <p class="dashboard-panel-kicker">Edición de cliente</p>
              <h3>Actualizar cliente</h3>
            </div>
          </div>

          <form class="workshop-edit-form" (ngSubmit)="submitClientEdit()">
            <label class="workshop-edit-field">
              <span>Carnet</span>
              <input type="text" name="identity_card" [(ngModel)]="clientForm.identity_card" required minlength="5" />
            </label>

            <label class="workshop-edit-field">
              <span>Nombre completo</span>
              <input type="text" name="full_name" [(ngModel)]="clientForm.full_name" required minlength="3" />
            </label>

            <label class="workshop-edit-field">
              <span>Correo</span>
              <input type="email" name="email" [(ngModel)]="clientForm.email" required />
            </label>

            <label class="workshop-edit-field">
              <span>Telefono</span>
              <input type="text" name="phone" [(ngModel)]="clientForm.phone" required minlength="7" />
            </label>

            <label class="workshop-edit-field">
              <span>Rol</span>
              <input type="text" name="role" [(ngModel)]="clientForm.role" required minlength="2" />
            </label>

            <label class="workshop-edit-field">
              <span>Estado</span>
              <select name="status" [(ngModel)]="clientForm.status" required>
                <option value="active">Activo</option>
                <option value="suspended">Desactivado</option>
              </select>
            </label>

            <label class="workshop-edit-field workshop-edit-field-wide">
              <span class="client-terms-row">
                <input type="checkbox" name="accepted_terms" [(ngModel)]="clientForm.accepted_terms" />
                <span>Terminos aceptados</span>
              </span>
            </label>

            <p class="workshop-edit-feedback" *ngIf="clientEditFeedback">
              {{ clientEditFeedback }}
            </p>

            <div class="workshop-edit-actions">
              <button class="dashboard-refresh-button" type="submit" [disabled]="isSavingClient">
                {{ isSavingClient ? 'Actualizando...' : 'Actualizar' }}
              </button>
              <button class="dashboard-secondary-button" type="button" (click)="cancelClientEdit()">
                Cancelar
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class DashboardPageComponent {
  private readonly http = inject(HttpClient);
  private readonly workshopsApiUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/workshops`;
  private readonly techniciansApiUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/technicians`;
  private readonly clientsApiUrl = `${window.location.protocol}//${window.location.hostname}:8000/api/clientes`;

  readonly requests: DashboardItem[] = [
    {
      title: 'Cambio de bateria',
      subtitle: 'Cliente en Equipetrol, Santa Cruz',
      meta: 'Hace 8 min',
      priority: 'Alta',
    },
    {
      title: 'Remolque urbano',
      subtitle: 'Vehiculo detenido en Av. Banzer',
      meta: 'Hace 12 min',
      priority: 'Media',
    },
    {
      title: 'Falta de combustible',
      subtitle: 'Solicitud desde zona sur',
      meta: 'Hace 21 min',
      priority: 'Seguimiento',
    },
  ];

  selectedSection: DashboardSection = 'dashboard';
  isSidebarCollapsed = false;
  workshops: WorkshopRegistration[] = [];
  technicians: Technician[] = [];
  clients: Client[] = [];
  isLoading = true;
  isTechniciansLoading = true;
  isClientsLoading = true;
  isSavingTechnician = false;
  isSavingWorkshop = false;
  isSavingClient = false;
  editingTechnicianId: number | null = null;
  editingWorkshopId: number | null = null;
  editingClientId: number | null = null;
  technicianFeedback = '';
  workshopEditFeedback = '';
  clientEditFeedback = '';
  technicianFilter: TechnicianFilter = 'activos';
  showTechnicianForm = false;
  showWorkshopEditModal = false;
  showClientEditModal = false;
  workshopsPage = 1;
  readonly workshopsPageSize = 15;
  private readonly workshopApprovalStorageKey = 'dashboard-workshop-approval-status';
  private workshopApprovalState: Record<number, WorkshopApprovalStatus> = this.readWorkshopApprovalState();

  technicianForm: TechnicianFormModel = this.createEmptyTechnicianForm();
  workshopForm: WorkshopFormModel = this.createEmptyWorkshopForm();
  clientForm: ClientFormModel = this.createEmptyClientForm();

  stats: DashboardStat[] = [
    {
      label: 'Solicitudes hoy',
      value: '18',
      detail: 'Auxilios y consultas registradas durante la jornada.',
      trend: '+12%',
      tone: 'gold',
    },
    {
      label: 'Talleres registrados',
      value: '0',
      detail: 'Registros creados desde el formulario publico.',
      trend: 'Actual',
      tone: 'blue',
    },
    {
      label: 'Tecnicos disponibles',
      value: '0',
      detail: 'Personal listo para atender solicitudes inmediatas.',
      trend: 'Equipo',
      tone: 'teal',
    },
    {
      label: 'Clientes activos',
      value: '0',
      detail: 'Usuarios listos para iniciar sesion desde la app movil.',
      trend: 'App',
      tone: 'blue',
    },
    {
      label: 'Cobertura',
      value: '0 zonas',
      detail: 'Ciudad, periferia y rutas con respuesta coordinada.',
      trend: 'Expandible',
      tone: 'slate',
    },
  ];

  constructor() {
    this.loadWorkshops();
    this.loadTechnicians();
    this.loadClients();
  }

  get sectionTitle(): string {
    if (this.selectedSection === 'technicians') {
      return 'Gestion de Tecnicos';
    }

    if (this.selectedSection === 'clients') {
      return 'Gestion de Clientes';
    }

    if (this.selectedSection === 'workshops') {
      return 'Gestion de Solicitudes';
    }

    return 'Resumen general';
  }

  get recentWorkshops(): WorkshopRegistration[] {
    return this.workshops.slice(0, 4);
  }

  get displayWorkshops(): WorkshopDisplayItem[] {
    return this.workshops.map((workshop) => ({
      ...workshop,
      approval_status: this.workshopApprovalState[workshop.id] ?? 'pendiente',
    }));
  }

  get paginatedWorkshops(): WorkshopDisplayItem[] {
    const start = (this.workshopsPage - 1) * this.workshopsPageSize;
    return this.displayWorkshops.slice(start, start + this.workshopsPageSize);
  }

  get workshopsTotalPages(): number {
    return Math.max(1, Math.ceil(this.displayWorkshops.length / this.workshopsPageSize));
  }

  get workshopsRangeStart(): number {
    if (!this.displayWorkshops.length) {
      return 0;
    }

    return (this.workshopsPage - 1) * this.workshopsPageSize + 1;
  }

  get workshopsRangeEnd(): number {
    return Math.min(this.workshopsPage * this.workshopsPageSize, this.displayWorkshops.length);
  }

  get recentTechnicians(): Technician[] {
    return this.technicians.slice(0, 4);
  }

  get filteredTechnicians(): Technician[] {
    if (this.technicianFilter === 'todos') {
      return this.technicians;
    }

    if (this.technicianFilter === 'historial') {
      return this.technicians.filter((technician) => technician.status === 'fuera_de_servicio');
    }

    return this.technicians.filter((technician) => technician.status !== 'fuera_de_servicio');
  }

  get uniqueZonesCount(): number {
    return new Set(this.workshops.map((workshop) => workshop.zone).filter(Boolean)).size;
  }

  get latestWorkshopLabel(): string {
    const latest = this.workshops[0];
    return latest ? latest.workshop_name : 'Sin ingresos';
  }

  get latestWorkshopDetail(): string {
    const latest = this.workshops[0];
    return latest
      ? `${latest.contact_name} · ${latest.created_at ? new Date(latest.created_at).toLocaleString() : 'Reciente'}`
      : 'Aun no se ha recibido una nueva afiliacion.';
  }

  createEmptyTechnicianForm(): TechnicianFormModel {
    return {
      full_name: '',
      phone: '',
      email: '',
      specialty: '',
      status: 'disponible',
    };
  }

  createEmptyWorkshopForm(): WorkshopFormModel {
    return {
      workshop_name: '',
      contact_name: '',
      phone: '',
      email: '',
      zone: '',
      specialty: '',
    };
  }

  createEmptyClientForm(): ClientFormModel {
    return {
      identity_card: '',
      full_name: '',
      email: '',
      phone: '',
      role: 'client',
      status: 'active',
      accepted_terms: true,
    };
  }

  selectSection(section: DashboardSection): void {
    this.selectedSection = section;
  }

  toggleSidebar(): void {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }

  goToPreviousWorkshopsPage(): void {
    this.workshopsPage = Math.max(1, this.workshopsPage - 1);
  }

  goToNextWorkshopsPage(): void {
    this.workshopsPage = Math.min(this.workshopsTotalPages, this.workshopsPage + 1);
  }

  techniciansByStatus(status: TechnicianStatus): number {
    return this.technicians.filter((technician) => technician.status === status).length;
  }

  statusLabel(status: TechnicianStatus): string {
    if (status === 'fuera_de_servicio') {
      return 'Fuera de servicio';
    }

    return status.charAt(0).toUpperCase() + status.slice(1);
  }

  clientStatusLabel(status: ClientStatus): string {
    return status === 'active' ? 'Activo' : 'Desactivado';
  }

  getWorkshopStatus(createdAt: string): string {
    const created = new Date(createdAt).getTime();
    const hours = (Date.now() - created) / (1000 * 60 * 60);

    if (hours <= 3) {
      return 'Nuevo';
    }

    if (hours <= 24) {
      return 'Hoy';
    }

    return 'Pendiente';
  }

  workshopApprovalLabel(status: WorkshopApprovalStatus): string {
    if (status === 'aprobada') {
      return 'Aprobada';
    }

    if (status === 'rechazada') {
      return 'Rechazada';
    }

    return 'Pendiente';
  }

  startCreate(): void {
    this.selectedSection = 'technicians';
    this.showTechnicianForm = true;
    this.editingTechnicianId = null;
    this.technicianFeedback = '';
    this.technicianForm = this.createEmptyTechnicianForm();
  }

  resetTechnicianForm(): void {
    this.editingTechnicianId = null;
    this.technicianFeedback = '';
    this.technicianForm = this.createEmptyTechnicianForm();
  }

  cancelTechnicianForm(): void {
    this.showTechnicianForm = false;
    this.resetTechnicianForm();
  }

  editTechnician(technician: Technician): void {
    this.selectedSection = 'technicians';
    this.showTechnicianForm = true;
    this.editingTechnicianId = technician.id;
    this.technicianFeedback = '';
    this.technicianForm = {
      full_name: technician.full_name,
      phone: technician.phone,
      email: technician.email,
      specialty: technician.specialty,
      status: technician.status,
    };
  }

  submitTechnician(): void {
    const payload = {
      full_name: this.technicianForm.full_name.trim(),
      phone: this.technicianForm.phone.trim(),
      email: this.technicianForm.email.trim(),
      specialty: this.technicianForm.specialty.trim(),
      status: this.technicianForm.status,
    };

    if (!payload.full_name || !payload.phone || !payload.email || !payload.specialty) {
      this.technicianFeedback = 'Completa todos los campos del tecnico antes de guardar.';
      return;
    }

    this.isSavingTechnician = true;
    this.technicianFeedback = '';

    if (this.editingTechnicianId) {
      this.http.put<Technician>(`${this.techniciansApiUrl}/${this.editingTechnicianId}`, payload).subscribe({
        next: () => {
          this.isSavingTechnician = false;
          this.technicianFeedback = 'Tecnico actualizado correctamente.';
          this.resetTechnicianForm();
          this.showTechnicianForm = false;
          this.loadTechnicians();
        },
        error: () => {
          this.isSavingTechnician = false;
          this.technicianFeedback = 'No se pudo actualizar el tecnico.';
        },
      });
      return;
    }

    this.http.post<Technician>(this.techniciansApiUrl, payload).subscribe({
      next: () => {
        this.isSavingTechnician = false;
        this.technicianFeedback = 'Tecnico registrado correctamente.';
        this.resetTechnicianForm();
        this.showTechnicianForm = false;
        this.loadTechnicians();
      },
      error: () => {
        this.isSavingTechnician = false;
        this.technicianFeedback = 'No se pudo registrar el tecnico.';
      },
    });
  }

  deleteTechnician(technician: Technician): void {
    const confirmed = window.confirm(`¿Deseas eliminar a ${technician.full_name}?`);

    if (!confirmed) {
      return;
    }

    this.http.delete(`${this.techniciansApiUrl}/${technician.id}`).subscribe({
      next: () => {
        this.technicianFeedback = 'Tecnico eliminado correctamente.';
        this.loadTechnicians();
      },
      error: () => {
        this.technicianFeedback = 'No se pudo eliminar el tecnico.';
      },
    });
  }

  toggleTechnicianStatus(technician: Technician): void {
    const nextStatus: TechnicianStatus =
      technician.status === 'disponible'
        ? 'ocupado'
        : technician.status === 'ocupado'
          ? 'fuera_de_servicio'
          : 'disponible';

    this.http
      .put<Technician>(`${this.techniciansApiUrl}/${technician.id}`, {
        full_name: technician.full_name,
        phone: technician.phone,
        email: technician.email,
        specialty: technician.specialty,
        status: nextStatus,
      })
      .subscribe({
        next: () => {
          this.loadTechnicians();
        },
      });
  }

  cycleWorkshopApproval(workshop: WorkshopDisplayItem): void {
    const nextStatus: WorkshopApprovalStatus =
      workshop.approval_status === 'pendiente'
        ? 'aprobada'
        : workshop.approval_status === 'aprobada'
          ? 'rechazada'
          : 'pendiente';

    this.workshopApprovalState[workshop.id] = nextStatus;
    this.persistWorkshopApprovalState();
  }

  editWorkshop(workshop: WorkshopDisplayItem): void {
    this.editingWorkshopId = workshop.id;
    this.workshopEditFeedback = '';
    this.workshopForm = {
      workshop_name: workshop.workshop_name,
      contact_name: workshop.contact_name,
      phone: workshop.phone,
      email: workshop.email,
      zone: workshop.zone,
      specialty: workshop.specialty,
    };
    this.showWorkshopEditModal = true;
  }

  deleteWorkshop(workshop: WorkshopDisplayItem): void {
    const confirmed = window.confirm(`¿Deseas eliminar el taller ${workshop.workshop_name}?`);

    if (!confirmed) {
      return;
    }

    this.http.delete(`${this.workshopsApiUrl}/${workshop.id}`).subscribe({
      next: () => {
        delete this.workshopApprovalState[workshop.id];
        this.persistWorkshopApprovalState();
        this.loadWorkshops();
      },
      error: () => {
        window.alert('No se pudo eliminar el taller.');
      },
    });
  }

  cancelWorkshopEdit(): void {
    this.showWorkshopEditModal = false;
    this.editingWorkshopId = null;
    this.isSavingWorkshop = false;
    this.workshopEditFeedback = '';
    this.workshopForm = this.createEmptyWorkshopForm();
  }

  submitWorkshopEdit(): void {
    if (!this.editingWorkshopId) {
      return;
    }

    const target = this.workshops.find((item) => item.id === this.editingWorkshopId);

    if (!target) {
      this.workshopEditFeedback = 'No se encontró el taller que intentas actualizar.';
      return;
    }

    const payload: WorkshopRegistration = {
      ...target,
      workshop_name: this.workshopForm.workshop_name.trim(),
      contact_name: this.workshopForm.contact_name.trim(),
      phone: this.workshopForm.phone.trim(),
      email: this.workshopForm.email.trim(),
      zone: this.workshopForm.zone.trim(),
      specialty: this.workshopForm.specialty.trim(),
    };

    if (
      !payload.workshop_name ||
      !payload.contact_name ||
      !payload.phone ||
      !payload.zone ||
      !payload.specialty
    ) {
      this.workshopEditFeedback = 'Completa Taller, Responsable, Contacto, Zona y Especialidad.';
      return;
    }

    this.isSavingWorkshop = true;
    this.workshopEditFeedback = '';

    this.http.put<WorkshopRegistration>(`${this.workshopsApiUrl}/${this.editingWorkshopId}`, payload).subscribe({
      next: () => {
        this.isSavingWorkshop = false;
        this.cancelWorkshopEdit();
        this.loadWorkshops();
      },
      error: () => {
        this.isSavingWorkshop = false;
        this.workshopEditFeedback = 'No se pudo actualizar el taller.';
      },
    });
  }

  loadWorkshops(): void {
    this.isLoading = true;

    this.http.get<WorkshopRegistration[]>(this.workshopsApiUrl).subscribe({
      next: (workshops) => {
        this.workshops = workshops;
        this.workshopsPage = 1;
        this.isLoading = false;
        this.refreshStats();
      },
      error: () => {
        this.workshops = [];
        this.workshopsPage = 1;
        this.isLoading = false;
        this.refreshStats();
      },
    });
  }

  loadTechnicians(): void {
    this.isTechniciansLoading = true;

    this.http.get<Technician[]>(this.techniciansApiUrl).subscribe({
      next: (technicians) => {
        this.technicians = technicians;
        this.isTechniciansLoading = false;
        this.refreshStats();
      },
      error: () => {
        this.technicians = [];
        this.isTechniciansLoading = false;
        this.refreshStats();
      },
    });
  }

  loadClients(): void {
    this.isClientsLoading = true;

    this.http.get<Client[]>(this.clientsApiUrl).subscribe({
      next: (clients) => {
        this.clients = clients;
        this.isClientsLoading = false;
        this.refreshStats();
      },
      error: () => {
        this.clients = [];
        this.isClientsLoading = false;
        this.refreshStats();
      },
    });
  }

  toggleClientStatus(client: Client): void {
    const nextStatus: ClientStatus = client.status === 'active' ? 'suspended' : 'active';

    this.http
      .put<Client>(`${this.clientsApiUrl}/${client.id}/status`, {
        status: nextStatus,
      })
      .subscribe({
        next: () => {
          this.loadClients();
        },
      });
  }

  editClient(client: Client): void {
    this.editingClientId = client.id;
    this.clientEditFeedback = '';
    this.clientForm = {
      identity_card: client.identity_card,
      full_name: client.full_name,
      email: client.email,
      phone: client.phone,
      role: client.role,
      status: client.status,
      accepted_terms: client.accepted_terms,
    };
    this.showClientEditModal = true;
  }

  cancelClientEdit(): void {
    this.showClientEditModal = false;
    this.editingClientId = null;
    this.isSavingClient = false;
    this.clientEditFeedback = '';
    this.clientForm = this.createEmptyClientForm();
  }

  submitClientEdit(): void {
    if (!this.editingClientId) {
      return;
    }

    const payload = {
      identity_card: this.clientForm.identity_card.trim(),
      full_name: this.clientForm.full_name.trim(),
      email: this.clientForm.email.trim(),
      phone: this.clientForm.phone.trim(),
      role: this.clientForm.role.trim(),
      status: this.clientForm.status,
      accepted_terms: this.clientForm.accepted_terms,
    };

    if (!payload.identity_card || !payload.full_name || !payload.email || !payload.phone || !payload.role) {
      this.clientEditFeedback = 'Completa carnet, nombre, correo, telefono y rol.';
      return;
    }

    this.isSavingClient = true;
    this.clientEditFeedback = '';

    this.http.put<Client>(`${this.clientsApiUrl}/${this.editingClientId}`, payload).subscribe({
      next: () => {
        this.isSavingClient = false;
        this.cancelClientEdit();
        this.loadClients();
      },
      error: () => {
        this.isSavingClient = false;
        this.clientEditFeedback = 'No se pudo actualizar el cliente.';
      },
    });
  }

  deleteClient(client: Client): void {
    const confirmed = window.confirm(`¿Deseas eliminar a ${client.full_name}?`);

    if (!confirmed) {
      return;
    }

    this.http.delete(`${this.clientsApiUrl}/${client.id}`).subscribe({
      next: () => {
        this.loadClients();
      },
      error: () => {
        window.alert('No se pudo eliminar el cliente.');
      },
    });
  }

  private normalizeWorkshopApprovalStatus(value: string): WorkshopApprovalStatus | null {
    const normalized = value.trim().toLowerCase();

    if (normalized === 'pendiente' || normalized === 'aprobada' || normalized === 'rechazada') {
      return normalized;
    }

    return null;
  }

  private readWorkshopApprovalState(): Record<number, WorkshopApprovalStatus> {
    if (typeof window === 'undefined') {
      return {};
    }

    try {
      const raw = window.localStorage.getItem(this.workshopApprovalStorageKey);
      return raw ? JSON.parse(raw) : {};
    } catch {
      return {};
    }
  }

  private persistWorkshopApprovalState(): void {
    if (typeof window === 'undefined') {
      return;
    }

    window.localStorage.setItem(this.workshopApprovalStorageKey, JSON.stringify(this.workshopApprovalState));
  }

  private refreshStats(): void {
    this.stats = this.stats.map((stat) => {
      if (stat.label === 'Talleres registrados') {
        return {
          ...stat,
          value: String(this.workshops.length),
          detail: this.workshops.length
            ? 'Solicitudes recibidas desde el formulario de afiliacion.'
            : 'Aun no se recibieron solicitudes de taller.',
        };
      }

      if (stat.label === 'Tecnicos disponibles') {
        return {
          ...stat,
          value: String(this.techniciansByStatus('disponible')),
          detail: this.technicians.length
            ? 'Estado actualizado segun el tecnico registrado en el panel.'
            : 'Aun no se registraron tecnicos en el sistema.',
        };
      }

      if (stat.label === 'Clientes activos') {
        const activeClients = this.clients.filter((client) => client.status === 'active').length;
        return {
          ...stat,
          value: String(activeClients),
          detail: this.clients.length
            ? 'Clientes con acceso habilitado para autenticacion movil.'
            : 'Aun no se registraron clientes en el sistema.',
        };
      }

      if (stat.label === 'Cobertura') {
        return {
          ...stat,
          value: `${this.uniqueZonesCount || 0} zonas`,
          detail: this.uniqueZonesCount
            ? 'Cobertura detectada en zonas con alta circulacion y demanda.'
            : 'Sin zonas activas registradas todavia.',
        };
      }

      return stat;
    });
  }
}
