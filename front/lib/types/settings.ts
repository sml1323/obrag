export interface SettingsResponse {
  id: number;
  vault_path: string | null;
  para_root_path: string | null;
  llm_provider: string;
  llm_model: string;
  llm_api_key: string | null;
  embedding_provider: string;
  embedding_model: string;
  embedding_api_key: string | null;
  ollama_endpoint: string;
  created_at: string;
  updated_at: string;
}

export interface SettingsUpdate {
  vault_path?: string;
  para_root_path?: string;
  llm_provider?: string;
  llm_model?: string;
  llm_api_key?: string;
  embedding_provider?: string;
  embedding_model?: string;
  embedding_api_key?: string;
  ollama_endpoint?: string;
}
