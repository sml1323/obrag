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
  project: ParaProjectRead;
}

export function ProjectCard({ project }: ProjectCardProps) {
  const [isOpen, setIsOpen] = React.useState(false)
  const [progress, setProgress] = React.useState(0)
  const [isMounted, setIsMounted] = React.useState(false)

  React.useEffect(() => {
    setIsMounted(true)
    const saved = localStorage.getItem(`para-progress-${project.id}`)
    if (saved) {
      setProgress(parseInt(saved, 10))
    }
  }, [project.id])

  const handleProgressChange = (value: number[]) => {
    const newProgress = value[0]
    setProgress(newProgress)
    localStorage.setItem(`para-progress-${project.id}`, newProgress.toString())
  }

  const lastModified = project.last_modified_at ? new Date(project.last_modified_at) : null
  const isStale = lastModified ? differenceInDays(new Date(), lastModified) > 30 : false

  return (
    <div className={cn(
      "bg-[#fffdf5] border-[3px] border-black p-4 relative transition-all",
      "shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[10px_10px_0px_0px_rgba(0,0,0,1)]"
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
