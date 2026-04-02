import { Component, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private readonly http = inject(HttpClient);

  apiStatus = 'Checking backend...';

  constructor() {
    this.http
      .get<{ status: string; database: string }>('http://localhost:8000/api/health')
      .subscribe({
        next: (response) => {
          this.apiStatus = `API ${response.status} | DB ${response.database}`;
        },
        error: () => {
          this.apiStatus = 'Backend not available yet';
        },
      });
  }
}

