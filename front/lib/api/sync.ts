import { request } from "./client";
import { SyncResult, SyncTriggerBody, SyncTriggerOptions } from "../types/vault";

export async function triggerSync(
  options: SyncTriggerOptions = {},
): Promise<SyncResult> {
  const { body = {}, projectId, forceReindex } = options;
  
  const params = new URLSearchParams();
  if (projectId !== undefined) {
    params.set("project_id", String(projectId));
  }
  if (forceReindex) {
    params.set("force_reindex", "true");
  }
  
  const query = params.toString() ? `?${params.toString()}` : "";
  return request<SyncResult>(`/sync/trigger${query}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
