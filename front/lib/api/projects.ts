import type { ProjectRead, ProjectUpdate } from '@/lib/types/project';
import { request } from './client';

export async function createProject(data: {
  name: string;
  vaultPath: string;
  description?: string;
}): Promise<ProjectRead> {
  return request<ProjectRead>('/projects', {
    method: 'POST',
    body: JSON.stringify({
      name: data.name,
      vaultPath: data.vaultPath,
      description: data.description,
    }),
  });
}

export async function listProjects(): Promise<ProjectRead[]> {
  return request<ProjectRead[]>('/projects');
}

export async function getProject(id: number): Promise<ProjectRead> {
  return request<ProjectRead>(`/projects/${id}`);
}

export async function updateProject(
  id: number,
  data: ProjectUpdate,
): Promise<ProjectRead> {
  return request<ProjectRead>(`/projects/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: number): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/projects/${id}`, {
    method: 'DELETE',
  });
}

export async function getProjectByPath(vaultPath: string): Promise<ProjectRead | null> {
  const projects = await listProjects();
  return projects.find(p => p.path === vaultPath) || null;
}
