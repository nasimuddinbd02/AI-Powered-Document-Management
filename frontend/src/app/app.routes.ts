import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { roleGuard } from './core/guards/role.guard';

export const routes: Routes = [
  // Auth (public)
  { path: 'login', loadComponent: () => import('./pages/login/login.component').then(m => m.LoginComponent) },
  { path: 'register', loadComponent: () => import('./pages/register/register.component').then(m => m.RegisterComponent) },

  // Protected layout routes
  {
    path: '',
    loadComponent: () => import('./pages/layout/layout.component').then(m => m.LayoutComponent),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'dashboard', pathMatch: 'full' },
      {
        path: 'dashboard',
        loadComponent: () => import('./pages/dashboard/dashboard.component').then(m => m.DashboardComponent),
        data: { title: 'Dashboard' }
      },
      {
        path: 'documents',
        children: [
          {
            path: '',
            loadComponent: () => import('./pages/documents/document-list/document-list.component').then(m => m.DocumentListComponent),
            data: { title: 'Documents' }
          },
          {
            path: 'upload',
            loadComponent: () => import('./pages/documents/document-upload/document-upload.component').then(m => m.DocumentUploadComponent),
            data: { title: 'Upload Document' }
          },
          {
            path: ':id',
            loadComponent: () => import('./pages/documents/document-detail/document-detail.component').then(m => m.DocumentDetailComponent),
            data: { title: 'Document Detail' }
          }
        ]
      },
      {
        path: 'search',
        loadComponent: () => import('./pages/search/search.component').then(m => m.SearchComponent),
        data: { title: 'Search' }
      },
      {
        path: 'ai-assistant',
        loadComponent: () => import('./pages/ai-assistant/ai-assistant.component').then(m => m.AIAssistantComponent),
        data: { title: 'AI Assistant' }
      },
      {
        path: 'settings',
        loadComponent: () => import('./pages/settings/settings.component').then(m => m.SettingsComponent),
        data: { title: 'Settings' }
      },
      {
        path: 'admin',
        loadComponent: () => import('./pages/admin/admin.component').then(m => m.AdminComponent),
        canActivate: [roleGuard],
        data: { title: 'Administration', roles: ['admin'] }
      }
    ]
  },

  // Fallback
  { path: '**', redirectTo: 'dashboard' }
];
