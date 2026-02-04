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

export type EmbeddingScope = Record<string, boolean>;
