import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AISummary, ChatMessage, ChatRequest, ChatResponse } from '../models/ai.model';

@Injectable({ providedIn: 'root' })
export class AIService {
  private readonly apiUrl = `${environment.apiUrl}/ai`;

  constructor(private http: HttpClient) {}

  summarizeDocument(documentUuid: string): Observable<AISummary> {
    return this.http.post<AISummary>(`${this.apiUrl}/summarize/${documentUuid}/`, {});
  }

  getSummary(documentUuid: string): Observable<AISummary> {
    return this.http.get<AISummary>(`${this.apiUrl}/summaries/`, {
      params: { document__uuid: documentUuid }
    });
  }

  askQuestion(question: string, documentId?: string): Observable<ChatResponse> {
    const payload: any = { question };
    if (documentId) {
      payload.document_ids = [documentId];
    }
    return this.http.post<any>(`${this.apiUrl}/ask/`, payload).pipe(
      map(res => ({
        id: res.id || Date.now().toString(),
        message: res.answer || res.message || '',
        sources: (res.sources || []).map((s: any) => ({
          documentId: s.documentId || s.document_uuid || s.document_id || '',
          documentTitle: s.documentTitle || s.document_title || '',
          excerpt: s.excerpt || '',
          relevanceScore: s.relevanceScore || s.relevance_score || 0,
          pageNumber: s.pageNumber || s.page_number,
        })),
        conversationId: res.conversationId || res.conversation_id || '',
        tokensUsed: res.tokensUsed || res.tokens_used || 0,
      }))
    );
  }

  sendChatMessage(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<any>(`${this.apiUrl}/chat/`, {
      message: request.message,
      conversationId: request.conversationId,
    }).pipe(
      map(res => ({
        id: res.id || Date.now().toString(),
        message: res.message || '',
        sources: (res.sources || []).map((s: any) => ({
          documentId: s.documentId || s.document_uuid || '',
          documentTitle: s.documentTitle || s.document_title || '',
          excerpt: s.excerpt || '',
          relevanceScore: s.relevanceScore || s.relevance_score || 0,
          pageNumber: s.pageNumber || s.page_number,
        })),
        conversationId: res.conversationId || res.conversation_id || '',
        tokensUsed: res.tokensUsed || res.tokens_used || 0,
      }))
    );
  }

  getChatHistory(conversationId?: string): Observable<ChatMessage[]> {
    const url = conversationId
      ? `${this.apiUrl}/chat/history/${conversationId}/`
      : `${this.apiUrl}/chat/history/`;
    return this.http.get<ChatMessage[]>(url);
  }

  getConversations(): Observable<{ id: string; title: string; lastMessage: string; updatedAt: string }[]> {
    return this.http.get<any[]>(`${this.apiUrl}/chat/conversations/`);
  }

  deleteConversation(conversationId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/chat/conversations/${conversationId}/`);
  }
}
