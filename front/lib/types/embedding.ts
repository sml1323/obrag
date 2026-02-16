export type EmbeddingModelStatusValue = "not_found" | "downloading" | "ready" | "error";

export interface EmbeddingModelStatus {
  model_id: string;
  status: EmbeddingModelStatusValue;
  progress: number;
  size_mb?: number;
  error?: string | null;
  local_path?: string | null;
}

export interface EmbeddingModelListItem {
  model_id: string;
  size_mb?: number;
  dimension?: number;
  status: string;
  is_cached: boolean;
}

export interface EmbeddingModelListResponse {
  models: EmbeddingModelListItem[];
}

export interface EmbeddingModelDownloadResponse {
  model_id: string;
  status: string;
  message: string;
}

export interface EmbeddingModelClearResponse {
  status: string;
  model_id: string;
}

export interface CollectionInfo {
  name: string;
  count: number;
  model_name: string | null;
}

export interface CollectionListResponse {
  collections: CollectionInfo[];
}

export interface VectorPoint {
  id: string;
  x: number;
  y: number;
  z: number | null;
  text: string;
  source: string | null;
  metadata: Record<string, unknown>;
}

export interface VectorVisualizationResponse {
  collection_name: string;
  total_count: number;
  points: VectorPoint[];
  categories: string[];
  dimensions: number;
}
