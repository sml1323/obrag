"use client";

import { useState } from "react";
import {
  FolderKanban,
  MessageSquare,
  Library,
  ChevronRight,
  Database,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type MenuView = "chat" | "para" | "topics";

interface MainMenuProps {
  currentView: MenuView;
  onViewChange: (view: MenuView) => void;
  hasActiveChat: boolean;
}

const menuItems = [
  {
    id: "para" as MenuView,
    label: "PARA 대시보드",
    description: "프로젝트 진척도 관리",
    icon: FolderKanban,
  },
  {
    id: "chat" as MenuView,
    label: "대화하기",
    description: "AI와 실시간 대화",
    icon: MessageSquare,
  },
  {
    id: "topics" as MenuView,
    label: "대화 기록",
    description: "주제별 대화 세션 관리",
    icon: Library,
  },
];

export function MainMenu({
  currentView,
  onViewChange,
  hasActiveChat,
}: MainMenuProps) {
  const [hoveredItem, setHoveredItem] = useState<MenuView | null>(null);

  return (
    <nav className="flex flex-col gap-1">
      {menuItems.map((item) => {
        const Icon = item.icon;
        const isActive = currentView === item.id;
        const isHovered = hoveredItem === item.id;

        return (
          <button
            key={item.id}
            onClick={() => onViewChange(item.id)}
            onMouseEnter={() => setHoveredItem(item.id)}
            onMouseLeave={() => setHoveredItem(null)}
            className={cn(
              "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all duration-200",
              isActive
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground"
            )}
          >
            <div
              className={cn(
                "w-8 h-8 rounded-lg flex items-center justify-center transition-colors",
                isActive
                  ? "bg-primary/20 text-primary"
                  : "bg-sidebar-accent/50 text-sidebar-foreground/60"
              )}
            >
              <Icon className="h-4 w-4" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="font-medium text-sm">{item.label}</span>
                {item.id === "chat" && hasActiveChat && (
                  <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                )}
              </div>
              <p className="text-xs text-muted-foreground truncate">
                {item.description}
              </p>
            </div>
            <ChevronRight
              className={cn(
                "h-4 w-4 text-muted-foreground/50 transition-transform",
                (isActive || isHovered) && "translate-x-0.5"
              )}
            />
          </button>
        );
      })}
    </nav>
  );
}
