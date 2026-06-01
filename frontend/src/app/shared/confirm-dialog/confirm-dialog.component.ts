import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatDialogModule, MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

export interface ConfirmDialogData {
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  type?: 'warning' | 'danger' | 'info';
  icon?: string;
}

@Component({
  selector: 'app-confirm-dialog',
  standalone: true,
  imports: [CommonModule, MatDialogModule, MatIconModule, MatButtonModule],
  template: `
    <div class="confirm-dialog">
      <div class="dialog-icon" [ngClass]="data.type || 'warning'">
        <mat-icon>{{ data.icon || getDefaultIcon() }}</mat-icon>
      </div>
      <h2 class="dialog-title">{{ data.title }}</h2>
      <p class="dialog-message">{{ data.message }}</p>
      <div class="dialog-actions">
        <button class="btn btn-secondary" (click)="onCancel()">
          {{ data.cancelText || 'Cancel' }}
        </button>
        <button class="btn" [ngClass]="getConfirmClass()" (click)="onConfirm()">
          {{ data.confirmText || 'Confirm' }}
        </button>
      </div>
    </div>
  `,
  styles: [`
    .confirm-dialog {
      padding: var(--space-xl);
      text-align: center;
      min-width: 360px;
    }

    .dialog-icon {
      width: 56px;
      height: 56px;
      border-radius: var(--radius-full);
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 0 auto var(--space-lg);
    }

    .dialog-icon.warning {
      background: rgba(245, 158, 11, 0.15);
      color: var(--color-accent-amber);
    }

    .dialog-icon.danger {
      background: rgba(244, 63, 94, 0.15);
      color: var(--color-accent-rose);
    }

    .dialog-icon.info {
      background: rgba(59, 130, 246, 0.15);
      color: var(--color-accent-blue);
    }

    .dialog-icon mat-icon {
      font-size: 28px;
      width: 28px;
      height: 28px;
    }

    .dialog-title {
      font-size: var(--font-size-xl);
      font-weight: 700;
      color: var(--color-text-primary);
      margin-bottom: var(--space-sm);
    }

    .dialog-message {
      color: var(--color-text-secondary);
      font-size: var(--font-size-sm);
      line-height: 1.6;
      margin-bottom: var(--space-xl);
    }

    .dialog-actions {
      display: flex;
      gap: var(--space-md);
      justify-content: center;
    }

    .dialog-actions .btn {
      min-width: 120px;
    }
  `]
})
export class ConfirmDialogComponent {
  data = inject<ConfirmDialogData>(MAT_DIALOG_DATA);
  private dialogRef = inject(MatDialogRef<ConfirmDialogComponent>);

  getDefaultIcon(): string {
    switch (this.data.type) {
      case 'danger': return 'warning';
      case 'info': return 'info';
      default: return 'help_outline';
    }
  }

  getConfirmClass(): string {
    return this.data.type === 'danger' ? 'btn-danger' : 'btn-primary';
  }

  onConfirm(): void {
    this.dialogRef.close(true);
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }
}
