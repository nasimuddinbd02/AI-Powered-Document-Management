import { Component, inject, ViewChild, ElementRef, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterModule } from '@angular/router';
import { MatIconModule } from '@angular/material/icon';
import { AIService } from '../../core/services/ai.service';
import { ChatMessage, ChatResponse, SourceReference } from '../../core/models/ai.model';

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
  private shouldScroll = false;

  suggestedQuestions = [
    'Summarize the Q4 Financial Report',
    'What are the key milestones in the Product Roadmap?',
    'Compare revenue growth across quarters',
    'Find all documents related to marketing strategy',
    'What are the main topics in the Employee Handbook?',
  ];

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
  }

  sendMessage(content?: string): void {
    const message = content || this.currentMessage.trim();
    if (!message) return;

    // Add user message
    const userMsg: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };
    this.messages.push(userMsg);
    this.currentMessage = '';
    this.isTyping = true;
    this.shouldScroll = true;

    // Send to API
    this.aiService.sendChatMessage({
      message,
      conversationId: this.conversationId
    }).subscribe({
      next: (response: ChatResponse) => {
        this.addAssistantMessage(response.message, response.sources);
        this.conversationId = response.conversationId;
      },
      error: () => {
        // Demo mock response
        setTimeout(() => {
          this.addAssistantMessage(this.getMockResponse(message), this.getMockSources());
        }, 1500);
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
      .replace(/- /g, '• ');
  }

  private getMockResponse(question: string): string {
    const responses: Record<string, string> = {
      default: `Based on my analysis of your documents, here's what I found:\n\n**Key Findings:**\n\n1. **Revenue Growth**: The Q4 2024 report shows a 15% increase in revenue compared to Q3, driven primarily by the new product launch in October.\n\n2. **Cost Optimization**: Operating costs were reduced by 8% through process automation and vendor renegotiation.\n\n3. **Market Expansion**: Three new geographic markets were entered, contributing 12% of total revenue.\n\n**Recommendations:**\n- Continue investment in product R&D\n- Expand the automated marketing pipeline\n- Monitor cost efficiency ratios quarterly\n\nWould you like me to dive deeper into any of these areas?`
    };
    return responses['default'];
  }

  private getMockSources(): SourceReference[] {
    return [
      { documentId: '1', documentTitle: 'Q4 Financial Report 2024', excerpt: 'Revenue grew 15% quarter over quarter...', relevanceScore: 0.94, pageNumber: 12 },
      { documentId: '2', documentTitle: 'Product Roadmap 2025', excerpt: 'October launch contributed significantly...', relevanceScore: 0.87, pageNumber: 4 },
      { documentId: '5', documentTitle: 'Budget Analysis 2024', excerpt: 'Cost reduction initiatives achieved 8% savings...', relevanceScore: 0.79, pageNumber: 8 },
    ];
  }
}
