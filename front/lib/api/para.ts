import { request } from "./client";
import { ParaProjectRead } from "../types/para";

export async function listParaProjects(): Promise<ParaProjectRead[]> {
  return request<ParaProjectRead[]>("/para/projects");
}
