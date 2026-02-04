"use client";

import { useState, useEffect } from "react";
import { Character, CharacterMood } from "@/components/character";
import { cn } from "@/lib/utils";
import { CheckCircle2, Clock, RotateCw, BookOpen } from "lucide-react";
import { motion } from "framer-motion";

export interface ReviewItem {
  id: string;
  title: string;
  filePath: string;
  dueDate: Date;
  daysSinceCreated: number; // Ebbinghaus day (1, 3, 7, 14, 30...)
  isCompleted: boolean;
  isOverdue: boolean;
}

// Mock data generator
const generateReviewItems = (): ReviewItem[] => {
  const today = new Date();
  
  return [
    {
      id: "1",
      title: "양자역학 기초.md",
      filePath: "물리 공부/양자역학 기초.md",
      dueDate: today,
      daysSinceCreated: 3,
      isCompleted: false,
      isOverdue: false,
    },
    {
      id: "2",
      title: "AI 트렌드 2025.md",
      filePath: "블로그 글 작성/AI 트렌드 2025.md",
      dueDate: new Date(today.getTime() - 24 * 60 * 60 * 1000), // Yesterday
      daysSinceCreated: 7,
      isCompleted: false,
      isOverdue: true,
    },
    {
      id: "3",
      title: "React Hooks 정리.md",
      filePath: "개발/React Hooks 정리.md",
      dueDate: today,
      daysSinceCreated: 1,
      isCompleted: false,
      isOverdue: false,
    },
    {
      id: "4",
      title: "사피엔스.md",
      filePath: "독서 노트/사피엔스.md",
      dueDate: new Date(today.getTime() - 48 * 60 * 60 * 1000), // 2 days ago
      daysSinceCreated: 30,
      isCompleted: false,
      isOverdue: true,
    },
  ];
};

export function ReviewEngine() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [characterMood, setCharacterMood] = useState<CharacterMood>("default");
  const [characterMessage, setCharacterMessage] = useState("");

  useEffect(() => {
    // Load mock data
    const data = generateReviewItems();
    setItems(data);
    updateCharacterState(data);
  }, []);

  const updateCharacterState = (currentItems: ReviewItem[]) => {
    const incomplete = currentItems.filter((i) => !i.isCompleted);
    const overdue = incomplete.filter((i) => i.isOverdue);

    if (incomplete.length === 0) {
      if (currentItems.length > 0) {
        setCharacterMood("happy");
        setCharacterMessage("오늘 복습 완료!");
      } else {
        setCharacterMood("default");
        setCharacterMessage("오늘은 쉬는 날!");
      }
    } else if (overdue.length > 0) {
      setCharacterMood("sad");
      setCharacterMessage(`밀린 복습 ${overdue.length}개...`);
    } else {
      setCharacterMood("loading");
      setCharacterMessage(`오늘 ${incomplete.length}개 복습해요`);
    }
  };

  const handleComplete = (id: string) => {
    const newItems = items.map((item) =>
      item.id === id ? { ...item, isCompleted: true } : item
    );
    setItems(newItems);
    updateCharacterState(newItems);
  };

  const todayItems = items.filter((i) => !i.isOverdue && !i.isCompleted);
  const overdueItems = items.filter((i) => i.isOverdue && !i.isCompleted);
  const completedItems = items.filter((i) => i.isCompleted);

  return (
    <div className="flex flex-col h-full bg-background relative overflow-hidden">
      {/* Header Section */}
      <div className="p-8 pb-4 flex items-end justify-between z-10">
        <div>
          <h1 className="text-3xl font-bold mb-2">복습 엔진</h1>
          <p className="text-muted-foreground">
            에빙하우스 망각곡선 기반 복습 시스템
          </p>
        </div>
        <div className="flex items-center gap-4">
          <div className="text-right">
            <p className="text-sm font-medium text-muted-foreground">진행률</p>
            <p className="text-2xl font-bold font-mono">
              {items.length > 0
                ? Math.round((completedItems.length / items.length) * 100)
                : 0}
              %
            </p>
          </div>
          <Character
            mood={characterMood}
            size="md"
            message={characterMessage}
            className="mb-[-10px]"
          />
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto p-8 pt-0">
        <div className="max-w-4xl mx-auto space-y-8">
          
          {/* Action Button */}
          {items.some(i => !i.isCompleted) && (
            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className="w-full py-4 bg-primary text-primary-foreground text-xl font-bold rounded-xl neo-border neo-shadow flex items-center justify-center gap-3 transition-transform"
            >
              <RotateCw className="w-6 h-6 animate-spin-slow" />
              랜덤 복습 시작
            </motion.button>
          )}

          {/* Overdue Section */}
          {overdueItems.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold flex items-center gap-2 text-destructive">
                <Clock className="w-5 h-5" />
                밀린 복습 ({overdueItems.length})
              </h2>
              <div className="grid gap-3">
                {overdueItems.map((item) => (
                  <ReviewCard key={item.id} item={item} onComplete={handleComplete} />
                ))}
              </div>
            </div>
          )}

          {/* Today's Review Section */}
          {todayItems.length > 0 && (
            <div className="space-y-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <BookOpen className="w-5 h-5" />
                오늘의 복습 ({todayItems.length})
              </h2>
              <div className="grid gap-3">
                {todayItems.map((item) => (
                  <ReviewCard key={item.id} item={item} onComplete={handleComplete} />
                ))}
              </div>
            </div>
          )}

          {/* Completed Section */}
          {completedItems.length > 0 && (
            <div className="space-y-4 opacity-60">
              <h2 className="text-xl font-bold flex items-center gap-2 text-muted-foreground">
                <CheckCircle2 className="w-5 h-5" />
                완료됨 ({completedItems.length})
              </h2>
              <div className="grid gap-3">
                {completedItems.map((item) => (
                  <ReviewCard key={item.id} item={item} onComplete={handleComplete} />
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ReviewCard({ item, onComplete }: { item: ReviewItem; onComplete: (id: string) => void }) {
  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn(
        "p-4 rounded-xl border-2 flex items-center justify-between group transition-all",
        item.isCompleted 
          ? "bg-muted border-transparent" 
          : "bg-card border-border hover:border-primary hover:shadow-md"
      )}
    >
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h3 className={cn("font-bold text-lg", item.isCompleted && "line-through text-muted-foreground")}>
            {item.title}
          </h3>
          {!item.isCompleted && item.isOverdue && (
            <span className="text-[10px] bg-destructive/10 text-destructive px-2 py-0.5 rounded-full font-bold">
              OVERDUE
            </span>
          )}
          <span className="text-[10px] bg-secondary text-secondary-foreground px-2 py-0.5 rounded-full font-bold">
            {item.daysSinceCreated}일차
          </span>
        </div>
        <p className="text-sm text-muted-foreground">{item.filePath}</p>
      </div>

      <button
        onClick={() => !item.isCompleted && onComplete(item.id)}
        disabled={item.isCompleted}
        className={cn(
          "w-10 h-10 rounded-full flex items-center justify-center border-2 transition-all",
          item.isCompleted
            ? "bg-primary border-primary text-primary-foreground"
            : "border-muted-foreground/30 hover:border-primary hover:text-primary"
        )}
      >
        {item.isCompleted ? <CheckCircle2 className="w-6 h-6" /> : <div className="w-4 h-4 rounded-full bg-current opacity-20" />}
      </button>
    </motion.div>
  );
}
