"use client";

import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  ResponsiveContainer,
  Cell,
  Tooltip,
} from "recharts";
import {
  Folder,
  FolderOpen,
  FileText,
  ChevronLeft,
  AlertTriangle,
  TrendingUp,
  Clock,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Slider } from "@/components/ui/slider";
import { ChartContainer } from "@/components/ui/chart";
import { SadCharacter } from "@/components/sad-character";
import { cn } from "@/lib/utils";

export interface ParaProject {
  id: string;
  name: string;
  progress: number;
  lastModified: Date;
  fileCount: number;
  files: ParaFile[];
}

export interface ParaFile {
  id: string;
  name: string;
  lastModified: Date;
  preview?: string;
}

interface ParaDashboardProps {
  projects: ParaProject[];
  onUpdateProgress: (projectId: string, progress: number) => void;
  staleDays?: number;
}

const STALE_THRESHOLD_DAYS = 14;

function getDaysSinceModified(date: Date): number {
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - new Date(date).getTime());
  return Math.floor(diffTime / (1000 * 60 * 60 * 24));
}

function formatDate(date: Date): string {
  const d = new Date(date);
  return d.toLocaleDateString("ko-KR", {
    month: "short",
    day: "numeric",
  });
}

export function ParaDashboard({
  projects,
  onUpdateProgress,
  staleDays = STALE_THRESHOLD_DAYS,
}: ParaDashboardProps) {
  const [selectedProject, setSelectedProject] = useState<ParaProject | null>(
    null
  );
  const [editingProgress, setEditingProgress] = useState<string | null>(null);

  // Sort projects by staleness (most stale first)
  const staleProjects = [...projects]
    .map((p) => ({
      ...p,
      daysSinceModified: getDaysSinceModified(p.lastModified),
    }))
    .filter((p) => p.daysSinceModified >= staleDays)
    .sort((a, b) => b.daysSinceModified - a.daysSinceModified);

  // Chart data
  const progressChartData = projects.map((p) => ({
    name: p.name.length > 8 ? p.name.slice(0, 8) + "..." : p.name,
    fullName: p.name,
    progress: p.progress,
  }));

  const staleChartData = staleProjects.slice(0, 5).map((p) => ({
    name: p.name.length > 8 ? p.name.slice(0, 8) + "..." : p.name,
    fullName: p.name,
    days: p.daysSinceModified,
  }));

  // Project detail view
  if (selectedProject) {
    return (
      <div className="flex flex-col h-full">
        {/* Header */}
        <header className="h-14 border-b border-border flex items-center gap-3 px-4 bg-background/80 backdrop-blur-sm">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setSelectedProject(null)}
            className="h-8 w-8"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <FolderOpen className="h-5 w-5 text-primary" />
          <h1 className="font-semibold text-foreground">
            {selectedProject.name}
          </h1>
          <span className="text-xs text-muted-foreground ml-auto">
            {selectedProject.fileCount}개 파일
          </span>
        </header>

        {/* File list */}
        <div className="flex-1 overflow-y-auto p-4">
          <div className="max-w-3xl mx-auto space-y-2">
            {selectedProject.files.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                <FileText className="h-12 w-12 mx-auto mb-3 opacity-30" />
                <p>파일이 없습니다</p>
              </div>
            ) : (
              selectedProject.files.map((file) => (
                <button
                  key={file.id}
                  type="button"
                  className="w-full p-3 rounded-lg border border-border bg-card hover:bg-card/80 transition-colors text-left"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-foreground truncate">
                        {file.name}
                      </p>
                      {file.preview && (
                        <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                          {file.preview}
                        </p>
                      )}
                    </div>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatDate(file.lastModified)}
                    </span>
                  </div>
                </button>
              ))
            )}
          </div>
        </div>
      </div>
    );
  }

  // Dashboard view
  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <header className="h-14 border-b border-border flex items-center px-4 bg-background/80 backdrop-blur-sm">
        <h1 className="font-semibold text-foreground">PARA 프로젝트 대시보드</h1>
        <span className="text-xs text-muted-foreground ml-3">
          {projects.length}개 프로젝트
        </span>
      </header>

      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-6xl mx-auto space-y-6">
          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Progress Chart */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2 text-card-foreground">
                  <TrendingUp className="h-4 w-4 text-accent" />
                  프로젝트 진척도
                </CardTitle>
              </CardHeader>
              <CardContent>
                {progressChartData.length > 0 ? (
                  <ChartContainer
                    config={{
                      progress: {
                        label: "진척도",
                        color: "oklch(0.55 0.18 175)",
                      },
                    }}
                    className="h-[200px]"
                  >
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={progressChartData} layout="vertical">
                        <XAxis
                          type="number"
                          domain={[0, 100]}
                          tickFormatter={(v) => `${v}%`}
                          stroke="oklch(0.6 0.02 250)"
                          fontSize={12}
                        />
                        <YAxis
                          type="category"
                          dataKey="name"
                          width={80}
                          stroke="oklch(0.6 0.02 250)"
                          fontSize={12}
                        />
                        <Tooltip
                          content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                              const data = payload[0].payload;
                              return (
                                <div className="bg-popover border border-border rounded-lg p-2 shadow-lg">
                                  <p className="text-sm font-medium text-popover-foreground">
                                    {data.fullName}
                                  </p>
                                  <p className="text-xs text-muted-foreground">
                                    진척도: {data.progress}%
                                  </p>
                                </div>
                              );
                            }
                            return null;
                          }}
                        />
                        <Bar dataKey="progress" radius={[0, 4, 4, 0]}>
                          {progressChartData.map((entry, index) => (
                            <Cell
                              key={`cell-${index}`}
                              fill={
                                entry.progress >= 80
                                  ? "oklch(0.55 0.18 175)"
                                  : entry.progress >= 50
                                    ? "oklch(0.7 0.15 280)"
                                    : "oklch(0.6 0.15 45)"
                              }
                            />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </ChartContainer>
                ) : (
                  <div className="h-[200px] flex items-center justify-center text-muted-foreground text-sm">
                    프로젝트를 추가해주세요
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Stale Projects Chart */}
            <Card className="bg-card border-border">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium flex items-center gap-2 text-card-foreground">
                  <AlertTriangle className="h-4 w-4 text-destructive" />
                  유기된 프로젝트
                  <span className="text-xs font-normal text-muted-foreground">
                    ({staleDays}일 이상 미수정)
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {staleChartData.length > 0 ? (
                  <div className="flex gap-4">
                    <div className="flex-shrink-0">
                      <SadCharacter
                        message=""
                        size="md"
                        daysStale={staleChartData[0]?.days}
                      />
                    </div>
                    <ChartContainer
                      config={{
                        days: {
                          label: "방치 일수",
                          color: "oklch(0.55 0.2 25)",
                        },
                      }}
                      className="h-[160px] flex-1"
                    >
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={staleChartData} layout="vertical">
                          <XAxis
                            type="number"
                            tickFormatter={(v) => `${v}일`}
                            stroke="oklch(0.6 0.02 250)"
                            fontSize={12}
                          />
                          <YAxis
                            type="category"
                            dataKey="name"
                            width={70}
                            stroke="oklch(0.6 0.02 250)"
                            fontSize={12}
                          />
                          <Tooltip
                            content={({ active, payload }) => {
                              if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                  <div className="bg-popover border border-border rounded-lg p-2 shadow-lg">
                                    <p className="text-sm font-medium text-popover-foreground">
                                      {data.fullName}
                                    </p>
                                    <p className="text-xs text-muted-foreground">
                                      {data.days}일 동안 수정 없음
                                    </p>
                                  </div>
                                );
                              }
                              return null;
                            }}
                          />
                          <Bar
                            dataKey="days"
                            fill="oklch(0.55 0.2 25)"
                            radius={[0, 4, 4, 0]}
                          />
                        </BarChart>
                      </ResponsiveContainer>
                    </ChartContainer>
                  </div>
                ) : (
                  <div className="h-[160px] flex items-center justify-center text-muted-foreground text-sm">
                    <div className="text-center">
                      <p>유기된 프로젝트가 없어요</p>
                      <p className="text-xs mt-1">잘하고 계시네요!</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Project List */}
          <Card className="bg-card border-border">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium flex items-center gap-2 text-card-foreground">
                <Folder className="h-4 w-4 text-primary" />
                프로젝트 목록
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {projects.length === 0 ? (
                  <div className="text-center py-8 text-muted-foreground">
                    <Folder className="h-12 w-12 mx-auto mb-3 opacity-30" />
                    <p>프로젝트가 없습니다</p>
                    <p className="text-xs mt-1">
                      프로젝트 폴더를 추가해주세요
                    </p>
                  </div>
                ) : (
                  projects.map((project) => {
                    const daysSinceModified = getDaysSinceModified(
                      project.lastModified
                    );
                    const isStale = daysSinceModified >= staleDays;

                    return (
                      <div
                        key={project.id}
                        className={cn(
                          "p-3 rounded-lg border transition-colors",
                          isStale
                            ? "border-destructive/30 bg-destructive/5"
                            : "border-border bg-card hover:bg-card/80"
                        )}
                      >
                        <div className="flex items-center gap-3">
                          <button
                            type="button"
                            onClick={() => setSelectedProject(project)}
                            className="flex items-center gap-3 flex-1 min-w-0 text-left"
                          >
                            <div
                              className={cn(
                                "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                                isStale
                                  ? "bg-destructive/10"
                                  : "bg-primary/10"
                              )}
                            >
                              {isStale ? (
                                <SadCharacter message="" size="sm" />
                              ) : (
                                <Folder
                                  className={cn(
                                    "h-5 w-5",
                                    isStale
                                      ? "text-destructive"
                                      : "text-primary"
                                  )}
                                />
                              )}
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="font-medium text-foreground truncate">
                                {project.name}
                              </p>
                              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                <span>{project.fileCount}개 파일</span>
                                <span className="w-1 h-1 rounded-full bg-muted-foreground/50" />
                                <span className="flex items-center gap-1">
                                  <Clock className="h-3 w-3" />
                                  {daysSinceModified}일 전
                                </span>
                              </div>
                            </div>
                          </button>

                          {/* Progress control */}
                          <div className="flex items-center gap-3 flex-shrink-0">
                            {editingProgress === project.id ? (
                              <div className="flex items-center gap-2 w-40">
                                <Slider
                                  value={[project.progress]}
                                  onValueChange={([value]) =>
                                    onUpdateProgress(project.id, value)
                                  }
                                  onValueCommit={() => setEditingProgress(null)}
                                  max={100}
                                  step={5}
                                  className="flex-1"
                                />
                                <span className="text-xs font-medium text-foreground w-10 text-right">
                                  {project.progress}%
                                </span>
                              </div>
                            ) : (
                              <button
                                type="button"
                                onClick={() => setEditingProgress(project.id)}
                                className="flex items-center gap-2 px-2 py-1 rounded-md hover:bg-muted transition-colors"
                              >
                                <div className="w-20 h-2 rounded-full bg-muted overflow-hidden">
                                  <div
                                    className={cn(
                                      "h-full rounded-full transition-all",
                                      project.progress >= 80
                                        ? "bg-accent"
                                        : project.progress >= 50
                                          ? "bg-primary"
                                          : "bg-chart-3"
                                    )}
                                    style={{ width: `${project.progress}%` }}
                                  />
                                </div>
                                <span className="text-xs font-medium text-muted-foreground w-10 text-right">
                                  {project.progress}%
                                </span>
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
