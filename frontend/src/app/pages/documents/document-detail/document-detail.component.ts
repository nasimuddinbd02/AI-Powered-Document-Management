import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatMenuModule } from '@angular/material/menu';
import { MatDialog } from '@angular/material/dialog';
import { DocumentService } from '../../../core/services/document.service';
import { AIService } from '../../../core/services/ai.service';
import { Document, DocumentVersion } from '../../../core/models/document.model';
import { AISummary } from '../../../core/models/ai.model';
import { FileSizePipe } from '../../../shared/pipes/file-size.pipe';
import { TimeAgoPipe } from '../../../shared/pipes/time-ago.pipe';
import { FileIconPipe } from '../../../shared/pipes/file-icon.pipe';
import { LoadingSpinnerComponent } from '../../../shared/loading-spinner/loading-spinner.component';
import { ConfirmDialogComponent } from '../../../shared/confirm-dialog/confirm-dialog.component';

@Component({
  selector: 'app-document-detail',
  standalone: true,
  imports: [
    CommonModule, RouterModule, MatIconModule, MatTabsModule, MatMenuModule,
    FileSizePipe, TimeAgoPipe, FileIconPipe, LoadingSpinnerComponent
  ],
  templateUrl: './document-detail.component.html',
  styleUrls: ['./document-detail.component.css']
})
export class DocumentDetailComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private documentService = inject(DocumentService);
  private aiService = inject(AIService);
  private dialog = inject(MatDialog);

  document: Document | null = null;
  aiSummary: AISummary | null = null;
  isLoading = true;
  isSummarizing = false;
  activeTab = 0;

  ngOnInit(): void {
    const uuid = this.route.snapshot.paramMap.get('id');
    if (uuid) {
      this.loadDocument(uuid);
    }
  }

  private loadDocument(uuid: string): void {
    this.documentService.getDocument(uuid).subscribe({
      next: (doc) => {
        this.document = doc;
        this.isLoading = false;
        if (doc.aiProcessed) this.loadSummary(uuid);
      },
      error: () => {
        // Mock data
        this.document = this.getMockDocument(uuid);
        this.isLoading = false;
      }
    });
  }

  private loadSummary(docId: string): void {
    this.aiService.getSummary(docId).subscribe({
      next: (summary) => this.aiSummary = summary,
      error: () => {
        this.aiSummary = {
          id: '1', documentId: docId, summary: 'This document provides a comprehensive overview of the quarterly financial performance, including revenue analysis, cost breakdowns, and projections for the next quarter. Key findings include a 15% increase in revenue compared to the previous quarter, driven primarily by the new product launch.',
          keyTopics: ['Revenue Analysis', 'Cost Management', 'Q4 Projections', 'Product Launch Impact'],
          entities: [
            { name: 'Q4 2024', type: 'date', relevance: 0.95 },
            { name: 'Finance Dept', type: 'organization', relevance: 0.88 },
            { name: 'Product X', type: 'concept', relevance: 0.82 },
          ],
          sentiment: 'positive', language: 'en', wordCount: 4520, readingTime: 18,
          generatedAt: new Date().toISOString()
        };
      }
    });
  }

  generateSummary(): void {
    if (!this.document) return;
    this.isSummarizing = true;
    this.aiService.summarizeDocument(this.document.uuid).subscribe({
      next: (summary) => {
        this.aiSummary = summary;
        this.isSummarizing = false;
        if (this.document) this.document.aiProcessed = true;
      },
      error: () => {
        this.loadSummary(this.document!.uuid);
        this.isSummarizing = false;
      }
    });
  }

  downloadDocument(): void {
    if (!this.document) return;
    this.documentService.downloadDocument(this.document.uuid).subscribe({
      next: (blob) => {
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = this.document!.fileName;
        a.click();
        URL.revokeObjectURL(url);
      }
    });
  }

  deleteDocument(): void {
    if (!this.document) return;
    const dialogRef = this.dialog.open(ConfirmDialogComponent, {
      data: {
        title: 'Delete Document',
        message: `Are you sure you want to delete "${this.document.title}"? This action cannot be undone.`,
        confirmText: 'Delete',
        type: 'danger'
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.documentService.deleteDocument(this.document!.uuid).subscribe({
          next: () => this.router.navigate(['/documents']),
          error: () => this.router.navigate(['/documents'])
        });
      }
    });
  }

  getAccessLabel(level: string): string {
    const map: Record<string, string> = { private: 'Private', department: 'Department', public: 'Public' };
    return map[level] || level;
  }

  getAccessIcon(level: string): string {
    const map: Record<string, string> = { private: 'lock', department: 'group', public: 'public' };
    return map[level] || 'lock';
  }

  getMetadataKeys(): string[] {
    if (!this.document?.metadata) return [];
    return Object.keys(this.document.metadata);
  }

  private getMockDocument(uuid: string): Document {
    return {
      uuid, title: 'Q4 Financial Report 2024', description: 'Comprehensive quarterly financial report with revenue analysis, cost breakdowns, and projections.',
      fileName: 'Q4_Report.pdf', fileType: 'pdf', fileSize: 2457600, mimeType: 'application/pdf',
      storagePath: '/docs/Q4_Report.pdf', category: { id: '1', name: 'Reports', icon: 'assessment' },
      tags: [{ id: '1', name: 'Finance', color: '#3B82F6' }, { id: '2', name: 'Quarterly', color: '#10B981' }],
      metadata: { author: 'Finance Team', pages: '24', department: 'Finance' },
      accessLevel: 'department', owner: { id: '1', name: 'Alice Chen', email: 'alice@company.com', avatar: '' },
      versions: [
        { id: 'v3', versionNumber: 3, fileName: 'Q4_Report_v3.pdf', fileSize: 2457600, changeSummary: 'Final version with updated projections', uploadedBy: { id: '1', name: 'Alice Chen' }, createdAt: new Date(Date.now() - 3600000).toISOString(), downloadUrl: '#' },
        { id: 'v2', versionNumber: 2, fileName: 'Q4_Report_v2.pdf', fileSize: 2200000, changeSummary: 'Added cost breakdown section', uploadedBy: { id: '1', name: 'Alice Chen' }, createdAt: new Date(Date.now() - 86400000).toISOString(), downloadUrl: '#' },
        { id: 'v1', versionNumber: 1, fileName: 'Q4_Report_v1.pdf', fileSize: 1800000, changeSummary: 'Initial draft', uploadedBy: { id: '1', name: 'Alice Chen' }, createdAt: new Date(Date.now() - 172800000).toISOString(), downloadUrl: '#' },
      ],
      aiSummary: '', aiProcessed: true, ocrCompleted: true, downloadCount: 47,
      createdAt: new Date(Date.now() - 172800000).toISOString(),
      updatedAt: new Date(Date.now() - 3600000).toISOString(),
    };
  }
}
