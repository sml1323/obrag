export interface SourceChunk {
  content: string;
  source: string;
  score: number;
}

export interface ChatRequest {
  question: string;
  session_id?: string;
  top_k?: number;
  temperature?: number;
  max_tokens?: number;
  llm_provider?: string;
  llm_model?: string;
  api_key?: string;
}

export interface ChatResponse {
  answer: string;
  sources: SourceChunk[];
  model: string;
  usage: any;
}

export type SSEEvent =
  | { type: "start"; sources: SourceChunk[]; model: string }
  | { type: "content"; content: string }
  | { type: "done" };
