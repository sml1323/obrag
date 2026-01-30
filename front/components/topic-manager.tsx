"use client";

import { useState } from "react";
import {
  MessageSquare,
  Plus,
  Trash2,
  Calendar,
  ChevronLeft,
  Search,
  FolderOpen,
  Edit2,
  Check,
  X,
  MoreVertical,
  Folder,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

// 개별 대화 세션
export interface Conversation {
  id: string;
  title: string;
  preview?: string;
  createdAt: Date;
  updatedAt: Date;
  messageCount: number;
  topicId: string | null; // null이면 미분류
}

// 주제 (대화를 그룹화)
export interface Topic {
  id: string;
  name: string;
  description?: string;
  color?: string;
  createdAt: Date;
  conversationCount: number;
}

interface TopicManagerProps {
  topics: Topic[];
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelectConversation: (conversationId: string) => void;
  onCreateTopic: (name: string, description?: string) => void;
  onUpdateTopic: (topicId: string, name: string, description?: string) => void;
  onDeleteTopic: (topicId: string) => void;
  onCreateConversation: (topicId: string | null) => void;
  onMoveConversation: (conversationId: string, newTopicId: string | null) => void;
  onDeleteConversation: (conversationId: string) => void;
}

type ViewMode = "topics" | "conversations";

export function TopicManager({
  topics,
  conversations,
  activeConversationId,
  onSelectConversation,
  onCreateTopic,
  onUpdateTopic,
  onDeleteTopic,
  onCreateConversation,
  onMoveConversation,
  onDeleteConversation,
}: TopicManagerProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("topics");
  const [selectedTopicId, setSelectedTopicId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [showNewTopicDialog, setShowNewTopicDialog] = useState(false);
  const [showMoveDialog, setShowMoveDialog] = useState(false);
  const [selectedConversationForMove, setSelectedConversationForMove] =
    useState<string | null>(null);
  const [newTopicName, setNewTopicName] = useState("");
  const [newTopicDescription, setNewTopicDescription] = useState("");
  const [editingTopicId, setEditingTopicId] = useState<string | null>(null);
  const [editTopicName, setEditTopicName] = useState("");

  const selectedTopic = topics.find((t) => t.id === selectedTopicId);

  // 주제별 대화 필터링
  const getConversationsByTopic = (topicId: string | null) => {
    return conversations.filter((conv) => {
      const matchesTopic = conv.topicId === topicId;
      const matchesSearch =
        conv.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        conv.preview?.toLowerCase().includes(searchQuery.toLowerCase());
      return matchesTopic && matchesSearch;
    });
  };

  const displayedConversations =
    viewMode === "conversations" && selectedTopicId !== null
      ? getConversationsByTopic(selectedTopicId)
      : viewMode === "conversations" && selectedTopicId === null
        ? getConversationsByTopic(null)
        : [];

  const handleCreateTopic = () => {
    if (!newTopicName.trim()) return;
    onCreateTopic(newTopicName, newTopicDescription);
    setNewTopicName("");
    setNewTopicDescription("");
    setShowNewTopicDialog(false);
  };

  const handleEditTopic = (topicId: string) => {
    const topic = topics.find((t) => t.id === topicId);
    if (!topic) return;
    if (!editTopicName.trim()) {
      setEditingTopicId(null);
      return;
    }
    onUpdateTopic(topicId, editTopicName, topic.description);
    setEditingTopicId(null);
  };

  const handleSelectTopic = (topicId: string | null) => {
    setSelectedTopicId(topicId);
    setViewMode("conversations");
    setSearchQuery("");
  };

  const handleBackToTopics = () => {
    setViewMode("topics");
    setSelectedTopicId(null);
    setSearchQuery("");
  };

  const handleMoveConversation = (targetTopicId: string | null) => {
    if (selectedConversationForMove) {
      onMoveConversation(selectedConversationForMove, targetTopicId);
      setShowMoveDialog(false);
      setSelectedConversationForMove(null);
    }
  };

  const formatDate = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - new Date(date).getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) return "오늘";
    if (days === 1) return "어제";
    if (days < 7) return `${days}일 전`;
    if (days < 30) return `${Math.floor(days / 7)}주 전`;
    return `${Math.floor(days / 30)}개월 전`;
  };

  const uncategorizedCount = conversations.filter((c) => c.topicId === null).length;

  // 주제 목록 뷰
  if (viewMode === "topics") {
    return (
      <div className="flex flex-col h-full bg-background">
        {/* Header */}
        <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-sm shrink-0">
          <div className="flex items-center gap-2">
            <Folder className="h-5 w-5 text-primary" />
            <h2 className="text-lg font-semibold text-foreground">주제</h2>
          </div>
          <Button
            onClick={() => setShowNewTopicDialog(true)}
            size="sm"
            className="gap-2"
          >
            <Plus className="h-4 w-4" />
            새 주제
          </Button>
        </header>

        {/* Topic Grid */}
        <ScrollArea className="flex-1 p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* 미분류 대화 */}
            {uncategorizedCount > 0 && (
              <button
                onClick={() => handleSelectTopic(null)}
                className="group relative p-6 rounded-xl border-2 border-dashed border-border hover:border-primary bg-card hover:bg-accent/50 transition-all text-left"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="p-2 rounded-lg bg-muted group-hover:bg-primary/20 transition-colors">
                    <MessageSquare className="h-5 w-5 text-muted-foreground group-hover:text-primary transition-colors" />
                  </div>
                </div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  미분류 대화
                </h3>
                <p className="text-sm text-muted-foreground mb-3">
                  주제가 지정되지 않은 대화
                </p>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <MessageSquare className="h-3 w-3" />
                  <span>{uncategorizedCount}개 대화</span>
                </div>
              </button>
            )}

            {/* 주제 목록 */}
            {topics.map((topic) => (
              <div
                key={topic.id}
                className="group relative p-6 rounded-xl border border-border hover:border-primary bg-card hover:shadow-md transition-all"
              >
                <div className="flex items-start justify-between mb-3">
                  <button
                    onClick={() => handleSelectTopic(topic.id)}
                    className="flex-1 text-left"
                  >
                    <div className="p-2 rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors w-fit">
                      <FolderOpen className="h-5 w-5 text-primary" />
                    </div>
                  </button>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem
                        onClick={() => {
                          setEditingTopicId(topic.id);
                          setEditTopicName(topic.name);
                        }}
                      >
                        <Edit2 className="h-4 w-4 mr-2" />
                        이름 변경
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => onDeleteTopic(topic.id)}
                        className="text-destructive"
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        삭제
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                <button
                  onClick={() => handleSelectTopic(topic.id)}
                  className="w-full text-left"
                >
                  {editingTopicId === topic.id ? (
                    <div className="flex items-center gap-2 mb-2">
                      <Input
                        value={editTopicName}
                        onChange={(e) => setEditTopicName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") handleEditTopic(topic.id);
                          if (e.key === "Escape") setEditingTopicId(null);
                        }}
                        className="h-8 text-sm"
                        autoFocus
                      />
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleEditTopic(topic.id);
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <Check className="h-4 w-4" />
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                          e.stopPropagation();
                          setEditingTopicId(null);
                        }}
                        className="h-8 w-8 p-0"
                      >
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ) : (
                    <h3 className="text-base font-semibold text-foreground mb-1 group-hover:text-primary transition-colors">
                      {topic.name}
                    </h3>
                  )}
                  {topic.description && (
                    <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                      {topic.description}
                    </p>
                  )}
                  <div className="flex items-center gap-2 text-xs text-muted-foreground">
                    <MessageSquare className="h-3 w-3" />
                    <span>{topic.conversationCount}개 대화</span>
                  </div>
                </button>
              </div>
            ))}
          </div>

          {topics.length === 0 && uncategorizedCount === 0 && (
            <div className="flex flex-col items-center justify-center h-[400px] text-center">
              <div className="p-4 rounded-full bg-muted/50 mb-4">
                <Folder className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground mb-4">
                아직 주제가 없습니다
              </p>
              <Button onClick={() => setShowNewTopicDialog(true)}>
                <Plus className="h-4 w-4 mr-2" />
                첫 주제 만들기
              </Button>
            </div>
          )}
        </ScrollArea>

        {/* New Topic Dialog */}
        <Dialog open={showNewTopicDialog} onOpenChange={setShowNewTopicDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>새 주제 만들기</DialogTitle>
              <DialogDescription>
                대화를 그룹화할 주제를 만듭니다.
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4 py-4">
              <div className="space-y-2">
                <Label htmlFor="topicName">주제 이름</Label>
                <Input
                  id="topicName"
                  placeholder="예: 프로젝트 기획"
                  value={newTopicName}
                  onChange={(e) => setNewTopicName(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleCreateTopic()}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="topicDesc">설명 (선택)</Label>
                <Input
                  id="topicDesc"
                  placeholder="주제에 대한 간단한 설명"
                  value={newTopicDescription}
                  onChange={(e) => setNewTopicDescription(e.target.value)}
                />
              </div>
            </div>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowNewTopicDialog(false)}
              >
                취소
              </Button>
              <Button onClick={handleCreateTopic}>만들기</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>
    );
  }

  // 대화 목록 뷰
  return (
    <div className="flex flex-col h-full bg-background">
      {/* Header */}
      <header className="h-14 border-b border-border flex items-center justify-between px-4 bg-background/80 backdrop-blur-sm shrink-0">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleBackToTopics}
            className="gap-2"
          >
            <ChevronLeft className="h-4 w-4" />
            뒤로
          </Button>
          <div className="flex items-center gap-2">
            {selectedTopicId ? (
              <>
                <FolderOpen className="h-5 w-5 text-primary" />
                <h2 className="text-lg font-semibold text-foreground">
                  {selectedTopic?.name || "주제"}
                </h2>
              </>
            ) : (
              <>
                <MessageSquare className="h-5 w-5 text-muted-foreground" />
                <h2 className="text-lg font-semibold text-foreground">
                  미분류 대화
                </h2>
              </>
            )}
          </div>
        </div>
        <Button
          onClick={() => onCreateConversation(selectedTopicId)}
          size="sm"
          className="gap-2"
        >
          <Plus className="h-4 w-4" />
          새 대화
        </Button>
      </header>

      {/* Search */}
      <div className="p-4 border-b border-border shrink-0">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="대화 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Conversation List */}
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-2">
          {displayedConversations.map((conv) => (
            <div
              key={conv.id}
              className={cn(
                "group relative p-4 rounded-lg border border-border hover:border-primary bg-card hover:shadow-sm transition-all cursor-pointer",
                activeConversationId === conv.id &&
                  "border-primary bg-accent shadow-sm"
              )}
            >
              <button
                onClick={() => onSelectConversation(conv.id)}
                className="w-full text-left"
              >
                <div className="flex items-start justify-between mb-2">
                  <h3 className="text-sm font-semibold text-foreground line-clamp-1 flex-1 pr-2">
                    {conv.title}
                  </h3>
                  <span className="text-xs text-muted-foreground shrink-0">
                    {formatDate(conv.updatedAt)}
                  </span>
                </div>
                {conv.preview && (
                  <p className="text-xs text-muted-foreground line-clamp-2 mb-2">
                    {conv.preview}
                  </p>
                )}
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <MessageSquare className="h-3 w-3" />
                    {conv.messageCount}
                  </span>
                  <span className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {formatDate(conv.createdAt)}
                  </span>
                </div>
              </button>

              <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem
                      onClick={() => {
                        setSelectedConversationForMove(conv.id);
                        setShowMoveDialog(true);
                      }}
                    >
                      <FolderOpen className="h-4 w-4 mr-2" />
                      다른 주제로 이동
                    </DropdownMenuItem>
                    <DropdownMenuItem
                      onClick={() => onDeleteConversation(conv.id)}
                      className="text-destructive"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      삭제
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}

          {displayedConversations.length === 0 && (
            <div className="flex flex-col items-center justify-center h-[400px] text-center">
              <div className="p-4 rounded-full bg-muted/50 mb-4">
                <MessageSquare className="h-8 w-8 text-muted-foreground" />
              </div>
              <p className="text-muted-foreground mb-4">
                {searchQuery
                  ? "검색 결과가 없습니다"
                  : "아직 대화가 없습니다"}
              </p>
              <Button onClick={() => onCreateConversation(selectedTopicId)}>
                <Plus className="h-4 w-4 mr-2" />
                새 대화 시작
              </Button>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Move Dialog */}
      <Dialog open={showMoveDialog} onOpenChange={setShowMoveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>다른 주제로 이동</DialogTitle>
            <DialogDescription>
              대화를 다른 주제로 이동합니다.
            </DialogDescription>
          </DialogHeader>
          <ScrollArea className="max-h-[300px] py-4">
            <div className="space-y-2">
              <Button
                variant="outline"
                className="w-full justify-start bg-transparent"
                onClick={() => handleMoveConversation(null)}
              >
                <MessageSquare className="h-4 w-4 mr-2" />
                미분류
              </Button>
              {topics.map((topic) => (
                <Button
                  key={topic.id}
                  variant="outline"
                  className="w-full justify-start bg-transparent"
                  onClick={() => handleMoveConversation(topic.id)}
                  disabled={topic.id === selectedTopicId}
                >
                  <FolderOpen className="h-4 w-4 mr-2" />
                  {topic.name}
                </Button>
              ))}
            </div>
          </ScrollArea>
        </DialogContent>
      </Dialog>
    </div>
  );
}
