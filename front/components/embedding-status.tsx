"use client";

import { useState } from "react";
import { Database, RefreshCw, CheckCircle, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Character } from "./character";
import { cn } from "@/lib/utils";

export type EmbeddingState = "idle" | "indexing" | "ready" | "error";

interface EmbeddingStatusProps {
  state: EmbeddingState;
  progress?: number;
  totalFiles?: number;
  processedFiles?: number;
  onReindex: () => void;
}

export function EmbeddingStatus({
  state,
  progress = 0,
  totalFiles = 0,
  processedFiles = 0,
  onReindex,
}: EmbeddingStatusProps) {
  const [showDetails, setShowDetails] = useState(false);

  const getStatusIcon = () => {
    switch (state) {
      case "indexing":
        return <Loader2 className="h-4 w-4 animate-spin text-primary" />;
      case "ready":
        return <CheckCircle className="h-4 w-4 text-accent" />;
      case "error":
        return <AlertCircle className="h-4 w-4 text-destructive" />;
      default:
        return <Database className="h-4 w-4 text-muted-foreground" />;
    }
  };

  const getStatusText = () => {
    switch (state) {
      case "indexing":
        return "인덱싱 중...";
      case "ready":
        return "준비됨";
      case "error":
        return "오류 발생";
      default:
        return "대기 중";
    }
  };

  if (state === "indexing" && showDetails) {
    return (
      <div className="fixed inset-0 bg-background/95 backdrop-blur-sm z-50 flex items-center justify-center">
        <div className="text-center space-y-6 p-8">
          <Character
            mood="loading"
            message={`노트를 임베딩하고 있어요... (${processedFiles}/${totalFiles})`}
            size="lg"
          />
          <div className="w-64 mx-auto space-y-2">
            <Progress value={progress} className="h-2" />
            <p className="text-xs text-muted-foreground">
              {progress.toFixed(0)}% 완료
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDetails(false)}
            className="text-muted-foreground"
          >
            최소화
          </Button>
        </div>
      </div>
    );
  }

  return (
    <TooltipProvider>
      <div className="flex items-center gap-2">
        <Tooltip>
          <TooltipTrigger asChild>
            <button
              onClick={() => state === "indexing" && setShowDetails(true)}
              className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm transition-colors",
                state === "indexing"
                  ? "bg-primary/10 cursor-pointer hover:bg-primary/20"
                  : "bg-muted"
              )}
            >
              {getStatusIcon()}
              <span className="text-muted-foreground">{getStatusText()}</span>
              {state === "indexing" && (
                <span className="text-xs text-primary">
                  {progress.toFixed(0)}%
                </span>
              )}
            </button>
          </TooltipTrigger>
          <TooltipContent>
            {state === "ready" && (
              <p>{totalFiles}개의 노트가 인덱싱되었습니다</p>
            )}
            {state === "indexing" && (
              <p>클릭하여 자세히 보기</p>
            )}
            {state === "idle" && (
              <p>인덱싱을 시작해주세요</p>
            )}
            {state === "error" && (
              <p>인덱싱 중 오류가 발생했습니다</p>
            )}
          </TooltipContent>
        </Tooltip>

        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              onClick={onReindex}
              disabled={state === "indexing"}
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <RefreshCw className={cn("h-4 w-4", state === "indexing" && "animate-spin")} />
              <span className="sr-only">재인덱싱</span>
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>노트 재인덱싱</p>
          </TooltipContent>
        </Tooltip>
      </div>
    </TooltipProvider>
  );
}
