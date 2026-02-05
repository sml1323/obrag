import type { ProjectRead, ProjectUpdate } from '@/lib/types/project';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function createProject(data: {
  name: string;
  vaultPath: string;
  description?: string;
}): Promise<ProjectRead> {
  const response = await fetch('/api/projects', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name: data.name,
      vaultPath: data.vaultPath,
      description: data.description,
    }),
  });

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to create project',
    );
  }

  return json;
}

export async function listProjects(): Promise<ProjectRead[]> {
  const response = await fetch('/api/projects');

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to list projects',
    );
  }

  return json;
}

export async function getProject(id: number): Promise<ProjectRead> {
  const response = await fetch(`/api/projects/${id}`);

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Project not found',
    );
  }

  return json;
}

export async function updateProject(
  id: number,
  data: ProjectUpdate,
): Promise<ProjectRead> {
  const response = await fetch(`/api/projects/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to update project',
    );
  }

  return json;
}

export async function deleteProject(id: number): Promise<{ ok: boolean }> {
  const response = await fetch(`/api/projects/${id}`, {
    method: 'DELETE',
  });

  const json = await response.json();

  if (!response.ok) {
    throw new ApiError(
      response.status,
      json.detail || json.error || 'Failed to delete project',
    );
  }

  return json;
}

export async function getProjectByPath(vaultPath: string): Promise<ProjectRead | null> {
  const projects = await listProjects();
  return projects.find(p => p.path === vaultPath) || null;
}
