export interface Document {
  uuid: string;
  title: string;
  description?: string;
  fileName: string;
  fileType: string;
  fileSize: number;
  mimeType: string;
  storagePath: string;
  thumbnailUrl?: string;
  category?: Category;
  tags: Tag[];
  metadata: DocumentMetadata;
  accessLevel: 'private' | 'department' | 'public';
  owner: { id: string; name: string; email: string; avatar?: string };
  versions: DocumentVersion[];
  aiSummary?: string;
  ocrCompleted: boolean;
  aiProcessed: boolean;
  downloadCount: number;
  createdAt: string;
  updatedAt: string;
}

export interface DocumentVersion {
  id: string;
  versionNumber: number;
  fileName: string;
  fileSize: number;
  changeSummary?: string;
  uploadedBy: { id: string; name: string; avatar?: string };
  createdAt: string;
  downloadUrl: string;
}

export interface DocumentMetadata {
  [key: string]: string | number | boolean;
}

export interface Tag {
  id: string;
  name: string;
  color?: string;
}

export interface Category {
  id: string;
  name: string;
  description?: string;
  icon?: string;
  documentCount?: number;
}

export interface DocumentAccess {
  id: string;
  documentId: string;
  userId: string;
  userName: string;
  permission: 'view' | 'edit' | 'admin';
  grantedAt: string;
  grantedBy: string;
}

export interface DocumentUploadRequest {
  file: File;
  title: string;
  description?: string;
  tags?: string[];
  categoryId?: string;
  accessLevel: 'private' | 'department' | 'public';
  metadata?: DocumentMetadata;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface DocumentFilter {
  search?: string;
  category?: string;
  tags?: string[];
  fileType?: string;
  accessLevel?: string;
  dateFrom?: string;
  dateTo?: string;
  sortBy?: string;
  sortOrder?: 'asc' | 'desc';
  page?: number;
  pageSize?: number;
}
