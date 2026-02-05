"use client";

import { useEffect, useState, useMemo } from "react";
import { getVaultTree } from "@/lib/api/vault";
import { triggerSync } from "@/lib/api/sync";
import { getSettings } from "@/lib/api/settings";
import { TreeNode } from "@/lib/types/vault";
import { SyncResult } from "@/lib/types/sync";
import { FolderTree } from "./folder-tree";
import { Button } from "@/components/ui/button";
import { useLocalStorage } from "@/lib/hooks/use-local-storage";
import { cn } from "@/lib/utils";

function getAllPaths(nodes: TreeNode[]): string[] {
  let paths: string[] = [];
  for (const node of nodes) {
    paths.push(node.path);
    if (node.children) {
      paths = paths.concat(getAllPaths(node.children));
    }
  }
  return paths;
}

export function EmbeddingScope() {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [vaultPath, setVaultPath] = useState<string | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<SyncResult | null>(null);
  
  // Use null to detect first-time load
  const [savedPaths, setSavedPaths] = useLocalStorage<string[] | null>("embedding-scope", null);
  
  const selectedPaths = useMemo(() => {
    return new Set(savedPaths || []);
  }, [savedPaths]);

  useEffect(() => {
    async function init() {
      try {
        const settings = await getSettings();
        if (settings.vault_path) {
          setVaultPath(settings.vault_path);
          // Use global vault scope (project_id=undefined)
          const treeData = await getVaultTree();
          setTree(treeData.nodes);

          // If no paths saved yet, select all by default
          if (savedPaths === null) {
            const allPaths = getAllPaths(treeData.nodes);
            setSavedPaths(allPaths);
          }
        }
      } catch (error) {
        console.error("Failed to load embedding scope data:", error);
      }
    }
    init();
  }, []);

  const handleToggle = (path: string, checked: boolean) => {
    const newSet = new Set(selectedPaths);
    
    // Find the node to check if it's a directory
    const findNode = (nodes: TreeNode[]): TreeNode | null => {
      for (const node of nodes) {
        if (node.path === path) return node;
        if (node.children) {
          const found = findNode(node.children);
          if (found) return found;
        }
      }
      return null;
    };

    const targetNode = findNode(tree);
    
    const updatePath = (p: string, isChecked: boolean) => {
      if (isChecked) newSet.add(p);
      else newSet.delete(p);
    };

    updatePath(path, checked);

    // If directory, toggle all children
    if (targetNode && targetNode.is_dir) {
      const childPaths = getAllPaths(targetNode.children);
      childPaths.forEach(childPath => updatePath(childPath, checked));
    }

    setSavedPaths(Array.from(newSet));
  };

  const handleSync = async () => {
    setIsSyncing(true);
    setSyncResult(null);
    try {
      const result = await triggerSync({ 
        include_paths: Array.from(selectedPaths) 
      });
      setSyncResult(result);
    } catch (error) {
      console.error("Sync failed:", error);
    } finally {
      setIsSyncing(false);
    }
  };

  if (!vaultPath) {
    return (
      <div className="p-8 border-4 border-black shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] bg-white">
        <h2 className="text-xl font-bold mb-4">Configuration Required</h2>
        <p>Please configure your vault path in Settings first.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-black uppercase">Embedding Scope</h2>
          <div className="bg-[#FFE66D] border-2 border-black px-3 py-1 font-bold">
            {selectedPaths.size} Selected
          </div>
        </div>

        <div className="max-h-[500px] overflow-y-auto border-2 border-black p-4 bg-gray-50 mb-6">
          <FolderTree 
            nodes={tree} 
            selectedPaths={selectedPaths} 
            onToggle={handleToggle} 
          />
        </div>

        <div className="flex items-center justify-between">
          <Button 
            onClick={handleSync} 
            disabled={isSyncing || selectedPaths.size === 0}
            className={cn(
              "border-3 border-black font-bold text-lg px-8 py-6 h-auto transition-all",
              isSyncing ? "bg-gray-200" : "bg-[#FF6B35] hover:bg-[#FF8C60] hover:-translate-y-1 hover:shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]"
            )}
          >
            {isSyncing ? "Running Embedding..." : "RUN EMBEDDING"}
          </Button>

          {isSyncing && (
             <div className="w-1/2 h-6 border-2 border-black bg-white relative overflow-hidden">
               <div className="absolute top-0 left-0 h-full bg-[#FF6B35] animate-pulse w-full origin-left" />
             </div>
          )}
        </div>
      </div>

      {syncResult && (
        <div className="border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6 animate-in slide-in-from-bottom-4">
          <h3 className="text-xl font-black uppercase mb-4">Sync Results</h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <ResultBadge label="Added" value={syncResult.added} color="bg-green-400" />
            <ResultBadge label="Modified" value={syncResult.modified} color="bg-blue-400" />
            <ResultBadge label="Deleted" value={syncResult.deleted} color="bg-red-400" />
            <ResultBadge label="Skipped" value={syncResult.skipped} color="bg-gray-300" />
            <ResultBadge label="Chunks" value={syncResult.total_chunks} color="bg-[#FFE66D]" />
          </div>
          {syncResult.errors.length > 0 && (
            <div className="mt-4 p-4 border-2 border-red-500 bg-red-50 text-red-700">
              <p className="font-bold mb-2">Errors:</p>
              <ul className="list-disc pl-5">
                {syncResult.errors.map((err, i) => (
                  <li key={i}>{err}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function ResultBadge({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className={cn("border-2 border-black p-3 flex flex-col items-center justify-center", color)}>
      <span className="text-sm font-bold uppercase">{label}</span>
      <span className="text-2xl font-black">{value}</span>
    </div>
  );
}
