"use client";

import React, { useState } from "react";
import { TreeNode } from "@/lib/types/vault";
import { Checkbox } from "@/components/ui/checkbox";
import { cn } from "@/lib/utils";

interface FolderTreeProps {
  nodes: TreeNode[];
  selectedPaths: Set<string>;
  onToggle: (path: string, checked: boolean) => void;
  level?: number;
}

export function FolderTree({ nodes, selectedPaths, onToggle, level = 0 }: FolderTreeProps) {
  return (
    <div className="flex flex-col">
      {nodes.map((node) => (
        <FolderNode
          key={node.path}
          node={node}
          selectedPaths={selectedPaths}
          onToggle={onToggle}
          level={level}
        />
      ))}
    </div>
  );
}

interface FolderNodeProps {
  node: TreeNode;
  selectedPaths: Set<string>;
  onToggle: (path: string, checked: boolean) => void;
  level: number;
}

function FolderNode({ node, selectedPaths, onToggle, level }: FolderNodeProps) {
  const [isOpen, setIsOpen] = useState(false);
  const isSelected = selectedPaths.has(node.path);

  // Check if any children are selected to show indeterminate state if needed
  // (Simple implementation: just check exact match for now, or let parent handle logic)
  
  const handleToggle = (checked: boolean) => {
    onToggle(node.path, checked);
  };

  const toggleOpen = () => {
    if (node.is_dir) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div className="flex flex-col select-none">
      <div 
        className={cn(
          "flex items-center py-1 hover:bg-[#FFE66D] transition-colors cursor-pointer",
          level > 0 && "border-l-2 border-dashed border-gray-200"
        )}
        style={{ paddingLeft: `${level * 24 + 8}px` }}
      >
        <div className="mr-2" onClick={(e) => e.stopPropagation()}>
          <Checkbox 
            checked={isSelected} 
            onChange={handleToggle}
          />
        </div>
        
        <div 
          className="flex items-center flex-1 py-1"
          onClick={toggleOpen}
        >
          <span className="mr-2 text-xl">
            {node.is_dir ? "📁" : "📄"}
          </span>
          <span className="font-medium text-sm truncate">
            {node.name}
          </span>
          {node.is_dir && node.children.length > 0 && (
            <span className="ml-auto mr-4 text-xs text-gray-500 font-mono">
              {isOpen ? "[-]" : "[+]"}
            </span>
          )}
        </div>
      </div>

      {node.is_dir && isOpen && node.children && (
        <FolderTree
          nodes={node.children}
          selectedPaths={selectedPaths}
          onToggle={onToggle}
          level={level + 1}
        />
      )}
    </div>
  );
}
