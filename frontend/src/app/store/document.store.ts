import { Injectable, signal, computed } from '@angular/core';
import { Document, DocumentFilter } from '../core/models/document.model';

@Injectable({ providedIn: 'root' })
export class DocumentStore {
  private readonly _documents = signal<Document[]>([]);
  private readonly _selectedDocument = signal<Document | null>(null);
  private readonly _isLoading = signal(false);
  private readonly _totalDocuments = signal(0);
  private readonly _currentPage = signal(1);
  private readonly _pageSize = signal(12);
  private readonly _filters = signal<DocumentFilter>({});
  private readonly _viewMode = signal<'grid' | 'list'>('grid');

  readonly documents = this._documents.asReadonly();
  readonly selectedDocument = this._selectedDocument.asReadonly();
  readonly isLoading = this._isLoading.asReadonly();
  readonly totalDocuments = this._totalDocuments.asReadonly();
  readonly currentPage = this._currentPage.asReadonly();
  readonly pageSize = this._pageSize.asReadonly();
  readonly filters = this._filters.asReadonly();
  readonly viewMode = this._viewMode.asReadonly();
  readonly totalPages = computed(() => Math.ceil(this._totalDocuments() / this._pageSize()));
  readonly isEmpty = computed(() => this._documents().length === 0 && !this._isLoading());

  setDocuments(documents: Document[]): void {
    this._documents.set(documents);
  }

  setSelectedDocument(document: Document | null): void {
    this._selectedDocument.set(document);
  }

  setLoading(loading: boolean): void {
    this._isLoading.set(loading);
  }

  setTotal(total: number): void {
    this._totalDocuments.set(total);
  }

  setPage(page: number): void {
    this._currentPage.set(page);
  }

  setPageSize(size: number): void {
    this._pageSize.set(size);
  }

  setFilters(filters: DocumentFilter): void {
    this._filters.set(filters);
  }

  updateFilters(partial: Partial<DocumentFilter>): void {
    this._filters.set({ ...this._filters(), ...partial });
  }

  setViewMode(mode: 'grid' | 'list'): void {
    this._viewMode.set(mode);
  }

  removeDocument(uuid: string): void {
    this._documents.set(this._documents().filter(d => d.uuid !== uuid));
    this._totalDocuments.set(this._totalDocuments() - 1);
  }

  addDocument(document: Document): void {
    this._documents.set([document, ...this._documents()]);
    this._totalDocuments.set(this._totalDocuments() + 1);
  }
}
