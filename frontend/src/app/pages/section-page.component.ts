import { CommonModule } from '@angular/common';
import { Component, inject } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

import { sectionContent } from '../site-content';

@Component({
  selector: 'app-section-page',
  standalone: true,
  imports: [CommonModule, RouterLink],
  template: `
    <main class="page">
      <section class="section-hero">
        <p class="eyebrow">{{ content.eyebrow }}</p>
        <h1>{{ content.title }}</h1>
        <p class="lead">{{ content.intro }}</p>
      </section>

      <section class="spotlight compact">
        <div>
          <h2>Cómo está pensada esta vista</h2>
          <p>{{ content.lead }}</p>
        </div>

        <div class="quote-card">
          <p>{{ content.highlight }}</p>
        </div>
      </section>

      <section class="section">
        <div class="card-grid">
          <article class="info-card" *ngFor="let card of content.cards">
            <h3>{{ card.title }}</h3>
            <p>{{ card.description }}</p>
            <small *ngIf="card.detail">{{ card.detail }}</small>
          </article>
        </div>
      </section>

      <section class="closing-banner">
        <div>
          <p class="eyebrow">Siguiente paso</p>
          <h2>{{ content.cta }}</h2>
        </div>
        <a class="button primary" routerLink="/contacto">Ir a contacto</a>
      </section>
    </main>
  `,
  styleUrl: './shared-pages.css',
})
export class SectionPageComponent {
  private readonly route = inject(ActivatedRoute);

  readonly content =
    sectionContent[(this.route.snapshot.data['section'] as string) ?? 'nosotros'] ??
    sectionContent['nosotros'];
}
