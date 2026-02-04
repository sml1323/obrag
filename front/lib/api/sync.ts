import { ApiError } from './projects';

export interface SyncResult {
  added: number;
  modified: number;
  deleted: number;
  skipped: number;
  total_chunks: number;
  errors: string[];
}

export interface TriggerSyncOptions {
  projectId?: number;
  embeddingApiKey?: string;
  includePaths?: string[];
}

export async function triggerSync(options: TriggerSyncOptions = {}): Promise<SyncResult> {
  const { projectId, embeddingApiKey, includePaths } = options;
  const url = projectId ? `/api/sync/trigger?project_id=${projectId}` : '/api/sync/trigger';
  
  const body: Record<string, unknown> = {};
  if (embeddingApiKey) {
    body.embedding_api_key = embeddingApiKey;
  }
  if (includePaths && includePaths.length > 0) {
    body.include_paths = includePaths;
  }
  
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to trigger sync',
    );
  }

  return json;
}
