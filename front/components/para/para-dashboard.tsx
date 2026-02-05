"use client"

import * as React from "react"
import { listParaProjects } from "@/lib/api/para"
import type { ParaProjectRead } from "@/lib/types/para"
import { ProjectCard } from "./project-card"

export function ParaDashboard() {
  const [projects, setProjects] = React.useState<ParaProjectRead[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)

  React.useEffect(() => {
    async function fetchProjects() {
      try {
        setLoading(true)
        const data = await listParaProjects()
        
        // Sort by last_modified_at (most recent first)
        const sortedData = [...data].sort((a, b) => {
          const dateA = a.last_modified_at ? new Date(a.last_modified_at).getTime() : 0
          const dateB = b.last_modified_at ? new Date(b.last_modified_at).getTime() : 0
          return dateB - dateA
        })
        
        setProjects(sortedData)
      } catch (err) {
        console.error("Failed to fetch PARA projects:", err)
        setError("Failed to load projects. Please try again later.")
      } finally {
        setLoading(false)
      }
    }

    fetchProjects()
  }, [])

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin" />
        <p className="font-bold text-xl font-mono">LOADING PROJECTS...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 border-4 border-black bg-[#f87171] text-black font-bold text-center shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        {error}
      </div>
    )
  }

  if (projects.length === 0) {
    return (
      <div className="p-12 text-center border-4 border-black bg-gray-100 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <h2 className="text-2xl font-bold mb-4">No PARA projects found</h2>
        <p className="text-lg mb-6">Configure your vault and run embedding first.</p>
        <div className="inline-block px-4 py-2 bg-[#fde047] border-2 border-black font-bold">
          Check Settings
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-2 border-b-4 border-black pb-4">
        <h1 className="text-4xl font-extrabold uppercase tracking-tighter">
          Active Projects
        </h1>
        <p className="text-xl font-mono text-gray-600">
          {projects.length} PROJECTS TRACKED
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {projects.map((project) => (
          <ProjectCard key={project.id} project={project} />
        ))}
      </div>
    </div>
  )
}
