import { Component, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AIService } from '../../core/services/ai.service';
import { ChatMessage, ChatResponse, SourceReference } from '../../core/models/ai.model';

interface ConversationEntry {
  role: 'user' | 'assistant';
  content: string;
}

@Component({
  selector: 'app-ai-assistant',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterModule, MatIconModule],
  templateUrl: './ai-assistant.component.html',
  styleUrls: ['./ai-assistant.component.css']
})
export class AIAssistantComponent implements AfterViewChecked {
  @ViewChild('chatContainer') chatContainer!: ElementRef;
  @ViewChild('messageInput') messageInput!: ElementRef;

  private aiService = inject(AIService);

  messages: ChatMessage[] = [];
  currentMessage = '';
  isTyping = false;
  conversationId: string | undefined;
  errorMessage = '';
  private shouldScroll = false;
  private chatHistory: ConversationEntry[] = [];

  suggestedQuestions = [
    'What documents do I have uploaded?',
    'Summarize my most recent document',
    'What are the key topics across my documents?',
    'Find information about my resume',
    'What skills or experience are mentioned in my documents?',
  ];

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  sendMessage(content?: string): void {
    const message = content || this.currentMessage.trim();
    if (!message || this.isTyping) return;

    // Add user message to UI
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    this.messages.push(userMsg);
    this.currentMessage = '';
    this.isTyping = true;
    this.errorMessage = '';
    this.shouldScroll = true;

    // Track conversation history for multi-turn context
    this.chatHistory.push({ role: 'user', content: message });

    // Send to real backend API
    this.aiService.sendChatMessage({
      message,
      conversationId: this.conversationId
    }).subscribe({
      next: (response: ChatResponse) => {
        this.addAssistantMessage(response.message, response.sources);
        this.conversationId = response.conversationId;
        this.chatHistory.push({ role: 'assistant', content: response.message });
      },
      error: (err) => {
        console.error('AI Chat Error:', err);
        const errorText = err.error?.error || err.error?.message ||
          'Sorry, I encountered an error connecting to the AI service. Please check that the backend is running and the OpenAI API key is configured.';
        this.addAssistantMessage(errorText);
        this.errorMessage = 'AI service error — check console for details.';
      }
    });
  }

  private addAssistantMessage(content: string, sources?: SourceReference[]): void {
    const msg: ChatMessage = {
      id: Date.now().toString(),
      role: 'assistant',
      content,
      timestamp: new Date().toISOString(),
      sources
    };
    this.messages.push(msg);
    this.isTyping = false;
    this.shouldScroll = true;
  }

  clearChat(): void {
    this.messages = [];
    this.conversationId = undefined;
    this.chatHistory = [];
    this.errorMessage = '';
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  private scrollToBottom(): void {
    try {
      const el = this.chatContainer?.nativeElement;
      if (el) el.scrollTop = el.scrollHeight;
    } catch {}
  }

  formatMessage(content: string): string {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>')
      .replace(/^- /gm, '• ')
      .replace(/^\d+\.\s/gm, (match) => `<span class="list-number">${match}</span>`);
  }
}
