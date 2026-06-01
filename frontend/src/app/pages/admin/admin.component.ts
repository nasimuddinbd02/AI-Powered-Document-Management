import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';

interface AdminUser {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
  lastLogin: string;
  documentsCount: number;
}

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [CommonModule, MatIconModule, MatMenuModule],
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
export class AdminComponent {
  users: AdminUser[] = [
    { id: '1', name: 'Alice Chen', email: 'alice@company.com', role: 'admin', status: 'active', lastLogin: '2 min ago', documentsCount: 145 },
    { id: '2', name: 'Bob Smith', email: 'bob@company.com', role: 'editor', status: 'active', lastLogin: '1 hour ago', documentsCount: 87 },
    { id: '3', name: 'Sarah Park', email: 'sarah@company.com', role: 'editor', status: 'active', lastLogin: '3 hours ago', documentsCount: 234 },
    { id: '4', name: 'Mike Johnson', email: 'mike@company.com', role: 'viewer', status: 'active', lastLogin: '1 day ago', documentsCount: 12 },
    { id: '5', name: 'Emma Davis', email: 'emma@company.com', role: 'editor', status: 'inactive', lastLogin: '2 weeks ago', documentsCount: 56 },
    { id: '6', name: 'James Wilson', email: 'james@company.com', role: 'viewer', status: 'active', lastLogin: '5 hours ago', documentsCount: 34 },
  ];

  adminStats = [
    { label: 'Total Users', value: '156', icon: 'people', color: 'blue', trend: '+12 this month' },
    { label: 'Active Sessions', value: '42', icon: 'wifi', color: 'emerald', trend: 'Current' },
    { label: 'Storage Used', value: '127 GB', icon: 'storage', color: 'purple', trend: 'of 500 GB' },
    { label: 'API Calls Today', value: '8,429', icon: 'api', color: 'cyan', trend: '+15% vs yesterday' },
  ];

  getRoleBadgeClass(role: string): string {
    const map: Record<string, string> = { admin: 'badge-danger', editor: 'badge-primary', viewer: 'badge-warning' };
    return map[role] || 'badge-primary';
  }
}
