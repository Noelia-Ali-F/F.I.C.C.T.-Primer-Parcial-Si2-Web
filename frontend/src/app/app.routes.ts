import { Routes } from '@angular/router';

import { DashboardPageComponent } from './pages/dashboard-page.component';
import { HomePageComponent } from './pages/home-page.component';
import { LoginPageComponent } from './pages/login-page.component';
import { MapPageComponent } from './pages/map-page.component';
import { NotFoundPageComponent } from './pages/not-found-page.component';
import { PlanesPageComponent } from './pages/planes-page.component';
import { SectionPageComponent } from './pages/section-page.component';
import { ServiciosPageComponent } from './pages/servicios-page.component';

export const appRoutes: Routes = [
  {
    path: '',
    component: HomePageComponent,
    title: 'Inicio | Automóvil Club Boliviano',
  },
  {
    path: 'suscripciones',
    redirectTo: 'planes',
    pathMatch: 'full',
  },
  {
    path: 'nosotros',
    redirectTo: 'planes',
    pathMatch: 'full',
  },
  {
    path: 'planes',
    component: PlanesPageComponent,
    title: 'Planes | Talleres Socios',
  },
  {
    path: 'novedades',
    redirectTo: 'planes',
    pathMatch: 'full',
  },
  {
    path: 'servicios',
    component: ServiciosPageComponent,
    title: 'Servicios | Asistencia y Auxilio',
  },
  {
    path: 'mapa',
    component: MapPageComponent,
    title: 'Mapa | Santa Cruz de la Sierra',
  },
  {
    path: 'login',
    component: LoginPageComponent,
    title: 'Iniciar sesión | Taller ACB Asistencia',
  },
  {
    path: 'dashboard',
    component: DashboardPageComponent,
    title: 'Dashboard | Taller ACB Asistencia',
  },
  {
    path: 'escuela',
    redirectTo: 'mapa',
    pathMatch: 'full',
  },
  {
    path: 'contacto',
    component: SectionPageComponent,
    data: { section: 'contacto' },
    title: 'Contacto | Automóvil Club Boliviano',
  },
  {
    path: '**',
    component: NotFoundPageComponent,
    title: 'Página no encontrada',
  },
];
