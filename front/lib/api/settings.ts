export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export interface Settings {
  id: number;
  vault_path: string | null;
  para_root_path: string | null;
  llm_provider: string;
  llm_model: string;
  embedding_provider: string;
  embedding_model: string;
  llm_api_key: string | null;  // Will be masked from backend
  embedding_api_key: string | null;  // Will be masked from backend
  ollama_endpoint: string;
  created_at: string;
  updated_at: string;
}

export interface SettingsUpdate {
  vault_path?: string;
  para_root_path?: string;
  llm_provider?: string;
  llm_model?: string;
  embedding_provider?: string;
  embedding_model?: string;
  llm_api_key?: string;  // Full key when updating
  embedding_api_key?: string;  // Full key when updating
  ollama_endpoint?: string;
}

export async function getSettings(): Promise<Settings> {
  const response = await fetch('/api/settings');

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to get settings',
    );
  }

  return json;
}

export async function updateSettings(data: SettingsUpdate): Promise<Settings> {
  const response = await fetch('/api/settings', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to update settings',
    );
  }

  return json;
}
