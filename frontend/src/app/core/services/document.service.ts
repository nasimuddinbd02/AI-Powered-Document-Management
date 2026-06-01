import { Injectable } from '@angular/core';
import { HttpClient, HttpParams, HttpEvent, HttpRequest } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import {
  Document,
  DocumentVersion,
  DocumentUploadRequest,
  DocumentListResponse,
  DocumentFilter,
  Category,
  Tag
} from '../models/document.model';

@Injectable({ providedIn: 'root' })
export class DocumentService {
  private readonly apiUrl = `${environment.apiUrl}/documents`;

  constructor(private http: HttpClient) {}

  getDocuments(filter?: DocumentFilter): Observable<DocumentListResponse> {
    let params = new HttpParams();
    if (filter) {
      if (filter.search) params = params.set('search', filter.search);
      if (filter.category) params = params.set('category', filter.category);
      if (filter.fileType) params = params.set('fileType', filter.fileType);
      if (filter.accessLevel) params = params.set('accessLevel', filter.accessLevel);
      if (filter.dateFrom) params = params.set('dateFrom', filter.dateFrom);
      if (filter.dateTo) params = params.set('dateTo', filter.dateTo);
      if (filter.sortBy) params = params.set('sortBy', filter.sortBy);
      if (filter.sortOrder) params = params.set('sortOrder', filter.sortOrder);
      if (filter.page) params = params.set('page', filter.page.toString());
      if (filter.pageSize) params = params.set('pageSize', filter.pageSize.toString());
      if (filter.tags?.length) params = params.set('tags', filter.tags.join(','));
    }
    return this.http.get<any>(`${this.apiUrl}/`, { params }).pipe(
      map(response => ({
        documents: (response.results || []).map(this.mapDocument),
        total: response.count || 0,
        page: response.current_page || 1,
        pageSize: response.page_size || 12,
        totalPages: response.total_pages || 1
      }))
    );
  }

  getDocument(uuid: string): Observable<Document> {
    return this.http.get<any>(`${this.apiUrl}/${uuid}/`).pipe(
      map(res => this.mapDocument(res))
    );
  }

  uploadDocument(request: DocumentUploadRequest): Observable<HttpEvent<Document>> {
    const formData = new FormData();
    formData.append('file', request.file);
    formData.append('title', request.title);
    if (request.description) formData.append('description', request.description);
    if (request.tags) formData.append('tags', JSON.stringify(request.tags));
    if (request.categoryId) formData.append('categoryId', request.categoryId);
    formData.append('accessLevel', request.accessLevel);
    if (request.metadata) formData.append('metadata', JSON.stringify(request.metadata));

    const req = new HttpRequest('POST', `${this.apiUrl}/`, formData, {
      reportProgress: true
    });
    return this.http.request<Document>(req);
  }

  updateDocument(uuid: string, data: Partial<Document>): Observable<Document> {
    return this.http.patch<Document>(`${this.apiUrl}/${uuid}/`, data);
  }

  deleteDocument(uuid: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${uuid}/`);
  }

  getVersions(uuid: string): Observable<DocumentVersion[]> {
    return this.http.get<DocumentVersion[]>(`${this.apiUrl}/${uuid}/versions/`);
  }

  uploadVersion(uuid: string, file: File, changeSummary?: string): Observable<HttpEvent<DocumentVersion>> {
    const formData = new FormData();
    formData.append('file', file);
    if (changeSummary) formData.append('changeSummary', changeSummary);

    const req = new HttpRequest('POST', `${this.apiUrl}/${uuid}/versions/`, formData, {
      reportProgress: true
    });
    return this.http.request<DocumentVersion>(req);
  }

  downloadDocument(uuid: string, versionId?: string): Observable<Blob> {
    let url = `${this.apiUrl}/${uuid}/download/`;
    if (versionId) url += `?versionId=${versionId}`;
    return this.http.get(url, { responseType: 'blob' });
  }

  getCategories(): Observable<Category[]> {
    return this.http.get<Category[]>(`${environment.apiUrl}/categories/`);
  }

  getTags(): Observable<Tag[]> {
    return this.http.get<Tag[]>(`${environment.apiUrl}/tags/`);
  }

  getRecentDocuments(limit: number = 10): Observable<Document[]> {
    return this.http.get<any>(`${this.apiUrl}/recent/`, {
      params: new HttpParams().set('limit', limit.toString())
    }).pipe(map(res => (res.data || []).map(this.mapDocument)));
  }

  getStats(): Observable<{ totalDocuments: number; recentUploads: number; aiSummaries: number; storageUsed: number }> {
    return this.http.get<any>(`${this.apiUrl}/stats/`).pipe(map(res => res.data));
  }

  private mapDocument = (data: any): Document => {
    // Map metadata array to a key-value dictionary
    const mappedMetadata: any = {};
    if (Array.isArray(data.metadata)) {
      data.metadata.forEach((item: any) => {
        mappedMetadata[item.key] = item.value;
      });
    } else if (data.metadata) {
      Object.assign(mappedMetadata, data.metadata);
    }

    // Map versions array to frontend camelCase format
    const mappedVersions = Array.isArray(data.versions) ? data.versions.map((v: any) => ({
      id: v.id,
      versionNumber: v.version_number || v.versionNumber,
      fileName: v.file ? v.file.split('/').pop() : 'unknown',
      fileSize: v.file_size || v.fileSize,
      changeSummary: v.change_note || v.changeSummary || '',
      uploadedBy: {
        id: v.uploaded_by,
        name: v.uploaded_by_email ? v.uploaded_by_email.split('@')[0] : 'Unknown'
      },
      createdAt: v.created_at || v.createdAt,
      downloadUrl: v.file || '#'
    })) : data.versions;

    return {
      ...data,
      metadata: mappedMetadata,
      versions: mappedVersions,
      owner: typeof data.owner === 'object' ? data.owner : {
        id: data.owner,
        name: data.owner_name || data.owner_email?.split('@')[0] || 'Unknown',
        email: data.owner_email || ''
      },
      fileName: data.original_filename || data.fileName || 'unknown',
      fileType: data.file_type || data.fileType,
      fileSize: data.file_size || data.fileSize,
      mimeType: data.mime_type || data.mimeType,
      aiProcessed: data.ai_status === 'completed' || data.aiProcessed || false,
      ocrCompleted: data.ocr_status === 'completed' || data.ocrCompleted || false,
      createdAt: data.created_at || data.createdAt,
      updatedAt: data.updated_at || data.updatedAt,
    };
  };
}
