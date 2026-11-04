import {
  HealthResponse,
  ModelsResponse,
  ChatRequest,
  ChatResponse,
  ClearHistoryResponse,
  MetricsResponse,
  DocumentUploadResponse,
} from '../types/api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        ...(options.headers || {}),
      },
    });

    if (!res.ok) {
      let errorDetail = `Request failed with status ${res.status}`;
      try {
        const errorJson = await res.json();
        if (errorJson.detail) {
          errorDetail = typeof errorJson.detail === 'string'
            ? errorJson.detail
            : JSON.stringify(errorJson.detail);
        }
      } catch {
        errorDetail = res.statusText || errorDetail;
      }
      throw new ApiError(errorDetail, res.status);
    }

    return await res.json();
  } catch (err: any) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(
      `Unable to reach backend at ${API_BASE_URL}. Ensure the FastAPI server is running.`,
      0
    );
  }
}

export const api = {
  /**
   * Check backend health and local Ollama connectivity.
   */
  async getHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  /**
   * Fetch installed Ollama models.
   */
  async getModels(): Promise<ModelsResponse> {
    return request<ModelsResponse>('/models');
  },

  /**
   * Send a chat prompt and receive model inference response.
   */
  async sendChat(payload: ChatRequest): Promise<ChatResponse> {
    return request<ChatResponse>('/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    });
  },

  /**
   * Upload a document (PDF, TXT, DOCX) and receive model inference response.
   */
  async uploadChat(formData: FormData): Promise<DocumentUploadResponse> {
    return request<DocumentUploadResponse>('/chat/upload', {
      method: 'POST',
      body: formData,
    });
  },

  /**
   * Clear in-memory conversation history.
   * If sessionId is provided, clears only that session.
   */
  async clearHistory(sessionId?: string): Promise<ClearHistoryResponse> {
    const query = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    return request<ClearHistoryResponse>(`/chat/history${query}`, {
      method: 'DELETE',
    });
  },

  /**
   * Retrieve hardware and Ollama daemon process memory metrics.
   */
  async getMetrics(): Promise<MetricsResponse> {
    return request<MetricsResponse>('/metrics');
  },
};
