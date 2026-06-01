import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { AISummary, ChatMessage, ChatRequest, ChatResponse } from '../models/ai.model';

@Injectable({ providedIn: 'root' })
export class AIService {
  private readonly apiUrl = `${environment.apiUrl}/ai`;

  constructor(private http: HttpClient) {}

  summarizeDocument(documentId: string): Observable<AISummary> {
    return this.http.post<AISummary>(`${this.apiUrl}/summarize`, { documentId });
  }

  getSummary(documentId: string): Observable<AISummary> {
    return this.http.get<AISummary>(`${this.apiUrl}/summary/${documentId}`);
  }

  askQuestion(question: string, documentId?: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/ask`, { question, documentId });
  }

  sendChatMessage(request: ChatRequest): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${this.apiUrl}/chat`, request);
  }

  getChatHistory(conversationId?: string): Observable<ChatMessage[]> {
    const url = conversationId
      ? `${this.apiUrl}/chat/history/${conversationId}`
      : `${this.apiUrl}/chat/history`;
    return this.http.get<ChatMessage[]>(url);
  }

  getConversations(): Observable<{ id: string; title: string; lastMessage: string; updatedAt: string }[]> {
    return this.http.get<any[]>(`${this.apiUrl}/chat/conversations`);
  }

  deleteConversation(conversationId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/chat/conversations/${conversationId}`);
  }
}
