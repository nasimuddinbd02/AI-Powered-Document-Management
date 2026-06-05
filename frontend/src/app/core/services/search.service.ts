import { Injectable } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { SearchRequest, SearchResponse, SearchResult } from '../models/ai.model';

@Injectable({ providedIn: 'root' })
export class SearchService {
  private readonly apiUrl = `${environment.apiUrl}/search`;

  constructor(private http: HttpClient) {}

  search(request: SearchRequest): Observable<SearchResponse> {
    const payload = {
      query: request.query,
      search_type: request.mode || 'fulltext',
      limit: request.pageSize || 20,
      ...request.filters
    };
    return this.http.post<any>(`${this.apiUrl}/`, payload).pipe(
      map(res => {
        const rawResults = res.data?.results || [];
        const mappedResults: SearchResult[] = rawResults.map((item: any) => {
          // Check if it is a semantic search result from the backend
          const isSemantic = item.document_uuid !== undefined;
          
          if (isSemantic) {
            return {
              documentId: item.document_uuid,
              score: item.score ? (item.score > 1.0 ? 1.0 : item.score) : 1.0,
              highlights: item.chunk_text ? [item.chunk_text] : [],
              matchedContent: item.chunk_text || '',
              document: {
                uuid: item.document_uuid,
                id: item.document_id,
                title: item.document_title,
                fileName: 'Semantic_Result',
                fileType: 'txt',
                fileSize: 0,
                mimeType: 'text/plain',
                aiProcessed: true,
                ocrCompleted: false,
                owner: {
                  id: '',
                  name: item.owner_name || item.owner_email?.split('@')[0] || 'Unknown',
                  email: item.owner_email || ''
                },
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString(),
              }
            };
          }

          // Otherwise it is fulltext / hybrid which returns Document objects
          return {
            documentId: item.uuid || item.id,
            score: item.score ? (item.score > 1.0 ? 1.0 : item.score) : 1.0,
            highlights: item.highlights || [],
            matchedContent: item.matched_content || item.description || '',
            document: {
              ...item,
              owner: typeof item.owner === 'object' ? item.owner : {
                id: item.owner,
                name: item.owner_name || item.owner_email?.split('@')[0] || 'Unknown',
                email: item.owner_email || ''
              },
              fileName: item.original_filename || item.fileName || 'unknown',
              fileType: item.file_type || item.fileType,
              fileSize: item.file_size || item.fileSize,
              mimeType: item.mime_type || item.mimeType,
              aiProcessed: item.ai_status === 'completed' || item.aiProcessed || false,
              ocrCompleted: item.ocr_status === 'completed' || item.ocrCompleted || false,
              createdAt: item.created_at || item.createdAt,
              updatedAt: item.updated_at || item.updatedAt,
            }
          };
        });

        return {
          query: request.query,
          mode: request.mode || 'fulltext',
          results: mappedResults,
          total: res.data?.count || mappedResults.length,
          processingTime: 0.1
        };
      })
    );
  }

  fullTextSearch(query: string, page?: number, pageSize?: number): Observable<SearchResponse> {
    return this.search({
      query,
      mode: 'fulltext',
      page,
      pageSize
    });
  }

  semanticSearch(query: string, page?: number, pageSize?: number): Observable<SearchResponse> {
    return this.search({
      query,
      mode: 'semantic',
      page,
      pageSize
    });
  }

  hybridSearch(query: string, filters?: SearchRequest['filters'], page?: number, pageSize?: number): Observable<SearchResponse> {
    return this.search({
      query,
      mode: 'hybrid',
      filters,
      page,
      pageSize
    });
  }

  getSuggestions(query: string): Observable<string[]> {
    return this.http.get<string[]>(`${this.apiUrl}/suggestions/`, {
      params: new HttpParams().set('q', query)
    });
  }
}
