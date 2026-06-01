import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';

@Component({
  selector: 'app-empty-state',
  standalone: true,
  imports: [CommonModule, MatIconModule],
  template: `
    <div class="empty-state animate-fade-in-up">
      <div class="empty-icon-wrapper">
        <div class="empty-icon-bg"></div>
        <mat-icon class="empty-icon">{{ icon }}</mat-icon>
      </div>
      <h3 class="empty-title">{{ title }}</h3>
      <p class="empty-message">{{ message }}</p>
      <ng-content></ng-content>
    </div>
  `,
  styles: [`
    .empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: var(--space-3xl) var(--space-xl);
      text-align: center;
    }

    .empty-icon-wrapper {
      position: relative;
      margin-bottom: var(--space-xl);
    }

    .empty-icon-bg {
      width: 100px;
      height: 100px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(139, 92, 246, 0.1));
      animation: float 3s ease-in-out infinite;
    }

    .empty-icon {
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 44px !important;
      width: 44px !important;
      height: 44px !important;
      color: var(--color-text-muted);
    }

    .empty-title {
      font-size: var(--font-size-xl);
      font-weight: 600;
      color: var(--color-text-primary);
      margin-bottom: var(--space-sm);
    }

    .empty-message {
      font-size: var(--font-size-sm);
      color: var(--color-text-tertiary);
      max-width: 360px;
      line-height: 1.6;
      margin-bottom: var(--space-lg);
    }

    @keyframes float {
      0%, 100% { transform: translateY(0px); }
      50% { transform: translateY(-8px); }
    }
  `]
})
export class EmptyStateComponent {
  @Input() icon = 'inbox';
  @Input() title = 'Nothing here yet';
  @Input() message = '';
}
