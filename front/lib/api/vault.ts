import { ApiError } from './projects';
import type { TreeResponse } from '@/lib/types/vault';

export async function getVaultTree(projectId?: number): Promise<TreeResponse> {
  const url = projectId 
    ? `/api/vault/tree?project_id=${projectId}` 
    : '/api/vault/tree';
  
  const response = await fetch(url);
  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to get vault tree',
    );
  }

  return json;
}
