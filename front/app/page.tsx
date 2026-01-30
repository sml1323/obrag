"use client";

import { useState, useEffect, useCallback } from "react";
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { BookOpen } from "lucide-react";
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
import { MainMenu, type MenuView } from "@/components/main-menu";
import { TopicManager, type Topic, type Conversation } from "@/components/topic-manager";
import {
  ParaDashboard,
  type ParaProject,
  type ParaFile,
} from "@/components/para-dashboard";
import { ProjectManager, type Project as VaultProject } from "@/components/project-manager";
import { getProjects, updateProjectProgress, type Project } from "@/lib/api-client";

// Demo data removed

export default function Home() {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings);
  const [embeddingState, setEmbeddingState] = useState<EmbeddingState>("idle");
  const [embeddingProgress, setEmbeddingProgress] = useState(0);
  const [currentView, setCurrentView] = useState<MenuView>("chat");

  // Vault projects state (for embedding)
  const [vaultProjects, setVaultProjects] = useState<VaultProject[]>([]);
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);

  // PARA projects state
  const [paraProjects, setParaProjects] = useState<ParaProject[]>([]);

  // Topics and Conversations state
  const [topics, setTopics] = useState<Topic[]>([]);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeTopicId, setActiveTopicId] = useState<string | null>(null);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Load data from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem("obsidian-ai-settings");
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings));
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

    // Load active projects from API
    getProjects()
      .then((projects) => {
        const mappedProjects: ParaProject[] = projects.map((p) => ({
          id: String(p.id),
          name: p.name,
          progress: p.progress,
          lastModified: new Date(p.last_modified_at),
          fileCount: p.file_count,
          files: [], // Files not supported in list API yet
        }));
        setParaProjects(mappedProjects);
      })
      .catch((err) => console.error("Failed to load projects", err));

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
  }, []);

  // Save settings to localStorage
  const handleSettingsChange = useCallback((newSettings: AppSettings) => {
    setSettings(newSettings);
    localStorage.setItem("obsidian-ai-settings", JSON.stringify(newSettings));
  }, []);

  // Vault Project handlers
  const handleAddProject = useCallback(
    (projectData: Omit<VaultProject, "id" | "createdAt">) => {
      const newProject: VaultProject = {
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

  const handleSelectProject = useCallback((projectId: string) => {
    setActiveProjectId(projectId);
    localStorage.setItem("obsidian-ai-active-project", projectId);
  }, []);

  const handleDeleteProject = useCallback(
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

  const handleReindexProject = useCallback(
    (projectId: string) => {
      setEmbeddingState("indexing");
      setEmbeddingProgress(0);

      const interval = setInterval(() => {
        setEmbeddingProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval);
            setEmbeddingState("ready");

            // Update project's lastIndexed
            const updatedProjects = vaultProjects.map((p) =>
              p.id === projectId
                ? { ...p, lastIndexed: new Date(), fileCount: 42 }
                : p
            );
            setVaultProjects(updatedProjects);
            localStorage.setItem(
              "obsidian-ai-vault-projects",
              JSON.stringify(updatedProjects)
            );

            return 100;
          }
          return prev + Math.random() * 15;
        });
      }, 500);
    },
    [vaultProjects]
  );

  // PARA Project handlers
  const handleUpdateParaProgress = useCallback(
    async (projectId: string, progress: number) => {
      try {
        await updateProjectProgress(Number(projectId), progress);
        
        // Optimistic update
        setParaProjects((prev) =>
          prev.map((p) => (p.id === projectId ? { ...p, progress } : p))
        );
      } catch (err) {
        console.error("Failed to update project progress", err);
      }
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
      prepareSendMessagesRequest: ({ id, messages }) => ({
        body: {
          messages,
          id,
          settings: {
            llmProvider: settings.llmProvider,
            llmModel: settings.llmModel,
            apiKey: settings.llmApiKey,
          },
        },
      }),
    }),
  });

  const isLoading = status === "streaming" || status === "submitted";

  // Convert useChat messages to our Message format
  const chatMessages: Message[] = messages.map((msg) => ({
    id: msg.id,
    role: msg.role as "user" | "assistant",
    content:
      msg.parts
        ?.filter((p) => p.type === "text")
        .map((p) => (p as { type: "text"; text: string }).text)
        .join("") || "",
    timestamp: new Date(),
  }));

  const handleSendMessage = useCallback(
    (content: string) => {
      sendMessage({ text: content });

      // Update conversation if we have an active one
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

  const handleNewChat = useCallback(() => {
    setConversations([]);
    setActiveConversationId(null);
  }, [setConversations]);

  const handleReindex = useCallback(async () => {
    if (activeProjectId) {
      handleReindexProject(activeProjectId);
    } else {
      alert("먼저 Vault 설정에서 프로젝트를 선택해주세요.");
    }
  }, [activeProjectId, handleReindexProject]);

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
              progress={embeddingProgress}
              totalFiles={activeProject?.fileCount || 0}
              processedFiles={Math.floor(
                (embeddingProgress / 100) * (activeProject?.fileCount || 0)
              )}
              onReindex={handleReindex}
            />
            <SettingsPanel
              settings={settings}
              onSettingsChange={handleSettingsChange}
            />
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
                    {activeTopic.title}
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
          />
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
    </div>
  );
}
