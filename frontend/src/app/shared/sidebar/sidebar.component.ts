import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { UIStore } from '../../store/ui.store';
import { AuthService } from '../../core/services/auth.service';

interface NavItem {
  icon: string;
  label: string;
  route: string;
  roles?: string[];
}

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, MatTooltipModule],
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent {
  uiStore = inject(UIStore);
  authService = inject(AuthService);

  navItems: NavItem[] = [
    { icon: 'dashboard', label: 'Dashboard', route: '/dashboard' },
    { icon: 'description', label: 'Documents', route: '/documents' },
    { icon: 'cloud_upload', label: 'Upload', route: '/documents/upload' },
    { icon: 'search', label: 'Search', route: '/search' },
    { icon: 'smart_toy', label: 'AI Assistant', route: '/ai-assistant' },
    { icon: 'admin_panel_settings', label: 'Admin', route: '/admin', roles: ['admin'] },
    { icon: 'settings', label: 'Settings', route: '/settings' }
  ];

  get visibleNavItems(): NavItem[] {
    return this.navItems.filter(item => {
      if (!item.roles) return true;
      return item.roles.some(role => this.authService.hasRole(role));
    });
  }

  toggleSidebar(): void {
    this.uiStore.toggleSidebar();
  }
}
