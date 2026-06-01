import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { DocumentService } from '../../core/services/document.service';
import { FileSizePipe } from '../../shared/pipes/file-size.pipe';
import { TimeAgoPipe } from '../../shared/pipes/time-ago.pipe';
import { FileIconPipe } from '../../shared/pipes/file-icon.pipe';
import { Document } from '../../core/models/document.model';

interface DashboardStats {
  totalDocuments: number;
  recentUploads: number;
  aiSummaries: number;
  storageUsed: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterModule, MatIconModule, FileSizePipe, TimeAgoPipe, FileIconPipe],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  private documentService = inject(DocumentService);

  stats: DashboardStats = {
    totalDocuments: 1284,
    recentUploads: 47,
    aiSummaries: 892,
    storageUsed: 4831838208 // ~4.5GB
  };

  recentDocuments: Document[] = [];
  isLoading = true;
  activityItems = [
    { icon: 'cloud_upload', text: 'You uploaded "Q4 Financial Report.pdf"', time: '2 min ago', color: 'blue' },
    { icon: 'smart_toy', text: 'AI summary generated for "Project Roadmap.docx"', time: '15 min ago', color: 'purple' },
    { icon: 'share', text: 'Sarah shared "Design System v3" with you', time: '1 hour ago', color: 'emerald' },
    { icon: 'edit', text: 'Updated "Marketing Strategy 2024.pptx"', time: '3 hours ago', color: 'amber' },
    { icon: 'delete', text: 'Removed "Draft Notes.txt" from trash', time: '5 hours ago', color: 'rose' },
  ];

  quickActions = [
    { icon: 'cloud_upload', label: 'Upload Document', route: '/documents/upload', gradient: 'var(--gradient-primary)' },
    { icon: 'search', label: 'Smart Search', route: '/search', gradient: 'var(--gradient-secondary)' },
    { icon: 'smart_toy', label: 'Ask AI', route: '/ai-assistant', gradient: 'var(--gradient-accent)' },
    { icon: 'folder', label: 'Browse All', route: '/documents', gradient: 'var(--gradient-success)' },
  ];

  ngOnInit(): void {
    this.loadDashboard();
  }

  private loadDashboard(): void {
    this.documentService.getRecentDocuments(8).subscribe({
      next: (docs) => {
        this.recentDocuments = docs;
        this.isLoading = false;
      },
      error: () => {
        // Use mock data for demo
        this.recentDocuments = this.getMockDocuments();
        this.isLoading = false;
      }
    });

    this.documentService.getStats().subscribe({
      next: (s) => this.stats = s,
      error: () => {} // keep defaults
    });
  }

  private getMockDocuments(): Document[] {
    const base: Partial<Document>[] = [
      { uuid: '1', title: 'Q4 Financial Report', fileName: 'Q4_Report.pdf', fileType: 'pdf', fileSize: 2457600, createdAt: new Date(Date.now() - 120000).toISOString(), owner: { id: '1', name: 'You', email: '', avatar: '' }, aiProcessed: true, tags: [], ocrCompleted: true, downloadCount: 14, accessLevel: 'department', mimeType: 'application/pdf', storagePath: '', versions: [], metadata: {} },
      { uuid: '2', title: 'Project Roadmap 2024', fileName: 'Roadmap.docx', fileType: 'docx', fileSize: 1048576, createdAt: new Date(Date.now() - 900000).toISOString(), owner: { id: '1', name: 'You', email: '', avatar: '' }, aiProcessed: true, tags: [], ocrCompleted: false, downloadCount: 28, accessLevel: 'public', mimeType: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', storagePath: '', versions: [], metadata: {} },
      { uuid: '3', title: 'Brand Guidelines', fileName: 'Brand_Guide.pdf', fileType: 'pdf', fileSize: 5242880, createdAt: new Date(Date.now() - 3600000).toISOString(), owner: { id: '2', name: 'Sarah', email: '', avatar: '' }, aiProcessed: false, tags: [], ocrCompleted: true, downloadCount: 55, accessLevel: 'public', mimeType: 'application/pdf', storagePath: '', versions: [], metadata: {} },
      { uuid: '4', title: 'Sprint Planning Notes', fileName: 'Sprint_Notes.md', fileType: 'md', fileSize: 32768, createdAt: new Date(Date.now() - 7200000).toISOString(), owner: { id: '1', name: 'You', email: '', avatar: '' }, aiProcessed: true, tags: [], ocrCompleted: false, downloadCount: 8, accessLevel: 'private', mimeType: 'text/markdown', storagePath: '', versions: [], metadata: {} },
      { uuid: '5', title: 'Budget Analysis', fileName: 'Budget_2024.xlsx', fileType: 'xlsx', fileSize: 786432, createdAt: new Date(Date.now() - 18000000).toISOString(), owner: { id: '3', name: 'Mike', email: '', avatar: '' }, aiProcessed: true, tags: [], ocrCompleted: false, downloadCount: 19, accessLevel: 'department', mimeType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', storagePath: '', versions: [], metadata: {} },
      { uuid: '6', title: 'API Documentation', fileName: 'API_Docs.md', fileType: 'md', fileSize: 65536, createdAt: new Date(Date.now() - 43200000).toISOString(), owner: { id: '1', name: 'You', email: '', avatar: '' }, aiProcessed: true, tags: [], ocrCompleted: false, downloadCount: 42, accessLevel: 'public', mimeType: 'text/markdown', storagePath: '', versions: [], metadata: {} },
    ];
    return base as Document[];
  }
}
