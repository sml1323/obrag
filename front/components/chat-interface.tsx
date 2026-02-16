"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Sparkles, FileText } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Character } from "./character";
import { cn } from "@/lib/utils";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: { title: string; path: string }[];
  timestamp: Date;
}

interface ChatInterfaceProps {
  isLoading: boolean;
  onSendMessage: (message: string) => void;
  messages: Message[];
}

export function ChatInterface({
  isLoading,
  onSendMessage,
  messages,
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput("");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea
        ref={scrollRef}
        className="flex-1 px-4 py-6"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full min-h-[60vh] text-center">
            <div className="mb-6">
              <Character mood="default" size="lg" showMessage={false} />
            </div>
            <h2 className="text-2xl font-semibold text-foreground mb-2">
              Obsidian AI
            </h2>
            <p className="text-muted-foreground max-w-md leading-relaxed">
              Obsidian 노트를 기반으로 질문에 답변합니다.
              <br />
              먼저 설정에서 Vault 경로와 API 키를 입력해주세요.
            </p>
            <div className="flex gap-2 mt-6">
              <Button
                variant="outline"
                size="sm"
                className="border-border text-muted-foreground hover:text-foreground bg-transparent"
                onClick={() => onSendMessage("내 노트에서 최근 배운 내용을 요약해줘")}
              >
                <Sparkles className="h-4 w-4 mr-2" />
                최근 학습 요약
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="border-border text-muted-foreground hover:text-foreground bg-transparent"
                onClick={() => onSendMessage("복습이 필요한 노트를 알려줘")}
              >
                <FileText className="h-4 w-4 mr-2" />
                복습 추천
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-6 max-w-3xl mx-auto">
            {messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "flex",
                  message.role === "user" ? "justify-end" : "justify-start"
                )}
              >
                <div
                  className={cn(
                    "max-w-[85%] rounded-2xl px-4 py-3",
                    message.role === "user"
                      ? "bg-primary text-primary-foreground"
                      : "bg-card border border-border text-foreground"
                  )}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {message.content}
                  </p>
                  {message.sources && message.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-border/50">
                      <p className="text-xs text-muted-foreground mb-2">
                        참조한 노트:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {message.sources.map((source, idx) => (
                          <span
                            key={idx}
                            className="inline-flex items-center text-xs px-2 py-1 rounded-md bg-muted text-muted-foreground"
                          >
                            <FileText className="h-3 w-3 mr-1" />
                            {source.title}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isLoading && (
              <div className="flex justify-start">
                <div className="bg-card border border-border rounded-2xl px-6 py-4">
                  <Character mood="speak" size="sm" message="답변을 생성하고 있어요..." />
                </div>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t border-border bg-background/80 backdrop-blur-sm p-4">
        <form
          onSubmit={handleSubmit}
          className="max-w-3xl mx-auto flex gap-3 items-end"
        >
          <div className="flex-1 relative">
            <Textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Obsidian 노트에 대해 질문하세요..."
              className="min-h-[52px] max-h-[200px] resize-none bg-input border-border text-foreground placeholder:text-muted-foreground pr-4 rounded-xl"
              rows={1}
            />
          </div>
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="h-[52px] w-[52px] rounded-xl bg-primary hover:bg-primary/90 text-primary-foreground disabled:opacity-50 p-0"
          >
            <Send className="h-5 w-5" />
            <span className="sr-only">전송</span>
          </Button>
        </form>
      </div>
    </div>
  );
}

export type { Message };
