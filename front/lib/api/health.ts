import { BACKEND_URL } from "./client";

export interface HealthResponse {
  status: string;
}

export async function checkHealth(): Promise<HealthResponse> {
  const res = await fetch(`${BACKEND_URL}/health`, {
    method: "GET",
    signal: AbortSignal.timeout(5000),
  });
  if (!res.ok) throw new Error(`Health check failed: ${res.status}`);
  return res.json();
}
