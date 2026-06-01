import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, ActivatedRoute, Router } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { DocumentService } from '../../../core/services/document.service';
import { DocumentStore } from '../../../store/document.store';
import { Document, DocumentFilter, Category } from '../../../core/models/document.model';
import { FileSizePipe } from '../../../shared/pipes/file-size.pipe';
import { TimeAgoPipe } from '../../../shared/pipes/time-ago.pipe';
import { FileIconPipe } from '../../../shared/pipes/file-icon.pipe';
import { EmptyStateComponent } from '../../../shared/empty-state/empty-state.component';
import { LoadingSpinnerComponent } from '../../../shared/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../shared/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-document-list',
  standalone: true,
  imports: [
    CommonModule, RouterModule, FormsModule, MatIconModule, MatMenuModule, MatTooltipModule,
    FileSizePipe, TimeAgoPipe, FileIconPipe, EmptyStateComponent, LoadingSpinnerComponent
  ],
  templateUrl: './document-list.component.html',
  styleUrls: ['./document-list.component.css']
})
export class DocumentListComponent implements OnInit {
  private documentService = inject(DocumentService);
  private dialog = inject(MatDialog);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  store = inject(DocumentStore);

  categories: Category[] = [
    { id: '1', name: 'All Documents', icon: 'folder' },
    { id: '2', name: 'Reports', icon: 'assessment' },
    { id: '3', name: 'Presentations', icon: 'slideshow' },
    { id: '4', name: 'Spreadsheets', icon: 'table_chart' },
    { id: '5', name: 'Images', icon: 'image' },
    { id: '6', name: 'Code', icon: 'code' },
  ];

  searchQuery = '';
  sortOptions = [
    { value: 'createdAt', label: 'Date Created' },
    { value: 'title', label: 'Name' },
    { value: 'fileSize', label: 'Size' },
    { value: 'updatedAt', label: 'Last Modified' },
  ];
  currentSort = 'createdAt';
  currentSortOrder: 'asc' | 'desc' = 'desc';

  ngOnInit(): void {
    this.loadDocuments();
  }

  loadDocuments(): void {
    this.store.setLoading(true);
    const filter: DocumentFilter = {
      ...this.store.filters(),
      search: this.searchQuery,
      page: this.store.currentPage(),
      pageSize: this.store.pageSize(),
      sortBy: this.currentSort,
      sortOrder: this.currentSortOrder,
    };

    this.documentService.getDocuments(filter).subscribe({
      next: (response) => {
        this.store.setDocuments(response.documents);
        this.store.setTotal(response.total);
        this.store.setLoading(false);
      },
      error: () => {
        // Use mock data for demo
        this.store.setDocuments(this.getMockDocs());
        this.store.setTotal(24);
        this.store.setLoading(false);
      }
    });
  }

  onSearch(): void {
    this.store.setPage(1);
    this.loadDocuments();
  }

  onSortChange(sortBy: string): void {
    if (this.currentSort === sortBy) {
      this.currentSortOrder = this.currentSortOrder === 'asc' ? 'desc' : 'asc';
    } else {
      this.currentSort = sortBy;
      this.currentSortOrder = 'desc';
    }
    this.loadDocuments();
  }

  onPageChange(page: number): void {
    this.store.setPage(page);
    this.loadDocuments();
  }

  toggleView(mode: 'grid' | 'list'): void {
    this.store.setViewMode(mode);
  }

  deleteDocument(doc: Document, event: Event): void {
    event.stopPropagation();
    event.preventDefault();

    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Delete Document',
        message: `Are you sure you want to delete "${doc.title}"? This action cannot be undone.`,
        confirmText: 'Delete',
        type: 'danger',
        icon: 'delete_forever'
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.documentService.deleteDocument(doc.uuid).subscribe({
          next: () => this.store.removeDocument(doc.uuid),
          error: () => this.store.removeDocument(doc.uuid) // demo mode
        });
      }
    });
  }

  getAccessIcon(level: string): string {
    switch (level) {
      case 'private': return 'lock';
      case 'department': return 'group';
      case 'public': return 'public';
      default: return 'lock';
    }
  }

  get pages(): number[] {
    const total = this.store.totalPages();
    const current = this.store.currentPage();
    const pages: number[] = [];
    const start = Math.max(1, current - 2);
    const end = Math.min(total, current + 2);
    for (let i = start; i <= end; i++) pages.push(i);
    return pages;
  }

  private getMockDocs(): Document[] {
    const mockDocs: Partial<Document>[] = [
      { uuid: '1', title: 'Q4 Financial Report 2024', fileName: 'Q4_Report.pdf', fileType: 'pdf', fileSize: 2457600, createdAt: new Date(Date.now() - 120000).toISOString(), owner: { id: '1', name: 'Alice Chen', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '1', name: 'Finance', color: '#3B82F6' }], ocrCompleted: true, downloadCount: 14, accessLevel: 'department', mimeType: 'application/pdf', storagePath: '', versions: [], metadata: {} },
      { uuid: '2', title: 'Product Roadmap 2025', fileName: 'Roadmap.docx', fileType: 'docx', fileSize: 1048576, createdAt: new Date(Date.now() - 900000).toISOString(), owner: { id: '2', name: 'Bob Smith', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '2', name: 'Product', color: '#8B5CF6' }], ocrCompleted: false, downloadCount: 28, accessLevel: 'public', mimeType: 'application/vnd.openxmlformats', storagePath: '', versions: [], metadata: {} },
      { uuid: '3', title: 'Brand Guidelines v3', fileName: 'Brand_Guide.pdf', fileType: 'pdf', fileSize: 5242880, createdAt: new Date(Date.now() - 3600000).toISOString(), owner: { id: '3', name: 'Sarah Park', email: '', avatar: '' }, aiProcessed: false, tags: [{ id: '3', name: 'Design', color: '#EC4899' }], ocrCompleted: true, downloadCount: 55, accessLevel: 'public', mimeType: 'application/pdf', storagePath: '', versions: [], metadata: {} },
      { uuid: '4', title: 'Sprint Retrospective Notes', fileName: 'Sprint_Notes.md', fileType: 'md', fileSize: 32768, createdAt: new Date(Date.now() - 7200000).toISOString(), owner: { id: '1', name: 'Alice Chen', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '4', name: 'Engineering', color: '#06B6D4' }], ocrCompleted: false, downloadCount: 8, accessLevel: 'private', mimeType: 'text/markdown', storagePath: '', versions: [], metadata: {} },
      { uuid: '5', title: 'Budget Analysis 2024', fileName: 'Budget_2024.xlsx', fileType: 'xlsx', fileSize: 786432, createdAt: new Date(Date.now() - 18000000).toISOString(), owner: { id: '4', name: 'Mike Johnson', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '1', name: 'Finance', color: '#3B82F6' }], ocrCompleted: false, downloadCount: 19, accessLevel: 'department', mimeType: 'application/xlsx', storagePath: '', versions: [], metadata: {} },
      { uuid: '6', title: 'API Documentation', fileName: 'API_Docs.md', fileType: 'md', fileSize: 65536, createdAt: new Date(Date.now() - 43200000).toISOString(), owner: { id: '2', name: 'Bob Smith', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '4', name: 'Engineering', color: '#06B6D4' }], ocrCompleted: false, downloadCount: 42, accessLevel: 'public', mimeType: 'text/markdown', storagePath: '', versions: [], metadata: {} },
      { uuid: '7', title: 'Marketing Campaign Strategy', fileName: 'Campaign_Strategy.pptx', fileType: 'pptx', fileSize: 3145728, createdAt: new Date(Date.now() - 86400000).toISOString(), owner: { id: '5', name: 'Emma Davis', email: '', avatar: '' }, aiProcessed: false, tags: [{ id: '5', name: 'Marketing', color: '#F59E0B' }], ocrCompleted: false, downloadCount: 31, accessLevel: 'department', mimeType: 'application/pptx', storagePath: '', versions: [], metadata: {} },
      { uuid: '8', title: 'Employee Handbook', fileName: 'Handbook.pdf', fileType: 'pdf', fileSize: 4194304, createdAt: new Date(Date.now() - 172800000).toISOString(), owner: { id: '6', name: 'HR Team', email: '', avatar: '' }, aiProcessed: true, tags: [{ id: '6', name: 'HR', color: '#10B981' }], ocrCompleted: true, downloadCount: 156, accessLevel: 'public', mimeType: 'application/pdf', storagePath: '', versions: [], metadata: {} },
    ];
    return mockDocs as Document[];
  }
}
