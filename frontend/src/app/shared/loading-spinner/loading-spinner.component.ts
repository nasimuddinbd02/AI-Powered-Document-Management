import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-loading-spinner',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="spinner-wrapper" [class.overlay]="overlay">
      <div class="spinner">
        <div class="spinner-ring"></div>
        <div class="spinner-ring inner"></div>
      </div>
      <p class="spinner-message" *ngIf="message">{{ message }}</p>
    </div>
  `,
  styles: [`
    .spinner-wrapper {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--space-xl);
      gap: var(--space-lg);
    }

    .spinner-wrapper.overlay {
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      background: rgba(10, 22, 40, 0.8);
      backdrop-filter: blur(8px);
      z-index: 9999;
    }

    .spinner {
      position: relative;
      width: 48px;
      height: 48px;
    }

    .spinner-ring {
      position: absolute;
      width: 100%;
      height: 100%;
      border-radius: 50%;
      border: 3px solid transparent;
      border-top-color: var(--color-accent-blue);
      border-right-color: var(--color-accent-purple);
      animation: spin 1s linear infinite;
    }

    .spinner-ring.inner {
      width: 70%;
      height: 70%;
      top: 15%;
      left: 15%;
      border-top-color: var(--color-accent-purple);
      border-right-color: var(--color-accent-cyan);
      animation-direction: reverse;
      animation-duration: 0.8s;
    }

    .spinner-message {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
      font-weight: 500;
      animation: pulse 2s ease-in-out infinite;
    }

    @keyframes spin {
      to { transform: rotate(360deg); }
    }
  `]
})
export class LoadingSpinnerComponent {
  @Input() message = '';
  @Input() overlay = false;
}
