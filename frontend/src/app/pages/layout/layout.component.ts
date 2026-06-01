import { Component, inject, OnInit, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { SidebarComponent } from '../../shared/sidebar/sidebar.component';
import { TopbarComponent } from '../../shared/topbar/topbar.component';
import { UIStore } from '../../store/ui.store';

@Component({
  selector: 'app-layout',
  standalone: true,
  imports: [CommonModule, RouterOutlet, SidebarComponent, TopbarComponent],
  template: `
    <div class="app-layout" [class.sidebar-collapsed]="uiStore.sidebarCollapsed()">
      <app-sidebar></app-sidebar>
      <div class="main-area">
        <app-topbar></app-topbar>
        <main class="main-content">
          <router-outlet></router-outlet>
        </main>
      </div>
    </div>
  `,
  styles: [`
    .app-layout {
      display: flex;
      min-height: 100vh;
    }

    .main-area {
      flex: 1;
      margin-left: var(--sidebar-width);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
      transition: margin-left var(--transition-slow);
    }

    .sidebar-collapsed .main-area {
      margin-left: var(--sidebar-collapsed-width);
    }

    .main-content {
      flex: 1;
      overflow-y: auto;
    }

    @media (max-width: 768px) {
      .main-area {
        margin-left: 0;
      }
    }
  `]
})
export class LayoutComponent implements OnInit {
  uiStore = inject(UIStore);

  ngOnInit(): void {
    this.checkScreenSize();
  }

  @HostListener('window:resize')
  onResize(): void {
    this.checkScreenSize();
  }

  private checkScreenSize(): void {
    const isMobile = window.innerWidth < 768;
    this.uiStore.setMobile(isMobile);
    if (isMobile) {
      this.uiStore.setSidebarCollapsed(true);
    }
  }
}
