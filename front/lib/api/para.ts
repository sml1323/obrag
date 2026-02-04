import type { ParaProjectRead } from "@/lib/types/para";
import { ApiError } from "./projects";

export async function listParaProjects(): Promise<ParaProjectRead[]> {
  const response = await fetch("/api/para/projects");
  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || "Failed to list PARA projects",
    );
  }

  return json;
}
