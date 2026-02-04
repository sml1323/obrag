"use client";

import React, { useState } from "react";
import { TreeNode } from "@/lib/types/vault";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import {
  Check,
  ChevronDown,
  ChevronRight,
  Folder,
  FolderOpen,
  File,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export interface FolderTreeProps {
  nodes: TreeNode[];
  checkedPaths: Record<string, boolean>;
  onToggle: (path: string, checked: boolean) => void;
  onToggleAll: (checked: boolean) => void;
}

const TreeCheckbox = ({
  checked,
  onCheckedChange,
  className,
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  className?: string;
}) => {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={(e) => {
        e.stopPropagation();
        onCheckedChange(!checked);
      }}
      className={cn(
        "peer h-4 w-4 shrink-0 rounded-sm border border-primary ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=checked]:text-primary-foreground",
        checked ? "bg-primary text-primary-foreground" : "bg-transparent",
        className
      )}
    >
      {checked && <Check className="h-3 w-3 mx-auto" />}
    </button>
  );
};

interface TreeNodeItemProps {
  node: TreeNode;
  checkedPaths: Record<string, boolean>;
  onToggle: (path: string, checked: boolean) => void;
  depth: number;
}

const TreeNodeItem = ({
  node,
  checkedPaths,
  onToggle,
  depth,
}: TreeNodeItemProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const isChecked = checkedPaths[node.path] ?? true;
  const hasChildren = node.children && node.children.length > 0;

  const handleToggle = (checked: boolean) => {
    onToggle(node.path, checked);
  };

  const handleExpand = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (hasChildren) {
      setIsOpen(!isOpen);
    }
  };

  return (
    <div className="select-none">
      <div
        className={cn(
          "flex items-center py-1 pr-2 hover:bg-accent/50 rounded-md transition-colors cursor-pointer group",
          depth > 0 && "ml-4"
        )}
        style={{ paddingLeft: `${depth * 12}px` }}
        onClick={handleExpand}
      >
        <div className="flex items-center justify-center w-6 h-6 shrink-0 mr-1 text-muted-foreground/70">
          {hasChildren ? (
            <button
              type="button"
              onClick={handleExpand}
              className="p-0.5 hover:text-foreground hover:bg-muted rounded-sm transition-colors"
            >
              {isOpen ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </button>
          ) : (
            <div className="w-4 h-4" />
          )}
        </div>

        <div className="mr-2 flex items-center shrink-0">
          <TreeCheckbox
            checked={isChecked}
            onCheckedChange={handleToggle}
          />
        </div>

        <div className="flex items-center gap-2 min-w-0 flex-1">
          {hasChildren ? (
            isOpen ? (
              <FolderOpen className="h-4 w-4 text-blue-500/80 shrink-0" />
            ) : (
              <Folder className="h-4 w-4 text-blue-500/80 shrink-0" />
            )
          ) : (
            <File className="h-4 w-4 text-muted-foreground shrink-0" />
          )}
          <span className="text-sm truncate font-medium text-foreground/90 group-hover:text-foreground transition-colors">
            {node.name}
          </span>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {isOpen && hasChildren && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            {node.children.map((child) => (
              <TreeNodeItem
                key={child.path}
                node={child}
                checkedPaths={checkedPaths}
                onToggle={onToggle}
                depth={depth + 1}
              />
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export const FolderTree = ({
  nodes,
  checkedPaths,
  onToggle,
  onToggleAll,
}: FolderTreeProps) => {
  return (
    <div className="flex flex-col h-full bg-card border border-border rounded-lg shadow-sm">
      <div className="p-3 border-b border-border flex items-center justify-between bg-muted/30">
        <h3 className="font-semibold text-sm text-foreground">
          Embedding Scope
        </h3>
        <div className="flex gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggleAll(true)}
            className="h-7 px-2 text-xs hover:bg-primary/10 hover:text-primary"
          >
            Select All
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onToggleAll(false)}
            className="h-7 px-2 text-xs hover:bg-destructive/10 hover:text-destructive"
          >
            Deselect All
          </Button>
        </div>
      </div>
      <ScrollArea className="flex-1 p-2">
        <div className="space-y-0.5">
          {nodes.map((node) => (
            <TreeNodeItem
              key={node.path}
              node={node}
              checkedPaths={checkedPaths}
              onToggle={onToggle}
              depth={0}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
};

export default FolderTree;
