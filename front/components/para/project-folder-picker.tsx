"use client"

import * as React from "react"
import { ChevronRight, ChevronDown, Folder, FolderOpen } from "lucide-react"
import { TreeNode } from "@/lib/types/vault"
import { cn } from "@/lib/utils"

interface ProjectFolderPickerProps {
  nodes: TreeNode[]
  selectedPath: string | null
  onSelect: (path: string) => void
}

export function ProjectFolderPicker({
  nodes,
  selectedPath,
  onSelect,
}: ProjectFolderPickerProps) {
  const folders = nodes.filter((n) => n.is_dir)

  if (folders.length === 0) {
    return (
      <div className="p-4 text-sm text-gray-500 italic">
        No folders found in vault
      </div>
    )
  }

  return (
    <div className="flex flex-col">
      {folders.map((node) => (
        <FolderPickerNode
          key={node.path}
          node={node}
          selectedPath={selectedPath}
          onSelect={onSelect}
          level={0}
        />
      ))}
    </div>
  )
}

interface FolderPickerNodeProps {
  node: TreeNode
  selectedPath: string | null
  onSelect: (path: string) => void
  level: number
}

function FolderPickerNode({
  node,
  selectedPath,
  onSelect,
  level,
}: FolderPickerNodeProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const isSelected = selectedPath === node.path
  const childFolders = (node.children ?? []).filter((n) => n.is_dir)
  const hasChildren = childFolders.length > 0

  return (
    <div className="flex flex-col select-none">
      <div
        className={cn(
          "flex items-center py-1.5 cursor-pointer transition-colors",
          isSelected
            ? "bg-[#FF6B35] text-black font-black"
            : "hover:bg-[#FFE66D]",
          level > 0 && "border-l-2 border-dashed border-gray-300"
        )}
        style={{ paddingLeft: `${level * 20 + 8}px` }}
        onClick={() => onSelect(node.path)}
      >
        {hasChildren ? (
          <button
            className="p-0.5 mr-1 hover:bg-black/10 transition-colors"
            onClick={(e) => {
              e.stopPropagation()
              setIsOpen(!isOpen)
            }}
          >
            {isOpen ? (
              <ChevronDown size={14} strokeWidth={3} />
            ) : (
              <ChevronRight size={14} strokeWidth={3} />
            )}
          </button>
        ) : (
          <span className="w-[22px]" />
        )}

        {isSelected ? (
          <FolderOpen size={18} className="mr-2 flex-shrink-0" strokeWidth={2.5} />
        ) : (
          <Folder size={18} className="mr-2 flex-shrink-0" strokeWidth={2} />
        )}

        <span className="text-sm truncate">{node.name}</span>

        {isSelected && (
          <span className="ml-auto mr-2 text-[10px] font-black uppercase bg-black text-white px-1.5 py-0.5">
            SELECTED
          </span>
        )}
      </div>

      {hasChildren && isOpen && (
        <div>
          {childFolders.map((child) => (
            <FolderPickerNode
              key={child.path}
              node={child}
              selectedPath={selectedPath}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </div>
      )}
    </div>
  )
}
