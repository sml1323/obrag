"use client";

import { useState, useEffect } from "react";
import { Settings, X, Key, Brain, Database, FolderOpen } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Separator } from "@/components/ui/separator";

export interface AppSettings {
  llmProvider: string;
  llmModel: string;
  embeddingProvider: string;
  embeddingModel: string;
  llmApiKey: string;
  embeddingApiKey: string;
  ollamaEndpoint: string;
  vaultPath: string;
}

const defaultSettings: AppSettings = {
  llmProvider: "openai",
  llmModel: "gpt-4o",
  embeddingProvider: "openai",
  embeddingModel: "text-embedding-3-small",
  llmApiKey: "",
  embeddingApiKey: "",
  ollamaEndpoint: "http://localhost:11434",
  vaultPath: "",
};

const LLM_MODELS = {
  openai: ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"],
  gemini: ["gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"],
  ollama: ["llama3.2", "mistral", "codellama", "phi"],
};

const EMBEDDING_MODELS = {
  openai: ["text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"],
  ollama: ["bge-m3", "nomic-embed-text", "mxbai-embed-large"],
};

interface SettingsPanelProps {
  settings: AppSettings;
  onSettingsChange: (settings: AppSettings) => void;
}

export function SettingsPanel({ settings, onSettingsChange }: SettingsPanelProps) {
  const [open, setOpen] = useState(false);
  const [localSettings, setLocalSettings] = useState<AppSettings>(settings);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  const handleSave = () => {
    onSettingsChange(localSettings);
    setOpen(false);
  };

  const updateSetting = <K extends keyof AppSettings>(
    key: K,
    value: AppSettings[K]
  ) => {
    setLocalSettings((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button variant="ghost" size="icon" className="text-muted-foreground hover:text-foreground">
          <Settings className="h-5 w-5" />
          <span className="sr-only">설정</span>
        </Button>
      </SheetTrigger>
      <SheetContent className="w-[400px] sm:w-[540px] bg-card border-border overflow-y-auto">
        <SheetHeader>
          <SheetTitle className="text-foreground">설정</SheetTitle>
          <SheetDescription className="text-muted-foreground">
            AI 모델 및 임베딩 설정을 구성합니다.
          </SheetDescription>
        </SheetHeader>

        <div className="mt-6 space-y-6">
          {/* Vault Path */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-foreground">
              <FolderOpen className="h-4 w-4 text-primary" />
              <h3 className="font-medium">Obsidian Vault</h3>
            </div>
            <div className="space-y-2">
              <Label htmlFor="vaultPath" className="text-muted-foreground text-sm">
                Vault 경로
              </Label>
              <Input
                id="vaultPath"
                placeholder="/Users/your-name/Documents/Obsidian"
                value={localSettings.vaultPath}
                onChange={(e) => updateSetting("vaultPath", e.target.value)}
                className="bg-input border-border text-foreground placeholder:text-muted-foreground"
              />
            </div>
          </div>

          <Separator className="bg-border" />

          {/* LLM Settings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-foreground">
              <Brain className="h-4 w-4 text-primary" />
              <h3 className="font-medium">LLM 모델</h3>
            </div>
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor="llmProvider" className="text-muted-foreground text-sm">
                  Provider
                </Label>
                <Select
                  value={localSettings.llmProvider}
                  onValueChange={(value) => {
                    updateSetting("llmProvider", value);
                    updateSetting(
                      "llmModel",
                      LLM_MODELS[value as keyof typeof LLM_MODELS][0]
                    );
                  }}
                >
                  <SelectTrigger className="bg-input border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="gemini">Google Gemini</SelectItem>
                    <SelectItem value="ollama">Ollama (Local)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="llmModel" className="text-muted-foreground text-sm">
                  모델
                </Label>
                <Select
                  value={localSettings.llmModel}
                  onValueChange={(value) => updateSetting("llmModel", value)}
                >
                  <SelectTrigger className="bg-input border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {LLM_MODELS[
                      localSettings.llmProvider as keyof typeof LLM_MODELS
                    ]?.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator className="bg-border" />

          {/* Embedding Settings */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-foreground">
              <Database className="h-4 w-4 text-accent" />
              <h3 className="font-medium">임베딩 모델</h3>
            </div>
            <div className="grid gap-4">
              <div className="space-y-2">
                <Label htmlFor="embeddingProvider" className="text-muted-foreground text-sm">
                  Provider
                </Label>
                <Select
                  value={localSettings.embeddingProvider}
                  onValueChange={(value) => {
                    updateSetting("embeddingProvider", value);
                    updateSetting(
                      "embeddingModel",
                      EMBEDDING_MODELS[value as keyof typeof EMBEDDING_MODELS][0]
                    );
                  }}
                >
                  <SelectTrigger className="bg-input border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    <SelectItem value="openai">OpenAI</SelectItem>
                    <SelectItem value="ollama">Ollama (Local)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="embeddingModel" className="text-muted-foreground text-sm">
                  모델
                </Label>
                <Select
                  value={localSettings.embeddingModel}
                  onValueChange={(value) => updateSetting("embeddingModel", value)}
                >
                  <SelectTrigger className="bg-input border-border text-foreground">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-popover border-border">
                    {EMBEDDING_MODELS[
                      localSettings.embeddingProvider as keyof typeof EMBEDDING_MODELS
                    ]?.map((model) => (
                      <SelectItem key={model} value={model}>
                        {model}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </div>

          <Separator className="bg-border" />

          {/* API Keys */}
          <div className="space-y-3">
            <div className="flex items-center gap-2 text-foreground">
              <Key className="h-4 w-4 text-chart-3" />
              <h3 className="font-medium">API 키 설정</h3>
            </div>
            <div className="grid gap-4">
              {localSettings.llmProvider !== "ollama" && (
                <div className="space-y-2">
                  <Label htmlFor="llmApiKey" className="text-muted-foreground text-sm">
                    LLM API Key
                  </Label>
                  <Input
                    id="llmApiKey"
                    type="password"
                    placeholder="sk-..."
                    value={localSettings.llmApiKey}
                    onChange={(e) => updateSetting("llmApiKey", e.target.value)}
                    className="bg-input border-border text-foreground placeholder:text-muted-foreground font-mono"
                  />
                </div>
              )}
              {localSettings.embeddingProvider !== "ollama" && (
                <div className="space-y-2">
                  <Label htmlFor="embeddingApiKey" className="text-muted-foreground text-sm">
                    임베딩 API Key
                  </Label>
                  <Input
                    id="embeddingApiKey"
                    type="password"
                    placeholder="sk-..."
                    value={localSettings.embeddingApiKey}
                    onChange={(e) => updateSetting("embeddingApiKey", e.target.value)}
                    className="bg-input border-border text-foreground placeholder:text-muted-foreground font-mono"
                  />
                </div>
              )}
              {(localSettings.llmProvider === "ollama" ||
                localSettings.embeddingProvider === "ollama") && (
                <div className="space-y-2">
                  <Label htmlFor="ollamaEndpoint" className="text-muted-foreground text-sm">
                    Ollama Endpoint
                  </Label>
                  <Input
                    id="ollamaEndpoint"
                    placeholder="http://localhost:11434"
                    value={localSettings.ollamaEndpoint}
                    onChange={(e) => updateSetting("ollamaEndpoint", e.target.value)}
                    className="bg-input border-border text-foreground placeholder:text-muted-foreground font-mono"
                  />
                </div>
              )}
            </div>
          </div>

          <div className="pt-4">
            <Button
              onClick={handleSave}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              저장
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
}

export { defaultSettings };
