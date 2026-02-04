"use client";

import { useState, useEffect } from "react";
import { Settings, Key, Brain, Database, FolderOpen, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { createProject, getProjectByPath, ApiError } from "@/lib/api/projects";
import { getSettings, updateSettings, SettingsUpdate } from "@/lib/api/settings";
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
  paraRootPath: string;
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
  paraRootPath: "",
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
  onProjectCreated?: (backendId: number, vaultPath: string) => void;
}

export function SettingsPanel({ settings, onSettingsChange, onProjectCreated }: SettingsPanelProps) {
  const [open, setOpen] = useState(false);
  const [localSettings, setLocalSettings] = useState<AppSettings>(settings);
  const [isSaving, setIsSaving] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLocalSettings(settings);
  }, [settings]);

  useEffect(() => {
    if (open) {
      loadSettingsFromBackend();
    }
  }, [open]);

  const loadSettingsFromBackend = async () => {
    setIsLoading(true);
    try {
      const backendSettings = await getSettings();
      setLocalSettings({
        vaultPath: backendSettings.vault_path || "",
        paraRootPath: backendSettings.para_root_path || "",
        llmProvider: backendSettings.llm_provider,
        llmModel: backendSettings.llm_model,
        embeddingProvider: backendSettings.embedding_provider,
        embeddingModel: backendSettings.embedding_model,
        llmApiKey: "",
        embeddingApiKey: "",
        ollamaEndpoint: backendSettings.ollama_endpoint,
      });
      
      if (backendSettings.vault_path) {
        try {
          const existing = await getProjectByPath(backendSettings.vault_path);
          if (existing) {
            onProjectCreated?.(existing.id, backendSettings.vault_path);
          }
        } catch {
        }
      }
    } catch {
      console.warn('[Settings] Failed to load from backend, using local settings');
    }
    setIsLoading(false);
  };

  const handleSave = async () => {
    setError(null);
    setIsSaving(true);
    
    if (localSettings.vaultPath && localSettings.vaultPath !== settings.vaultPath) {
      try {
        const project = await createProject({
          name: localSettings.vaultPath.split('/').pop() || 'Vault',
          vaultPath: localSettings.vaultPath,
        });
        console.log('[Settings] Project created:', project.id);
        onProjectCreated?.(project.id, localSettings.vaultPath);
      } catch (err) {
        if (err instanceof ApiError) {
          if (err.status === 400) {
            console.log('[Settings] Project already exists for this path');
            const existing = await getProjectByPath(localSettings.vaultPath);
            if (existing) {
              onProjectCreated?.(existing.id, localSettings.vaultPath);
            }
          } else {
            setError(err.message);
            setIsSaving(false);
            return;
          }
        } else {
          console.warn('[Settings] Backend unavailable, using localStorage only');
        }
      }
    }

    // Save settings to backend
    try {
      const updateData: SettingsUpdate = {
        vault_path: localSettings.vaultPath || undefined,
        para_root_path: localSettings.paraRootPath || undefined,
        llm_provider: localSettings.llmProvider,
        llm_model: localSettings.llmModel,
        embedding_provider: localSettings.embeddingProvider,
        embedding_model: localSettings.embeddingModel,
        ollama_endpoint: localSettings.ollamaEndpoint,
      };
      // Only include API keys if user entered new ones (not empty)
      if (localSettings.llmApiKey) {
        updateData.llm_api_key = localSettings.llmApiKey;
      }
      if (localSettings.embeddingApiKey) {
        updateData.embedding_api_key = localSettings.embeddingApiKey;
      }
      await updateSettings(updateData);
    } catch (err) {
      console.warn('[Settings] Failed to save to backend:', err);
      // Continue with localStorage save even if backend fails
    }
    
    onSettingsChange(localSettings);
    setOpen(false);
    setIsSaving(false);
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

        {isLoading ? (
          <div className="flex flex-col items-center justify-center h-64 space-y-4">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
            <p className="text-muted-foreground">설정을 불러오는 중...</p>
          </div>
        ) : (
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
              <div className="space-y-2">
                <Label htmlFor="paraRootPath" className="text-muted-foreground text-sm">
                  프로젝트 루트(PARA)
                </Label>
                <Input
                  id="paraRootPath"
                  placeholder="Project"
                  value={localSettings.paraRootPath}
                  onChange={(e) => updateSetting("paraRootPath", e.target.value)}
                  className="bg-input border-border text-foreground placeholder:text-muted-foreground font-mono"
                />
                <p className="text-xs text-muted-foreground">
                  Vault 기준 상대 경로를 입력하세요. (예: Project)
                </p>
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

          <div className="pt-4 space-y-2">
            {error && (
              <div className="text-sm text-destructive bg-destructive/10 p-2 rounded">
                {error}
              </div>
            )}
            <Button
              onClick={handleSave}
              disabled={isSaving}
              className="w-full bg-primary hover:bg-primary/90 text-primary-foreground"
            >
              {isSaving ? "저장 중..." : "저장"}
            </Button>
          </div>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}

export { defaultSettings };
