"use client";

import { useState } from "react";
import {
  FolderOpen,
  Plus,
  Trash2,
  Check,
  FolderSync,
  AlertCircle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface Project {
  id: string;
  name: string;
  vaultPath: string;
  createdAt: Date;
  lastIndexed?: Date;
  fileCount?: number;
  backendId?: number;
}

interface ProjectManagerProps {
  projects: Project[];
  activeProjectId: string | null;
  onSelectProject: (projectId: string) => void;
  onAddProject: (project: Omit<Project, "id" | "createdAt">) => void;
  onDeleteProject: (projectId: string) => void;
  onReindex: (projectId: string) => void;
}

export function ProjectManager({
  projects,
  activeProjectId,
  onSelectProject,
  onAddProject,
  onDeleteProject,
  onReindex,
}: ProjectManagerProps) {
  const [isAdding, setIsAdding] = useState(false);
  const [newProjectName, setNewProjectName] = useState("");
  const [newVaultPath, setNewVaultPath] = useState("");

  const handleAddProject = () => {
    if (newProjectName.trim() && newVaultPath.trim()) {
      onAddProject({
        name: newProjectName.trim(),
        vaultPath: newVaultPath.trim(),
      });
      setNewProjectName("");
      setNewVaultPath("");
      setIsAdding(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="p-6 border-b border-border">
        <h1 className="text-2xl font-semibold text-foreground mb-2">
          프로젝트 관리
        </h1>
        <p className="text-muted-foreground">
          Obsidian Vault 폴더를 프로젝트로 등록하고 관리합니다.
        </p>
      </div>

      <ScrollArea className="flex-1 p-6">
        <div className="space-y-4 max-w-2xl">
          {/* Add New Project Card */}
          {isAdding ? (
            <Card className="border-primary/50 bg-card">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">새 프로젝트 추가</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="project-name">프로젝트 이름</Label>
                  <Input
                    id="project-name"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    placeholder="예: 개인 노트, 업무 자료"
                    className="bg-input border-border"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="vault-path">Vault 경로</Label>
                  <Input
                    id="vault-path"
                    value={newVaultPath}
                    onChange={(e) => setNewVaultPath(e.target.value)}
                    placeholder="/Users/username/Documents/ObsidianVault"
                    className="bg-input border-border font-mono text-sm"
                  />
                  <p className="text-xs text-muted-foreground">
                    Obsidian Vault 폴더의 전체 경로를 입력하세요.
                  </p>
                </div>
                <div className="flex gap-2 pt-2">
                  <Button
                    onClick={handleAddProject}
                    disabled={!newProjectName.trim() || !newVaultPath.trim()}
                    size="sm"
                  >
                    <Check className="h-4 w-4 mr-2" />
                    추가
                  </Button>
                  <Button
                    onClick={() => {
                      setIsAdding(false);
                      setNewProjectName("");
                      setNewVaultPath("");
                    }}
                    variant="ghost"
                    size="sm"
                  >
                    취소
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Button
              onClick={() => setIsAdding(true)}
              variant="outline"
              className="w-full justify-start gap-2 h-auto py-4 border-dashed border-border hover:border-primary/50 bg-transparent"
            >
              <Plus className="h-5 w-5 text-primary" />
              <span className="text-muted-foreground">
                새 프로젝트 추가하기
              </span>
            </Button>
          )}

          {/* Project List */}
          {projects.length === 0 && !isAdding ? (
            <div className="text-center py-12">
              <FolderOpen className="h-12 w-12 mx-auto text-muted-foreground/50 mb-4" />
              <h3 className="text-lg font-medium text-foreground mb-2">
                프로젝트가 없습니다
              </h3>
              <p className="text-muted-foreground text-sm">
                Obsidian Vault를 프로젝트로 추가하여 시작하세요.
              </p>
            </div>
          ) : (
            <div className="space-y-3">
              {projects.map((project) => (
                <Card
                  key={project.id}
                  className={cn(
                    "cursor-pointer transition-all hover:border-primary/30",
                    activeProjectId === project.id
                      ? "border-primary bg-primary/5"
                      : "border-border bg-card"
                  )}
                  onClick={() => onSelectProject(project.id)}
                >
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3 min-w-0">
                        <div
                          className={cn(
                            "w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0",
                            activeProjectId === project.id
                              ? "bg-primary/20 text-primary"
                              : "bg-muted text-muted-foreground"
                          )}
                        >
                          <FolderOpen className="h-5 w-5" />
                        </div>
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium text-foreground truncate">
                              {project.name}
                            </h3>
                            {activeProjectId === project.id && (
                              <span className="px-2 py-0.5 text-xs rounded-full bg-primary/20 text-primary">
                                활성
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-muted-foreground font-mono truncate mt-1">
                            {project.vaultPath}
                          </p>
                          <div className="flex items-center gap-3 mt-2 text-xs text-muted-foreground">
                            {project.fileCount !== undefined && (
                              <span>{project.fileCount}개 파일</span>
                            )}
                            {project.lastIndexed && (
                              <span>
                                마지막 인덱싱:{" "}
                                {new Date(project.lastIndexed).toLocaleDateString(
                                  "ko-KR"
                                )}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={(e) => {
                            e.stopPropagation();
                            onReindex(project.id);
                          }}
                        >
                          <FolderSync className="h-4 w-4" />
                          <span className="sr-only">재인덱싱</span>
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-destructive hover:text-destructive"
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteProject(project.id);
                          }}
                        >
                          <Trash2 className="h-4 w-4" />
                          <span className="sr-only">삭제</span>
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}

          {/* Info Box */}
          <div className="mt-6 p-4 rounded-lg bg-muted/50 border border-border">
            <div className="flex gap-3">
              <AlertCircle className="h-5 w-5 text-muted-foreground flex-shrink-0 mt-0.5" />
              <div className="text-sm text-muted-foreground">
                <p className="font-medium text-foreground mb-1">참고</p>
                <p>
                  프로젝트를 추가한 후 인덱싱을 실행하면 노트 내용이 임베딩되어
                  AI와 대화할 때 참조됩니다. 노트가 많을수록 처음 인덱싱에
                  시간이 걸릴 수 있습니다.
                </p>
              </div>
            </div>
          </div>
        </div>
      </ScrollArea>
    </div>
  );
}
