import { request } from "./client";
import { SyncResult, SyncTriggerBody } from "../types/vault";

export async function triggerSync(
  body: SyncTriggerBody = {},
  projectId?: number,
): Promise<SyncResult> {
  const query = projectId ? `?project_id=${projectId}` : "";
  return request<SyncResult>(`/sync/trigger${query}`, {
    method: "POST",
    body: JSON.stringify(body),
  });
}
