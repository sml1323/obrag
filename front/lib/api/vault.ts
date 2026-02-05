import { request } from "./client";
import { TreeResponse } from "../types/vault";

export async function getVaultTree(projectId?: number): Promise<TreeResponse> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return request<TreeResponse>(`/vault/tree${query}`);
}
