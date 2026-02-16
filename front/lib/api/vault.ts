import { request } from "./client";
import { TreeResponse, DocumentResponse } from "../types/vault";

export async function getVaultTree(projectId?: number): Promise<TreeResponse> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return request<TreeResponse>(`/vault/tree${query}`);
}

export async function getDocumentContent(
  source: string,
  relativePath?: string,
): Promise<DocumentResponse> {
  const params = new URLSearchParams({ source });
  if (relativePath) {
    params.set("relative_path", relativePath);
  }
  return request<DocumentResponse>(`/vault/document?${params.toString()}`);
}
