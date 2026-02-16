"use client"

import * as React from "react"
import { formatDistanceToNow, differenceInDays } from "date-fns"
import { ChevronDown, ChevronUp } from "lucide-react"
import { ParaProjectRead } from "@/lib/types/para"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { ProjectFiles } from "./project-files"
import { cn } from "@/lib/utils"

interface ProjectCardProps {
  project: ParaProjectRead
  progress?: number
  onProgressChange?: (projectId: string, progress: number) => void
  staleDays?: number
  variant?: "active" | "abandoned"
}

export function ProjectCard({
  project,
  progress: controlledProgress,
  onProgressChange,
  staleDays = 30,
  variant,
}: ProjectCardProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [isMounted, setIsMounted] = React.useState(false)

  const [localProgress, setLocalProgress] = React.useState(0)

  const isControlled = controlledProgress !== undefined

  React.useEffect(() => {
    setIsMounted(true)
    if (!isControlled) {
      const saved = localStorage.getItem(`para-progress-${project.id}`)
      if (saved) {
        setLocalProgress(parseInt(saved, 10))
      }
    }
  }, [project.id, isControlled])

  const progress = isControlled ? controlledProgress : localProgress

  const handleProgressChange = (value: number[]) => {
    const next = value[0]
    if (isControlled && onProgressChange) {
      onProgressChange(project.id, next)
    } else {
      setLocalProgress(next)
      localStorage.setItem(`para-progress-${project.id}`, next.toString())
    }
  }

  const lastModified = project.last_modified_at ? new Date(project.last_modified_at) : null
  const isStale = lastModified ? differenceInDays(new Date(), lastModified) > staleDays : false

  return (
    <div className={cn(
      "bg-[#fffdf5] border-[3px] border-black p-4 relative transition-all",
      "shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]",
      variant === "abandoned" && "border-l-[6px] border-l-[#f87171]"
    )}>
      <div 
        className="flex justify-between items-start mb-4 cursor-pointer"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <h3 className="text-xl font-bold">{project.name}</h3>
            {isStale && (
              <Badge variant="danger" className="text-[10px] uppercase">
                🔴 Stale
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <Badge variant="default" className="text-xs">
              {project.file_count} files
            </Badge>
            {lastModified && (
              <span>
                Updated {formatDistanceToNow(lastModified, { addSuffix: true })}
              </span>
            )}
          </div>
        </div>
        <button 
          className="p-1 border-2 border-black hover:bg-black hover:text-white transition-colors"
          onClick={(e) => {
            e.stopPropagation()
            setIsOpen(!isOpen)
          }}
        >
          {isOpen ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
        </button>
      </div>

      <div className="mb-4">
        {isMounted && (
          <Slider 
            value={[progress]} 
            onValueChange={handleProgressChange}
            max={100}
            step={1}
            label="Progress"
          />
        )}
      </div>

      <ProjectFiles files={project.files} isOpen={isOpen} />
    </div>
  )
}
