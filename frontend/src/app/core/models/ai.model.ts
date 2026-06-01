export interface AISummary {
  id: string;
  documentId: string;
  summary: string;
  keyTopics: string[];
  entities: Entity[];
  sentiment?: string;
  language?: string;
  wordCount: number;
  readingTime: number;
  generatedAt: string;
}

export interface Entity {
  name: string;
  type: 'person' | 'organization' | 'location' | 'date' | 'concept' | 'other';
  relevance: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  sources?: SourceReference[];
  isLoading?: boolean;
}

export interface ChatRequest {
  message: string;
  documentId?: string;
  conversationId?: string;
  context?: string;
}

export interface ChatResponse {
  id: string;
  message: string;
  sources: SourceReference[];
  conversationId: string;
  tokensUsed: number;
}

export interface SourceReference {
  documentId: string;
  documentTitle: string;
  excerpt: string;
  relevanceScore: number;
  pageNumber?: number;
}

export interface SearchResult {
  documentId: string;
  document: {
    uuid: string;
    title: string;
    fileName: string;
    fileType: string;
    owner: { name: string; avatar?: string };
    createdAt: string;
  };
  score: number;
  highlights: string[];
  matchedContent: string;
}

export interface SearchRequest {
  query: string;
  mode: 'fulltext' | 'semantic' | 'hybrid';
  filters?: {
    fileType?: string[];
    tags?: string[];
    dateFrom?: string;
    dateTo?: string;
    author?: string;
  };
  page?: number;
  pageSize?: number;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  mode: string;
  processingTime: number;
}
