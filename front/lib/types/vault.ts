export interface TreeNode {
  path: string;
  name: string;
  is_dir: boolean;
  children: TreeNode[];
}

export interface TreeResponse {
  root: string;
  nodes: TreeNode[];
}

export interface SyncResult {
  added: number;
  modified: number;
  deleted: number;
  skipped: number;
  total_chunks: number;
  errors: string[];
}

export interface SyncTriggerBody {
  embedding_api_key?: string;
  include_paths?: string[];
}
