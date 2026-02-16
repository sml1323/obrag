"use client"

import * as React from "react"
import { differenceInDays } from "date-fns"
import {
  FolderOpen,
  Activity,
  AlertTriangle,
  TrendingUp,
  Settings,
  FolderSearch,
} from "lucide-react"
import { listParaProjects } from "@/lib/api/para"
import { getSettings, updateSettings } from "@/lib/api/settings"
import { getVaultTree } from "@/lib/api/vault"
import type { ParaProjectRead } from "@/lib/types/para"
import type { TreeNode } from "@/lib/types/vault"
import { Button } from "@/components/ui/button"
import { ProjectCard } from "./project-card"
import { ProgressChart } from "./progress-chart"
import { ProjectFolderPicker } from "./project-folder-picker"

const STALE_DAYS = 30

function getProgressKey(projectId: string): string {
  return `para-progress-${projectId}`
}

function isProjectStale(p: ParaProjectRead): boolean {
  if (!p.last_modified_at) return false
  return differenceInDays(new Date(), new Date(p.last_modified_at)) > STALE_DAYS
}

interface StatTileProps {
  icon: React.ReactNode
  label: string
  value: string | number
  accent: string
}

function StatTile({ icon, label, value, accent }: StatTileProps) {
  return (
    <div className="border-[3px] border-black bg-[#fffdf5] shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] p-4 flex items-center gap-4">
      <div
        className="w-12 h-12 border-[3px] border-black flex items-center justify-center flex-shrink-0"
        style={{ backgroundColor: accent }}
      >
        {icon}
      </div>
      <div>
        <div className="text-sm font-bold uppercase tracking-wide text-gray-600">
          {label}
        </div>
        <div className="text-2xl font-black">{value}</div>
      </div>
    </div>
  )
}

export function ParaDashboard() {
  const [projects, setProjects] = React.useState<ParaProjectRead[]>([])
  const [loading, setLoading] = React.useState(true)
  const [error, setError] = React.useState<string | null>(null)
  const [progressById, setProgressById] = React.useState<Record<string, number>>({})
  const [progressReady, setProgressReady] = React.useState(false)

  const [vaultTree, setVaultTree] = React.useState<TreeNode[]>([])
  const [paraRootPath, setParaRootPath] = React.useState<string | null>(null)
  const [pendingPath, setPendingPath] = React.useState<string | null>(null)
  const [showFolderPicker, setShowFolderPicker] = React.useState(false)
  const [saving, setSaving] = React.useState(false)
  const [vaultConfigured, setVaultConfigured] = React.useState(true)

  const loadAll = React.useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const settings = await getSettings()

      if (!settings.vault_path) {
        setVaultConfigured(false)
        setLoading(false)
        return
      }
      setVaultConfigured(true)

      const currentRoot = settings.para_root_path || null
      setParaRootPath(currentRoot)
      setPendingPath(currentRoot)

      const tree = await getVaultTree()
      setVaultTree(tree.nodes)

      if (!currentRoot) {
        setShowFolderPicker(true)
        setProjects([])
        setLoading(false)
        return
      }

      const data = await listParaProjects()
      const sortedData = [...data].sort((a, b) => {
        const dateA = a.last_modified_at ? new Date(a.last_modified_at).getTime() : 0
        const dateB = b.last_modified_at ? new Date(b.last_modified_at).getTime() : 0
        return dateB - dateA
      })
      setProjects(sortedData)
    } catch (err) {
      console.error("Failed to load projects:", err)
      setError("Failed to load projects. Please try again later.")
    } finally {
      setLoading(false)
    }
  }, [])

  React.useEffect(() => {
    loadAll()
  }, [loadAll])

  React.useEffect(() => {
    if (projects.length === 0) {
      setProgressReady(paraRootPath !== null)
      return
    }
    const map: Record<string, number> = {}
    for (const p of projects) {
      const saved = localStorage.getItem(getProgressKey(p.id))
      map[p.id] = saved ? Math.min(100, Math.max(0, parseInt(saved, 10) || 0)) : 0
    }
    setProgressById(map)
    setProgressReady(true)
  }, [projects, paraRootPath])

  const handleProgressChange = (projectId: string, next: number) => {
    setProgressById((prev) => ({ ...prev, [projectId]: next }))
    localStorage.setItem(getProgressKey(projectId), String(next))
  }

  const handleSaveFolder = async () => {
    if (!pendingPath) return
    setSaving(true)
    try {
      await updateSettings({ para_root_path: pendingPath })
      setParaRootPath(pendingPath)
      setShowFolderPicker(false)
      await loadAll()
    } catch (err) {
      console.error("Failed to save project root:", err)
      setError("Failed to save folder selection.")
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <div className="w-16 h-16 border-4 border-black border-t-transparent rounded-full animate-spin" />
        <p className="font-bold text-xl font-mono">LOADING PROJECTS...</p>
      </div>
    )
  }

  if (!vaultConfigured) {
    return (
      <div className="p-12 text-center border-4 border-black bg-gray-100 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
        <h2 className="text-2xl font-bold mb-4">Vault Not Configured</h2>
        <p className="text-lg mb-6">Please set your vault path in Settings first.</p>
        <a
          href="/settings"
          className="inline-block px-6 py-3 bg-[#FF6B35] border-[3px] border-black font-bold text-lg shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all"
        >
          Go to Settings
        </a>
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

  if (showFolderPicker || !paraRootPath) {
    return (
      <div className="space-y-6">
        <div className="border-4 border-black bg-white shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] p-6">
          <div className="flex items-center gap-3 mb-4">
            <FolderSearch size={28} strokeWidth={3} />
            <h2 className="text-2xl font-black uppercase">Select Project Root Folder</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4 font-mono">
            Choose the folder whose subfolders will be tracked as individual projects.
          </p>
          <div className="max-h-[400px] overflow-y-auto border-2 border-black p-4 bg-gray-50 mb-4">
            <ProjectFolderPicker
              nodes={vaultTree}
              selectedPath={pendingPath}
              onSelect={setPendingPath}
            />
          </div>
          <div className="flex items-center justify-between">
            <div className="text-sm font-bold font-mono">
              {pendingPath ? (
                <span>
                  Selected: <span className="text-[#FF6B35]">{pendingPath}</span>
                </span>
              ) : (
                <span className="text-gray-400">No folder selected</span>
              )}
            </div>
            <div className="flex gap-3">
              {paraRootPath && (
                <Button
                  onClick={() => {
                    setShowFolderPicker(false)
                    setPendingPath(paraRootPath)
                  }}
                  className="border-[3px] border-black font-bold px-6 py-3 h-auto bg-gray-200 hover:bg-gray-300"
                >
                  Cancel
                </Button>
              )}
              <Button
                onClick={handleSaveFolder}
                disabled={!pendingPath || saving}
                className="border-[3px] border-black font-bold px-6 py-3 h-auto bg-[#FF6B35] hover:bg-[#FF8C60] disabled:opacity-50"
              >
                {saving ? "Saving..." : "Set as Project Root"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  const activeProjects = projects.filter((p) => !isProjectStale(p))
  const abandonedProjects = projects.filter((p) => isProjectStale(p))

  const total = projects.length
  const activeCount = activeProjects.length
  const abandonedCount = abandonedProjects.length
  const avgProgress =
    total > 0
      ? Math.round(
          projects.reduce((sum, p) => sum + (progressById[p.id] ?? 0), 0) / total
        )
      : 0

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between border-b-4 border-black pb-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-extrabold uppercase tracking-tighter">
            Projects
          </h1>
          <p className="text-xl font-mono text-gray-600">
            {total} PROJECTS TRACKED
          </p>
        </div>
        <button
          onClick={() => setShowFolderPicker(true)}
          className="flex items-center gap-2 px-4 py-2 border-[3px] border-black bg-[#fffdf5] font-bold text-sm shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-x-[-2px] hover:translate-y-[-2px] hover:shadow-[6px_6px_0px_0px_rgba(0,0,0,1)] transition-all"
        >
          <Settings size={16} strokeWidth={3} />
          <span className="font-mono text-xs truncate max-w-[160px]">{paraRootPath}</span>
        </button>
      </div>

      {progressReady && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <StatTile
              icon={<FolderOpen size={24} strokeWidth={3} />}
              label="Total"
              value={total}
              accent="#FFE66D"
            />
            <StatTile
              icon={<Activity size={24} strokeWidth={3} />}
              label="Active"
              value={activeCount}
              accent="#4ECDC4"
            />
            <StatTile
              icon={<AlertTriangle size={24} strokeWidth={3} />}
              label="Abandoned"
              value={abandonedCount}
              accent="#f87171"
            />
            <StatTile
              icon={<TrendingUp size={24} strokeWidth={3} />}
              label="Avg Progress"
              value={`${avgProgress}%`}
              accent="#a3e635"
            />
          </div>

          <ProgressChart
            projects={projects}
            progressById={progressById}
            staleDays={STALE_DAYS}
          />
        </>
      )}

      {activeProjects.length > 0 && (
        <section className="space-y-4">
          <h2 className="text-2xl font-black uppercase tracking-tight border-b-[3px] border-black pb-2">
            Active Projects
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {activeProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                progress={progressById[project.id] ?? 0}
                onProgressChange={handleProgressChange}
                staleDays={STALE_DAYS}
                variant="active"
              />
            ))}
          </div>
        </section>
      )}

      {abandonedProjects.length > 0 && (
        <section className="space-y-4">
          <div className="flex items-center gap-3 border-b-[3px] border-black pb-2">
            <h2 className="text-2xl font-black uppercase tracking-tight">
              유기된 프로젝트
            </h2>
            <span className="text-sm font-bold text-gray-500 font-mono">
              30+ DAYS SINCE LAST UPDATE
            </span>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {abandonedProjects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                progress={progressById[project.id] ?? 0}
                onProgressChange={handleProgressChange}
                staleDays={STALE_DAYS}
                variant="abandoned"
              />
            ))}
          </div>
        </section>
      )}

      {projects.length === 0 && paraRootPath && (
        <div className="p-12 text-center border-4 border-black bg-gray-100 shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
          <h2 className="text-2xl font-bold mb-4">No projects found</h2>
          <p className="text-lg mb-6">
            No subfolders with synced files found under{" "}
            <span className="font-mono font-bold">{paraRootPath}</span>.
          </p>
          <p className="text-sm text-gray-600">Run embedding first, or change the project root folder.</p>
        </div>
      )}
    </div>
  )
}
