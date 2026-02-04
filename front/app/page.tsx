"use client";

import { useState, useEffect, useCallback } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { BookOpen, Database } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ChatInterface, type Message } from "@/components/chat-interface";
import {
  SettingsPanel,
  defaultSettings,
  type AppSettings,
} from "@/components/settings-panel";
import {
  EmbeddingStatus,
  type EmbeddingState,
} from "@/components/embedding-status";
import { EmbeddingScopeModal } from "@/components/embedding-scope-modal";
import { MainMenu, type MenuView } from "@/components/main-menu";
import { TopicManager, type Topic, type Conversation } from "@/components/topic-manager";
import {
  ParaDashboard,
  type ParaProject,
} from "@/components/para-dashboard";
import { ReviewEngine } from "@/components/review-engine";
import { type Project } from "@/components/project-manager";
import { listProjects, getProjectByPath } from "@/lib/api/projects";
import { triggerSync } from "@/lib/api/sync";
import { getSettings } from "@/lib/api/settings";
import { listParaProjects } from "@/lib/api/para";
import type { ProjectRead } from "@/lib/types/project";
import type { ParaProjectRead } from "@/lib/types/para";

export default function Home() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [embeddingState, setEmbeddingState] = useState<EmbeddingState>("idle");
  const [_embeddingProgress, _setEmbeddingProgress] = useState(0);
  const [currentView, setCurrentView] = useState<MenuView>("chat");

  // Vault projects state (for embedding)
  const [vaultProjects, setVaultProjects] = useState<Project[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  // PARA projects state
  const [paraProjects, setParaProjects] = useState<ParaProject[]>([]);

  // Topics and Conversations state
  const [topics, setTopics] = useState<Topic[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeTopicId, _setActiveTopicId] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Embedding scope state
  const [embeddingScope, setEmbeddingScope] = useState<string[]>([]);
  const [showEmbeddingScopeModal, setShowEmbeddingScopeModal] = useState(false);
  const [paraRoot, setParaRoot] = useState<string | null>(null);

  const buildParaProjects = useCallback((backendParaProjects: ParaProjectRead[]) => {
    const savedParaProjects = localStorage.getItem("obsidian-ai-para-projects");
    const progressById: Record<string, number> = {};
    if (savedParaProjects) {
      try {
        const parsed = JSON.parse(savedParaProjects);
        if (Array.isArray(parsed)) {
          for (const item of parsed) {
            if (item && typeof item.id === "string") {
              progressById[item.id] =
                typeof item.progress === "number" ? item.progress : 0;
            }
          }
        }
      } catch {
        // ignore parse errors
      }
    }

    return backendParaProjects
      .map((p: ParaProjectRead): ParaProject | null => {
        if (!p.last_modified_at) {
          return null;
        }
        return {
          id: p.id,
          name: p.name,
          progress: progressById[p.id] ?? 0,
          lastModified: new Date(p.last_modified_at),
          fileCount: p.file_count,
          files: p.files.map((f) => ({
            id: f.id,
            name: f.name,
            lastModified: new Date(f.last_modified_at),
          })),
        };
      })
      .filter((p): p is ParaProject => Boolean(p));
  }, []);

  // Load data from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem("obsidian-ai-settings");
    if (savedSettings) {
      try {
        const parsed = JSON.parse(savedSettings);
        setSettings({ ...defaultSettings, ...parsed });
      } catch {
        // Ignore parse errors
      }
    }

    const savedProjects = localStorage.getItem("obsidian-ai-vault-projects");
    if (savedProjects) {
      try {
        setVaultProjects(JSON.parse(savedProjects));
      } catch {
        // Ignore parse errors
      }
    }

    const savedActiveProject = localStorage.getItem(
      "obsidian-ai-active-project"
    );
    if (savedActiveProject) {
      setActiveProjectId(savedActiveProject);
    }

    const savedParaProjects = localStorage.getItem("obsidian-ai-para-projects");
    if (savedParaProjects) {
      try {
        const parsed = JSON.parse(savedParaProjects);
        if (Array.isArray(parsed)) {
          const hydrated = parsed.map((p) => ({
            ...p,
            files: Array.isArray(p.files) ? p.files : [],
          }));
          setParaProjects(hydrated);
        }
      } catch {
        // Ignore parse errors
      }
    }

    const savedTopics = localStorage.getItem("obsidian-ai-topics");
    if (savedTopics) {
      try {
        setTopics(JSON.parse(savedTopics));
      } catch {
        // Ignore parse errors
      }
    }

    const savedConversations = localStorage.getItem("obsidian-ai-conversations");
    if (savedConversations) {
      try {
        setConversations(JSON.parse(savedConversations));
      } catch {
        // Ignore parse errors
      }
    }

    const savedParaRoot = localStorage.getItem("obsidian-ai-para-root");
    if (savedParaRoot) {
      setParaRoot(savedParaRoot);
    }

    const savedEmbeddingPaths = localStorage.getItem("obsidian-ai-embedding-paths");
    if (savedEmbeddingPaths) {
      try {
        const parsed = JSON.parse(savedEmbeddingPaths);
        if (Array.isArray(parsed)) {
          setEmbeddingScope(parsed);
        }
      } catch {
        // Ignore parse errors
      }
    }
  }, []);

  // Sync projects from backend
  useEffect(() => {
    const syncFromBackend = async () => {
      const [projectsResult, settingsResult] = await Promise.allSettled([
        listProjects(),
        getSettings(),
      ]);

      if (projectsResult.status === "fulfilled") {
        const backendProjects = projectsResult.value;
        if (backendProjects.length > 0) {
          const convertedProjects: Project[] = backendProjects.map((bp: ProjectRead) => ({
            id: crypto.randomUUID(),
            name: bp.name,
            vaultPath: bp.path,
            createdAt: new Date(bp.created_at),
            lastIndexed: bp.last_modified_at ? new Date(bp.last_modified_at) : undefined,
            backendId: bp.id,
          }));

          setVaultProjects(prev => {
            const backendPaths = new Set(convertedProjects.map(p => p.vaultPath));
            const offlineOnly = prev.filter(p => !backendPaths.has(p.vaultPath) && !p.backendId);
            const merged = [...convertedProjects, ...offlineOnly];
            localStorage.setItem("obsidian-ai-vault-projects", JSON.stringify(merged));
            return merged;
          });

          console.log("[Sync] Loaded", backendProjects.length, "projects from backend");
        }
      } else {
        console.warn("[Sync] Failed to load projects:", projectsResult.reason);
      }

      if (settingsResult.status === "fulfilled") {
        const backendSettings = settingsResult.value;
        setSettings(prev => ({
          ...prev,
          vaultPath: backendSettings.vault_path || prev.vaultPath,
          paraRootPath: backendSettings.para_root_path || prev.paraRootPath,
          llmProvider: backendSettings.llm_provider,
          llmModel: backendSettings.llm_model,
          embeddingProvider: backendSettings.embedding_provider,
          embeddingModel: backendSettings.embedding_model,
          ollamaEndpoint: backendSettings.ollama_endpoint,
        }));

        if (backendSettings.vault_path) {
          const matchingProject = await getProjectByPath(backendSettings.vault_path);
          if (matchingProject) {
            const frontendProject = {
              id: crypto.randomUUID(),
              name: matchingProject.name,
              vaultPath: matchingProject.path,
              createdAt: new Date(matchingProject.created_at),
              backendId: matchingProject.id,
            };
            setVaultProjects(prev => {
              const exists = prev.some(p => p.backendId === matchingProject.id);
              if (!exists) {
                const updated = [...prev, frontendProject];
                localStorage.setItem("obsidian-ai-vault-projects", JSON.stringify(updated));
                return updated;
              }
              return prev;
            });
            setActiveProjectId(prev => {
              if (!prev) {
                const project = vaultProjects.find(p => p.backendId === matchingProject.id) || frontendProject;
                localStorage.setItem("obsidian-ai-active-project", project.id);
                return project.id;
              }
              return prev;
            });
          }
        }
      } else {
        console.warn("[Sync] Failed to load settings:", settingsResult.reason);
      }

    };
    
    syncFromBackend();
  }, []);

  useEffect(() => {
    const refreshParaProjects = async () => {
      if (!settings.paraRootPath) {
        setParaProjects([]);
        localStorage.removeItem("obsidian-ai-para-projects");
        return;
      }

      try {
        const backendParaProjects = await listParaProjects();
        const mapped = buildParaProjects(backendParaProjects);
        setParaProjects(mapped);
        localStorage.setItem(
          "obsidian-ai-para-projects",
          JSON.stringify(mapped)
        );
      } catch (error) {
        console.warn("[PARA] Failed to refresh projects:", error);
      }
    };

    refreshParaProjects();
  }, [settings.paraRootPath, settings.vaultPath, buildParaProjects]);

  // Save settings to localStorage
  const handleSettingsChange = useCallback((newSettings: AppSettings) => {
    setSettings(newSettings);
    localStorage.setItem("obsidian-ai-settings", JSON.stringify(newSettings));
  }, []);

  const handleProjectCreated = useCallback((backendId: number, vaultPath: string) => {
    const existingProject = vaultProjects.find(p => p.vaultPath === vaultPath);
    
    if (existingProject) {
      const updatedProjects = vaultProjects.map(p =>
        p.vaultPath === vaultPath ? { ...p, backendId } : p
      );
      setVaultProjects(updatedProjects);
      localStorage.setItem("obsidian-ai-vault-projects", JSON.stringify(updatedProjects));
      setActiveProjectId(existingProject.id);
      localStorage.setItem("obsidian-ai-active-project", existingProject.id);
    } else {
      const newProject: Project = {
        id: crypto.randomUUID(),
        name: vaultPath.split('/').pop() || 'Vault',
        vaultPath,
        createdAt: new Date(),
        backendId,
      };
      const updatedProjects = [...vaultProjects, newProject];
      setVaultProjects(updatedProjects);
      localStorage.setItem("obsidian-ai-vault-projects", JSON.stringify(updatedProjects));
      setActiveProjectId(newProject.id);
      localStorage.setItem("obsidian-ai-active-project", newProject.id);
    }
  }, [vaultProjects]);

  // Vault Project handlers
  const _handleAddProject = useCallback(
    (projectData: Omit<Project, "id" | "createdAt">) => {
      const newProject: Project = {
        ...projectData,
        id: crypto.randomUUID(),
        createdAt: new Date(),
      };
      const updatedProjects = [...vaultProjects, newProject];
      setVaultProjects(updatedProjects);
      localStorage.setItem(
        "obsidian-ai-vault-projects",
        JSON.stringify(updatedProjects)
      );

      // Auto-select the new project
      setActiveProjectId(newProject.id);
      localStorage.setItem("obsidian-ai-active-project", newProject.id);
    },
    [vaultProjects]
  );

  const _handleSelectProject = useCallback((projectId: string) => {
    setActiveProjectId(projectId);
    localStorage.setItem("obsidian-ai-active-project", projectId);
  }, []);

  const _handleDeleteProject = useCallback(
    (projectId: string) => {
      const updatedProjects = vaultProjects.filter((p) => p.id !== projectId);
      setVaultProjects(updatedProjects);
      localStorage.setItem(
        "obsidian-ai-vault-projects",
        JSON.stringify(updatedProjects)
      );

      if (activeProjectId === projectId) {
        const newActiveId = updatedProjects[0]?.id || null;
        setActiveProjectId(newActiveId);
        if (newActiveId) {
          localStorage.setItem("obsidian-ai-active-project", newActiveId);
        } else {
          localStorage.removeItem("obsidian-ai-active-project");
        }
      }
    },
    [vaultProjects, activeProjectId]
  );

  // PARA Project handlers
  const handleParaRootChange = useCallback((path: string | null) => {
    setParaRoot(path);
    if (path) {
      localStorage.setItem("obsidian-ai-para-root", path);
    } else {
      localStorage.removeItem("obsidian-ai-para-root");
    }
  }, []);

  const handleUpdateParaProgress = useCallback(
    (projectId: string, progress: number) => {
      setParaProjects((prev) => {
        const updatedProjects = prev.map((p) =>
          p.id === projectId ? { ...p, progress } : p
        );
        localStorage.setItem(
          "obsidian-ai-para-projects",
          JSON.stringify(updatedProjects)
        );
        return updatedProjects;
      });
    },
    []
  );

  // Topic and Conversation handlers
  const handleCreateTopic = useCallback((name: string, description?: string) => {
    const newTopic: Topic = {
      id: crypto.randomUUID(),
      name,
      description,
      createdAt: new Date(),
      conversationCount: 0,
    };
    const updatedTopics = [newTopic, ...topics];
    setTopics(updatedTopics);
    localStorage.setItem("obsidian-ai-topics", JSON.stringify(updatedTopics));
  }, [topics]);

  const handleUpdateTopic = useCallback(
    (topicId: string, name: string, description?: string) => {
      const updatedTopics = topics.map((t) =>
        t.id === topicId ? { ...t, name, description } : t
      );
      setTopics(updatedTopics);
      localStorage.setItem("obsidian-ai-topics", JSON.stringify(updatedTopics));
    },
    [topics]
  );

  const handleDeleteTopic = useCallback(
    (topicId: string) => {
      const updatedTopics = topics.filter((t) => t.id !== topicId);
      setTopics(updatedTopics);
      localStorage.setItem("obsidian-ai-topics", JSON.stringify(updatedTopics));

      // Move conversations in this topic to uncategorized
      const updatedConversations = conversations.map((c) =>
        c.topicId === topicId ? { ...c, topicId: null } : c
      );
      setConversations(updatedConversations);
      localStorage.setItem("obsidian-ai-conversations", JSON.stringify(updatedConversations));
    },
    [topics, conversations]
  );

  const handleCreateConversation = useCallback((topicId: string | null) => {
    const newConversation: Conversation = {
      id: crypto.randomUUID(),
      title: `새 대화 ${conversations.length + 1}`,
      createdAt: new Date(),
      updatedAt: new Date(),
      messageCount: 0,
      topicId,
    };
    const updatedConversations = [newConversation, ...conversations];
    setConversations(updatedConversations);
    localStorage.setItem("obsidian-ai-conversations", JSON.stringify(updatedConversations));
    setActiveConversationId(newConversation.id);
    setCurrentView("chat");

    // Update topic conversation count
    if (topicId) {
      const updatedTopics = topics.map((t) =>
        t.id === topicId ? { ...t, conversationCount: t.conversationCount + 1 } : t
      );
      setTopics(updatedTopics);
      localStorage.setItem("obsidian-ai-topics", JSON.stringify(updatedTopics));
    }
  }, [conversations, topics]);

  const handleSelectConversation = useCallback((conversationId: string) => {
    setActiveConversationId(conversationId);
    setCurrentView("chat");
    // TODO: Load conversation messages from storage
  }, []);

  const handleMoveConversation = useCallback(
    (conversationId: string, newTopicId: string | null) => {
      const conversation = conversations.find((c) => c.id === conversationId);
      if (!conversation) return;

      const oldTopicId = conversation.topicId;
      
      const updatedConversations = conversations.map((c) =>
        c.id === conversationId ? { ...c, topicId: newTopicId } : c
      );
      setConversations(updatedConversations);
      localStorage.setItem("obsidian-ai-conversations", JSON.stringify(updatedConversations));

      // Update topic conversation counts
      const updatedTopics = topics.map((t) => {
        if (t.id === oldTopicId) {
          return { ...t, conversationCount: Math.max(0, t.conversationCount - 1) };
        }
        if (t.id === newTopicId) {
          return { ...t, conversationCount: t.conversationCount + 1 };
        }
        return t;
      });
      setTopics(updatedTopics);
      localStorage.setItem("obsidian-ai-topics", JSON.stringify(updatedTopics));
    },
    [conversations, topics]
  );

  const handleDeleteConversation = useCallback(
    (conversationId: string) => {
      const conversation = conversations.find((c) => c.id === conversationId);
      const updatedConversations = conversations.filter((c) => c.id !== conversationId);
      setConversations(updatedConversations);
      localStorage.setItem("obsidian-ai-conversations", JSON.stringify(updatedConversations));

      if (activeConversationId === conversationId) {
        setActiveConversationId(null);
      }

      // Update topic conversation count
      if (conversation?.topicId) {
        const updatedTopics = topics.map((t) =>
          t.id === conversation.topicId
            ? { ...t, conversationCount: Math.max(0, t.conversationCount - 1) }
            : t
        );
        setTopics(updatedTopics);
        localStorage.setItem(
          "obsidian-ai-topics",
          JSON.stringify(updatedTopics)
        );
      }
    },
    [conversations, activeConversationId, topics]
  );

  const { messages, sendMessage, status } = useChat({
    transport: new DefaultChatTransport({
      api: "/api/chat",
      body: {
        session_id: activeConversationId,
        settings: {
          llmProvider: settings.llmProvider,
          llmModel: settings.llmModel,
          apiKey: settings.llmApiKey,
        },
      },
    }),
  });

  const isLoading = status === "streaming" || status === "submitted";

  const chatMessages: Message[] = messages.map((msg) => {
    const content = msg.parts
      .filter((p): p is { type: "text"; text: string } => p.type === "text")
      .map((p) => p.text)
      .join("");

    return {
      id: msg.id,
      role: msg.role as "user" | "assistant",
      content,
      timestamp: new Date(),
    };
  });

  const handleSendMessage = useCallback(
    (content: string) => {
      sendMessage({ text: content });

      if (activeConversationId) {
        const updatedConversations = conversations.map((c) =>
          c.id === activeConversationId
            ? {
                ...c,
                updatedAt: new Date(),
                messageCount: c.messageCount + 1,
                preview: content.slice(0, 100),
                title: c.messageCount === 0 ? content.slice(0, 50) : c.title,
              }
            : c
        );
        setConversations(updatedConversations);
        localStorage.setItem(
          "obsidian-ai-conversations",
          JSON.stringify(updatedConversations)
        );
      }
    },
    [sendMessage, activeConversationId, conversations]
  );

  const _handleNewChat = useCallback(() => {
    setConversations([]);
    setActiveConversationId(null);
  }, [setConversations]);

  const handleReindex = useCallback(async () => {
    if (!settings.vaultPath) {
      alert("먼저 설정에서 Vault 경로를 입력해주세요.");
      return;
    }

    const embeddingApiKey = settings.embeddingApiKey || settings.llmApiKey;

    try {
      setEmbeddingState("indexing");
      await triggerSync({
        embeddingApiKey,
        includePaths: embeddingScope.length > 0 ? embeddingScope : undefined,
      });
      setEmbeddingState("ready");

      if (activeProjectId) {
        const updatedProjects = vaultProjects.map((p) =>
          p.id === activeProjectId
            ? { ...p, lastIndexed: new Date() }
            : p
        );
        setVaultProjects(updatedProjects);
        localStorage.setItem(
          "obsidian-ai-vault-projects",
          JSON.stringify(updatedProjects)
        );
      }
    } catch (error) {
      console.error("Indexing failed:", error);
      setEmbeddingState("idle");
      alert("인덱싱에 실패했습니다. 백엔드 상태를 확인해주세요.");
    }
  }, [activeProjectId, embeddingScope, settings, vaultProjects]);

  const activeProject = vaultProjects.find((p) => p.id === activeProjectId);
  const activeTopic = topics.find((t) => t.id === activeTopicId);

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-sidebar flex flex-col">
        {/* Logo */}
        <div className="p-4 border-b border-sidebar-border">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
              <BookOpen className="h-4 w-4 text-primary" />
            </div>
            <span className="font-semibold text-sidebar-foreground">
              Obsidian AI
            </span>
          </div>
        </div>

        {/* Main Menu */}
        <div className="p-3 flex-1">
          <MainMenu
            currentView={currentView}
            onViewChange={setCurrentView}
            hasActiveChat={messages.length > 0}
          />
        </div>

        {/* Active Project Info */}
        {activeProject && (
          <div className="px-3 pb-2">
            <div className="p-2 rounded-lg bg-sidebar-accent/50 border border-sidebar-border">
              <p className="text-xs text-muted-foreground mb-1">활성 Vault</p>
              <p className="text-sm font-medium text-sidebar-foreground truncate">
                {activeProject.name}
              </p>
            </div>
          </div>
        )}

        {/* Settings */}
        <div className="p-3 border-t border-sidebar-border">
          <div className="flex items-center justify-between">
            <EmbeddingStatus
              state={embeddingState}
              progress={_embeddingProgress}
              totalFiles={activeProject?.fileCount || 0}
              processedFiles={Math.floor(
                (_embeddingProgress / 100) * (activeProject?.fileCount || 0)
              )}
              onReindex={handleReindex}
            />
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowEmbeddingScopeModal(true)}
                title="Embedding Scope"
              >
                <Database className="h-4 w-4" />
              </Button>
              <SettingsPanel
                settings={settings}
                onSettingsChange={handleSettingsChange}
                onProjectCreated={handleProjectCreated}
              />
            </div>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col min-w-0">
        {currentView === "chat" && (
          <>
            {/* Header */}
            <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-sm">
              <div className="flex items-center gap-2">
                {activeTopic && (
                  <span className="text-sm font-medium text-foreground mr-2">
                    {activeTopic.name}
                  </span>
                )}
                <span className="text-sm text-muted-foreground">
                  {settings.llmProvider === "ollama"
                    ? "Local"
                    : settings.llmProvider.charAt(0).toUpperCase() +
                      settings.llmProvider.slice(1)}
                </span>
                <span className="text-xs px-2 py-0.5 rounded-md bg-muted text-muted-foreground">
                  {settings.llmModel}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {!settings.llmApiKey && settings.llmProvider !== "ollama" && (
                  <span className="text-xs text-destructive">
                    LLM API 키가 필요합니다
                  </span>
                )}
              </div>
            </header>

            {/* Chat Interface */}
            <ChatInterface
              isLoading={isLoading}
              onSendMessage={handleSendMessage}
              messages={chatMessages}
            />
          </>
        )}

        {currentView === "para" && (
          <ParaDashboard
            projects={paraProjects}
            onUpdateProgress={handleUpdateParaProgress}
            paraRoot={paraRoot}
            onParaRootChange={handleParaRootChange}
          />
        )}

        {currentView === "review" && (
          <ReviewEngine />
        )}

        {currentView === "topics" && (
          <TopicManager
            topics={topics}
            conversations={conversations}
            activeConversationId={activeConversationId}
            onSelectConversation={handleSelectConversation}
            onCreateTopic={handleCreateTopic}
            onUpdateTopic={handleUpdateTopic}
            onDeleteTopic={handleDeleteTopic}
            onCreateConversation={handleCreateConversation}
            onMoveConversation={handleMoveConversation}
            onDeleteConversation={handleDeleteConversation}
          />
        )}
      </main>
      {/* Modals */}
      <EmbeddingScopeModal
        open={showEmbeddingScopeModal}
        onOpenChange={setShowEmbeddingScopeModal}
        projectId={activeProject?.backendId}
        onScopeChange={setEmbeddingScope}
      />
    </div>
  );
}
