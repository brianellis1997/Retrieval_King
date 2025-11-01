import axios, { AxiosInstance } from 'axios';

interface Document {
  id: string;
  filename: string;
  file_type: string;
  file_size: number;
  upload_time: string;
  num_chunks: number;
  num_pages?: number;
}

interface Citation {
  citation_id: number;
  document_id: string;
  filename: string;
  chunk_id: string;
  text: string;
  page_number?: number;
  confidence_score: number;
}

interface QueryResponse {
  query_id: string;
  query: string;
  response: string;
  citations: Citation[];
  num_contexts_retrieved: number;
  num_contexts_used: number;
  processing_time_ms: number;
}

class APIService {
  private api: AxiosInstance;

  constructor(baseURL: string = 'http://localhost:8000') {
    this.api = axios.create({
      baseURL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
  }

  async uploadDocument(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.api.post('/api/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  async listDocuments(): Promise<Document[]> {
    const response = await this.api.get('/api/documents');
    return response.data.documents;
  }

  async deleteDocument(documentId: string): Promise<any> {
    const response = await this.api.delete(`/api/documents/${documentId}`);
    return response.data;
  }

  async query(query: string, topK: number = 10, useReranker: boolean = true): Promise<QueryResponse> {
    const response = await this.api.post('/api/query', {
      query,
      top_k: topK,
      use_reranker: useReranker,
      stream: false,
    });

    return response.data;
  }

  async queryStream(
    query: string,
    topK: number = 10,
    useReranker: boolean = true,
    onChunk: (chunk: string) => void
  ): Promise<void> {
    const response = await this.api.post('/api/query/stream', {
      query,
      top_k: topK,
      use_reranker: useReranker,
    }, {
      responseType: 'stream',
    });

    const reader = response.data;
    let buffer = '';

    reader.on('data', (chunk: Buffer) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6);
          try {
            const parsed = JSON.parse(data);
            if (parsed.content) {
              onChunk(parsed.content);
            }
          } catch (e) {
            console.error('Failed to parse stream data:', e);
          }
        }
      }
    });

    return new Promise((resolve, reject) => {
      reader.on('end', resolve);
      reader.on('error', reject);
    });
  }

  async healthCheck(): Promise<any> {
    const response = await this.api.get('/health');
    return response.data;
  }
}

export const apiService = new APIService();
export type { Document, Citation, QueryResponse };
