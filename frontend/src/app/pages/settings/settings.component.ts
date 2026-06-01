import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { AuthService } from '../../core/services/auth.service';
import { UIStore } from '../../store/ui.store';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, MatIconModule],
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent {
  private fb = inject(FormBuilder);
  authService = inject(AuthService);
  uiStore = inject(UIStore);

  activeSection = 'profile';
  isSaving = false;
  saveSuccess = false;

  profileForm: FormGroup;
  passwordForm: FormGroup;

  sections = [
    { id: 'profile', icon: 'person', label: 'Profile' },
    { id: 'security', icon: 'security', label: 'Security' },
    { id: 'preferences', icon: 'tune', label: 'Preferences' },
    { id: 'notifications', icon: 'notifications', label: 'Notifications' },
  ];

  constructor() {
    const user = this.authService.currentUser();
    this.profileForm = this.fb.group({
      name: [user?.name || '', [Validators.required]],
      email: [user?.email || '', [Validators.required, Validators.email]],
      department: [user?.department || '']
    });

    this.passwordForm = this.fb.group({
      currentPassword: ['', [Validators.required]],
      newPassword: ['', [Validators.required, Validators.minLength(8)]],
      confirmPassword: ['', [Validators.required]]
    });
  }

  saveProfile(): void {
    if (this.profileForm.invalid) return;
    this.isSaving = true;
    setTimeout(() => {
      this.isSaving = false;
      this.saveSuccess = true;
      setTimeout(() => this.saveSuccess = false, 3000);
    }, 1000);
  }

  changePassword(): void {
    if (this.passwordForm.invalid) return;
    this.isSaving = true;
    setTimeout(() => {
      this.isSaving = false;
      this.saveSuccess = true;
      this.passwordForm.reset();
      setTimeout(() => this.saveSuccess = false, 3000);
    }, 1000);
  }

  toggleTheme(): void {
    const next = this.uiStore.theme() === 'dark' ? 'light' : 'dark';
    this.uiStore.setTheme(next);
  }
}
