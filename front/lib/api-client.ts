const API_BASE = "http://localhost:8000"; // Assuming backend is on port 8000

export interface Project {
  id: number;
  name: string;
  path: string;
  description?: string;
  is_active: boolean;
  last_modified_at: string;
  created_at: string;
  progress: number;
  file_count: number;
  is_stale: boolean;
  days_inactive: number;
}

export async function getProjects(activeOnly: boolean = true): Promise<Project[]> {
  const params = new URLSearchParams({ active_only: String(activeOnly) });
  const res = await fetch(`${API_BASE}/projects/?${params}`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function updateProjectProgress(
  id: number,
  progress: number,
): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ progress }),
  });
  if (!res.ok) throw new Error("Failed to update project progress");
  return res.json();
}
