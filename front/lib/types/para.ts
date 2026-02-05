export interface ParaFileRead {
  id: string;
  name: string;
  relative_path: string;
  last_modified_at: string;
}

export interface ParaProjectRead {
  id: string;
  name: string;
  path: string;
  file_count: number;
  last_modified_at: string | null;
  files: ParaFileRead[];
}
