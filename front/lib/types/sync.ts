export interface SyncResult {
  added: number;
  modified: number;
  deleted: number;
  skipped: number;
  total_chunks: number;
  errors: string[];
}
