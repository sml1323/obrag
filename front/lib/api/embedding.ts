import { request } from "./client";
import type {
  EmbeddingModelListResponse,
  EmbeddingModelStatus,
  EmbeddingModelDownloadResponse,
  EmbeddingModelClearResponse,
  CollectionListResponse,
  VectorVisualizationResponse,
} from "../types/embedding";

export async function listEmbeddingModels(): Promise<EmbeddingModelListResponse> {
  return request<EmbeddingModelListResponse>("/embedding/models");
}

export async function getEmbeddingModelStatus(
  modelId: string,
): Promise<EmbeddingModelStatus> {
  const encoded = encodeURIComponent(modelId);
  return request<EmbeddingModelStatus>(
    `/embedding/models/${encoded}/status`,
  );
}

export async function downloadEmbeddingModel(
  modelId: string,
): Promise<EmbeddingModelDownloadResponse> {
  return request<EmbeddingModelDownloadResponse>("/embedding/models/download", {
    method: "POST",
    body: JSON.stringify({ model_id: modelId }),
  });
}

export async function clearEmbeddingDownloadState(
  modelId: string,
): Promise<EmbeddingModelClearResponse> {
  const encoded = encodeURIComponent(modelId);
  return request<EmbeddingModelClearResponse>(
    `/embedding/models/${encoded}/download-state`,
    {
      method: "DELETE",
    },
  );
}

export async function listCollections(): Promise<CollectionListResponse> {
  return request<CollectionListResponse>("/embedding/collections");
}

export async function getCollectionVectors(
  collectionName: string,
  limit: number = 500,
  perplexity: number = 30,
  dimensions: number = 3,
): Promise<VectorVisualizationResponse> {
  const encoded = encodeURIComponent(collectionName);
  return request<VectorVisualizationResponse>(
    `/embedding/collections/${encoded}/vectors?limit=${limit}&perplexity=${perplexity}&dimensions=${dimensions}`,
  );
}
