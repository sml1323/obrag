"use client"

import { useCallback, useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Character } from "@/components/character"
import { FolderTree } from "@/components/folder-tree"
import { getVaultTree } from "@/lib/api/vault"
import type { TreeNode } from "@/lib/types/vault"
import { AlertCircle, RotateCcw } from "lucide-react"

interface EmbeddingScopeModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectId?: number;
  scope?: string[];
  onScopeChange: (selectedPaths: string[]) => void;
}

const STORAGE_KEY = "obsidian-ai-embedding-scope";
const PATHS_STORAGE_KEY = "obsidian-ai-embedding-paths";

const filterFolders = (nodes: TreeNode[]): TreeNode[] => {
  return nodes
    .filter(node => node.is_dir)
    .map(node => ({
      ...node,
      children: node.children ? filterFolders(node.children) : []
    }));
};

export function EmbeddingScopeModal({
  open,
  onOpenChange,
  projectId,
  scope: _scope,
  onScopeChange
}: EmbeddingScopeModalProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [treeData, setTreeData] = useState<TreeNode[]>([]);
  const [checkedPaths, setCheckedPaths] = useState<Record<string, boolean>>({});

  const loadTree = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getVaultTree(projectId);
      const foldersOnly = filterFolders(data.nodes);
      setTreeData(foldersOnly);
      
      if (typeof window !== 'undefined') {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved) {
          try {
            setCheckedPaths(JSON.parse(saved));
          } catch (e) {
            console.error(e);
            setCheckedPaths({});
          }
        } else {
          setCheckedPaths({});
        }
      }
    } catch (err) {
      console.error(err);
      setError("Failed to load folder structure");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    if (open) {
      loadTree();
    }
  }, [open, loadTree]);

  const getAllPaths = (nodes: TreeNode[]): string[] => {
    let paths: string[] = [];
    for (const node of nodes) {
      paths.push(node.path);
      if (node.children) {
        paths = [...paths, ...getAllPaths(node.children)];
      }
    }
    return paths;
  };

  const handleSave = () => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(checkedPaths));
    
    const allPaths = getAllPaths(treeData);
    const selected = allPaths.filter(path => checkedPaths[path] ?? true);
    
    localStorage.setItem(PATHS_STORAGE_KEY, JSON.stringify(selected));
    
    onScopeChange(selected);
    onOpenChange(false);
  };

  const handleToggle = (path: string, checked: boolean) => {
    setCheckedPaths(prev => ({
      ...prev,
      [path]: checked
    }));
  };

  const handleToggleAll = (checked: boolean) => {
    if (checked) {
      setCheckedPaths({});
    } else {
      const allPaths = getAllPaths(treeData);
      const newPaths: Record<string, boolean> = {};
      allPaths.forEach(p => newPaths[p] = false);
      setCheckedPaths(newPaths);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px] h-[80vh] flex flex-col p-0 gap-0 overflow-hidden outline-none">
        <DialogHeader className="p-6 pb-2">
          <DialogTitle>Select Embedding Scope</DialogTitle>
        </DialogHeader>
        
        <div className="flex-1 overflow-hidden p-6 pt-2">
          {loading ? (
             <div className="h-full flex flex-col items-center justify-center">
               <Character mood="loading" size="lg" message="Loading folders..." />
             </div>
          ) : error ? (
            <div className="h-full flex flex-col items-center justify-center gap-4 text-destructive">
               <AlertCircle className="h-8 w-8" />
               <p className="font-medium">{error}</p>
               <Button onClick={loadTree} variant="outline" className="gap-2">
                 <RotateCcw className="h-4 w-4" /> Try Again
               </Button>
            </div>
          ) : (
            <FolderTree 
              nodes={treeData} 
              checkedPaths={checkedPaths} 
              onToggle={handleToggle}
              onToggleAll={handleToggleAll}
            />
          )}
        </div>

        <DialogFooter className="p-6 pt-2 border-t bg-background">
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={handleSave}>Save Scope</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
