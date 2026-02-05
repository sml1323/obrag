// Match backend src/api/schemas/project.py

export interface ProjectCreate {
  name: string;
  path: string;  // backend uses "path" 
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
  is_active?: boolean;
}

export interface ProjectRead {
  id: number;  // Backend uses integer ID!
  name: string;
  path: string;
  description?: string;
  is_active: boolean;
  last_modified_at: string;  // ISO datetime string
  created_at: string;
  is_stale: boolean;
  days_inactive: number;
}

// Extended frontend Project (compatible with existing project-manager.tsx)
export interface Project {
  id: string;  // Frontend uses UUID string
  name: string;
  vaultPath: string;  // Frontend uses "vaultPath" (mapped from path)
  createdAt: Date;
  lastIndexed?: Date;
  fileCount?: number;
  backendId?: number;  // Link to backend project
}
