/**
 * TypeScript Interfaces mapping directly to the FastAPI backend schemas.
 * (Source of truth: src/api/schemas.py)
 */

export interface HealthResponse {
  status: string;
  ollama_reachable: boolean;
  ollama_host: string;
}

export interface ModelsResponse {
  models: string[];
  count: number;
}

export interface ChatRequest {
  message: string;
  model?: string;
  session_id?: string;
}

export interface ChatResponse {
  session_id: string;
  model: string;
  response: string;
  latency_seconds: number;
}

export interface ClearHistoryResponse {
  cleared: boolean;
  session_id?: string | null;
  message: string;
}

export interface MetricsResponse {
  system: {
    os: string;
    os_release: string;
    architecture: string;
    cpu_count_logical: number;
    cpu_count_physical: number;
    total_ram_gb: number;
    available_ram_gb: number;
  };
  ollama_rss_mb?: number | null;
}


export interface DocumentUploadResponse {
  session_id: string;
  model: string;
  response: string;
  latency_seconds: number;
  filename: string;
  file_size_bytes: number;
  extracted_characters: number;
}
