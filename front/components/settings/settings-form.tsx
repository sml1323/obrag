"use client"

import * as React from "react"
import { downloadEmbeddingModel, getEmbeddingModelStatus } from "@/lib/api/embedding"
import { getSettings, updateSettings } from "@/lib/api/settings"
import type { EmbeddingModelStatus } from "@/lib/types/embedding"
import type { SettingsUpdate } from "@/lib/types/settings"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { SimpleSelect } from "@/components/ui/select"

function isMaskedValue(value: string | undefined): boolean {
  if (!value) return false
  return value.startsWith("***")
}

export function SettingsForm() {
  const [loading, setLoading] = React.useState(true)
  const [saving, setSaving] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [success, setSuccess] = React.useState<string | null>(null)
  
  const [formData, setFormData] = React.useState<SettingsUpdate>({
    vault_path: "",
    llm_provider: "openai",
    llm_model: "",
    llm_api_key: "",
    embedding_provider: "openai",
    embedding_model: "",
    embedding_api_key: "",
    ollama_endpoint: "",
  })

  const [hasLlmKey, setHasLlmKey] = React.useState(false)
  const [hasEmbeddingKey, setHasEmbeddingKey] = React.useState(false)
  const [llmKeyModified, setLlmKeyModified] = React.useState(false)
  const [embeddingKeyModified, setEmbeddingKeyModified] = React.useState(false)

  const [showLlmKey, setShowLlmKey] = React.useState(false)
  const [showEmbeddingKey, setShowEmbeddingKey] = React.useState(false)
  const [embeddingStatus, setEmbeddingStatus] = React.useState<EmbeddingModelStatus | null>(null)
  const [embeddingStatusLoading, setEmbeddingStatusLoading] = React.useState(false)
  const [embeddingDownloadLoading, setEmbeddingDownloadLoading] = React.useState(false)
  const [embeddingStatusError, setEmbeddingStatusError] = React.useState<string | null>(null)

  const localEmbeddingModelId = React.useMemo(() => {
    if (formData.embedding_provider !== "sentence_transformers") {
      return ""
    }
    const modelName = formData.embedding_model?.trim()
    return modelName || "BAAI/bge-m3"
  }, [formData.embedding_model, formData.embedding_provider])

  React.useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true)
        const data = await getSettings()
        
        const llmKeyIsSaved = isMaskedValue(data.llm_api_key || "")
        const embeddingKeyIsSaved = isMaskedValue(data.embedding_api_key || "")
        
        setHasLlmKey(llmKeyIsSaved)
        setHasEmbeddingKey(embeddingKeyIsSaved)
        
        setFormData({
          vault_path: data.vault_path || "",
          llm_provider: data.llm_provider || "openai",
          llm_model: data.llm_model || "",
          llm_api_key: llmKeyIsSaved ? "" : (data.llm_api_key || ""),
          embedding_provider: data.embedding_provider || "openai",
          embedding_model: data.embedding_model || "",
          embedding_api_key: embeddingKeyIsSaved ? "" : (data.embedding_api_key || ""),
          ollama_endpoint: data.ollama_endpoint || "",
        })
      } catch (err) {
        setError("Failed to load settings. Please try again.")
        console.error(err)
      } finally {
        setLoading(false)
      }
    }
    loadSettings()
  }, [])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData((prev) => ({ ...prev, [name]: value }))
    
    if (name === "llm_api_key") {
      setLlmKeyModified(true)
    }
    if (name === "embedding_api_key") {
      setEmbeddingKeyModified(true)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      const dataToSend = { ...formData }
      
      if (hasLlmKey && !llmKeyModified) {
        dataToSend.llm_api_key = "***"
      }
      if (hasEmbeddingKey && !embeddingKeyModified) {
        dataToSend.embedding_api_key = "***"
      }
      
      await updateSettings(dataToSend)
      setSuccess("Settings saved successfully!")
      
      if (llmKeyModified && formData.llm_api_key) {
        setHasLlmKey(true)
        setLlmKeyModified(false)
        setFormData(prev => ({ ...prev, llm_api_key: "" }))
      }
      if (embeddingKeyModified && formData.embedding_api_key) {
        setHasEmbeddingKey(true)
        setEmbeddingKeyModified(false)
        setFormData(prev => ({ ...prev, embedding_api_key: "" }))
      }
    } catch (err) {
      setError("Failed to save settings. Please check your inputs.")
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

  const refreshEmbeddingStatus = React.useCallback(async () => {
    if (formData.embedding_provider !== "sentence_transformers") {
      setEmbeddingStatus(null)
      setEmbeddingStatusError(null)
      return
    }

    if (!localEmbeddingModelId) {
      setEmbeddingStatus(null)
      return
    }

    setEmbeddingStatusLoading(true)
    setEmbeddingStatusError(null)
    try {
      const status = await getEmbeddingModelStatus(localEmbeddingModelId)
      setEmbeddingStatus(status)
    } catch (err) {
      console.error(err)
      setEmbeddingStatusError("Failed to check model status.")
      setEmbeddingStatus({
        model_id: localEmbeddingModelId,
        status: "error",
        progress: 0,
        error: "Status check failed",
      })
    } finally {
      setEmbeddingStatusLoading(false)
    }
  }, [formData.embedding_provider, localEmbeddingModelId])

  const handleModelDownload = React.useCallback(async () => {
    if (!localEmbeddingModelId) {
      return
    }

    setEmbeddingDownloadLoading(true)
    setEmbeddingStatusError(null)
    try {
      await downloadEmbeddingModel(localEmbeddingModelId)
    } catch (err) {
      console.error(err)
      setEmbeddingStatusError("Failed to start download.")
    } finally {
      setEmbeddingDownloadLoading(false)
      await refreshEmbeddingStatus()
    }
  }, [localEmbeddingModelId, refreshEmbeddingStatus])

  React.useEffect(() => {
    if (formData.embedding_provider === "sentence_transformers") {
      refreshEmbeddingStatus()
    } else {
      setEmbeddingStatus(null)
      setEmbeddingStatusError(null)
    }
  }, [formData.embedding_provider, localEmbeddingModelId, refreshEmbeddingStatus])

  React.useEffect(() => {
    if (embeddingStatus?.status !== "downloading") {
      return
    }

    const interval = setInterval(() => {
      refreshEmbeddingStatus()
    }, 2000)

    return () => clearInterval(interval)
  }, [embeddingStatus?.status, refreshEmbeddingStatus])

  const embeddingStatusLabel = (() => {
    if (embeddingStatusLoading) {
      return "Checking model status..."
    }

    if (!embeddingStatus) {
      return "Model status unknown"
    }

    switch (embeddingStatus.status) {
      case "ready":
        return "Model is ready"
      case "downloading":
        return "Model download in progress"
      case "not_found":
        return "Model is not downloaded"
      case "error":
        return "Model status error"
      default:
        return "Model status unknown"
    }
  })()

  const isDownloading = embeddingStatus?.status === "downloading"
  const isReady = embeddingStatus?.status === "ready"
  const downloadDisabled =
    embeddingDownloadLoading || embeddingStatusLoading || isDownloading || isReady || !localEmbeddingModelId

  const downloadLabel = isReady ? "Downloaded" : isDownloading ? "Downloading" : "Download"
  const embeddingStatusMessage = embeddingStatusError || embeddingStatus?.error || null

  if (loading) {
    return (
      <div className="flex h-64 w-full items-center justify-center">
        <div className="text-xl font-bold uppercase tracking-widest">Loading Settings...</div>
      </div>
    )
  }

  return (
    <div className="mx-auto max-w-2xl">
      <div className="border-3 border-black bg-[#FFFEF0] p-8 shadow-[6px_6px_0px_0px_rgba(0,0,0,1)]">
        <h1 className="mb-8 text-3xl font-black uppercase tracking-tight">System Configuration</h1>

        {error && (
          <div className="mb-6 border-3 border-black bg-red-100 p-4 font-bold text-red-600">
            {error}
          </div>
        )}

        {success && (
          <div className="mb-6 border-3 border-black bg-green-100 p-4 font-bold text-green-700">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-12">
          <section className="space-y-6">
            <h2 className="border-b-3 border-black pb-2 text-xl font-black uppercase">
              1. Vault Configuration
            </h2>
            <Input
              label="Vault Path"
              name="vault_path"
              value={formData.vault_path}
              onChange={handleChange}
              placeholder="/Users/username/Documents/MyVault"
            />
          </section>

          <section className="space-y-6">
            <h2 className="border-b-3 border-black pb-2 text-xl font-black uppercase">
              2. LLM Configuration
            </h2>
            <SimpleSelect
              label="LLM Provider"
              name="llm_provider"
              value={formData.llm_provider}
              onChange={handleChange}
              options={[
                { value: "openai", label: "OpenAI" },
                { value: "gemini", label: "Google Gemini" },
                { value: "ollama", label: "Ollama (Local)" },
              ]}
            />
            
            <div className="grid gap-6 md:grid-cols-2">
              <Input
                label="Model Name"
                name="llm_model"
                value={formData.llm_model}
                onChange={handleChange}
                placeholder="gpt-4-turbo"
              />
              <div className="relative">
                <Input
                  label={hasLlmKey && !llmKeyModified ? "API Key (saved)" : "API Key"}
                  name="llm_api_key"
                  type={showLlmKey ? "text" : "password"}
                  value={formData.llm_api_key}
                  onChange={handleChange}
                  placeholder={hasLlmKey ? "Enter new key to replace" : "sk-..."}
                />
                {hasLlmKey && !llmKeyModified && (
                  <div className="absolute right-0 top-6 flex items-center gap-2">
                    <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 border border-green-300">
                      SAVED
                    </span>
                  </div>
                )}
                {(!hasLlmKey || llmKeyModified) && (
                  <button
                    type="button"
                    onClick={() => setShowLlmKey(!showLlmKey)}
                    className="absolute right-0 top-0 text-xs font-bold uppercase underline hover:text-[#FF6B35]"
                  >
                    {showLlmKey ? "Hide" : "Show"}
                  </button>
                )}
              </div>
            </div>

            {formData.llm_provider === "ollama" && (
              <div className="animate-in fade-in slide-in-from-top-4">
                <Input
                  label="Ollama Endpoint"
                  name="ollama_endpoint"
                  value={formData.ollama_endpoint}
                  onChange={handleChange}
                  placeholder="http://localhost:11434"
                />
              </div>
            )}
          </section>

          <section className="space-y-6">
            <h2 className="border-b-3 border-black pb-2 text-xl font-black uppercase">
              3. Embedding Configuration
            </h2>
            <SimpleSelect
              label="Embedding Provider"
              name="embedding_provider"
              value={formData.embedding_provider}
              onChange={handleChange}
              options={[
                { value: "openai", label: "OpenAI" },
                { value: "ollama", label: "Ollama (Local)" },
                { value: "sentence_transformers", label: "Sentence Transformers (Local)" },
              ]}
            />
            
            <div className="grid gap-6 md:grid-cols-2">
              <Input
                label="Embedding Model"
                name="embedding_model"
                value={formData.embedding_model}
                onChange={handleChange}
                placeholder={
                  formData.embedding_provider === "openai" 
                    ? "text-embedding-3-small" 
                    : formData.embedding_provider === "ollama"
                    ? "nomic-embed-text"
                    : "BAAI/bge-m3"
                }
              />
              {formData.embedding_provider === "openai" && (
                <div className="relative">
                  <Input
                    label={hasEmbeddingKey && !embeddingKeyModified ? "Embedding API Key (saved)" : "Embedding API Key"}
                    name="embedding_api_key"
                    type={showEmbeddingKey ? "text" : "password"}
                    value={formData.embedding_api_key}
                    onChange={handleChange}
                    placeholder={hasEmbeddingKey ? "Enter new key to replace" : "sk-..."}
                  />
                  {hasEmbeddingKey && !embeddingKeyModified && (
                    <div className="absolute right-0 top-6 flex items-center gap-2">
                      <span className="text-xs font-bold text-green-600 bg-green-100 px-2 py-1 border border-green-300">
                        SAVED
                      </span>
                    </div>
                  )}
                  {(!hasEmbeddingKey || embeddingKeyModified) && (
                    <button
                      type="button"
                      onClick={() => setShowEmbeddingKey(!showEmbeddingKey)}
                      className="absolute right-0 top-0 text-xs font-bold uppercase underline hover:text-[#FF6B35]"
                    >
                      {showEmbeddingKey ? "Hide" : "Show"}
                    </button>
                  )}
                </div>
              )}
            </div>

            {formData.embedding_provider === "ollama" && (
              <div className="animate-in fade-in slide-in-from-top-4">
                <Input
                  label="Ollama Embedding Endpoint"
                  name="ollama_endpoint"
                  value={formData.ollama_endpoint}
                  onChange={handleChange}
                  placeholder="http://localhost:11434"
                />
                <p className="mt-2 text-sm text-gray-600">
                  Available models: nomic-embed-text (768d), mxbai-embed-large (1024d), all-minilm (384d)
                </p>
              </div>
            )}

            {formData.embedding_provider === "sentence_transformers" && (
              <div className="space-y-4">
                <div className="animate-in fade-in slide-in-from-top-4 rounded border-2 border-dashed border-gray-300 bg-gray-50 p-4">
                  <p className="text-sm text-gray-600">
                    <span className="font-bold">Recommended models:</span><br />
                    • BAAI/bge-m3 (1024d) - Best multilingual<br />
                    • dragonkue/BGE-m3-ko (1024d) - Korean optimized
                  </p>
                </div>
                <div className="rounded border-3 border-black bg-white p-4">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="space-y-1">
                      <p className="text-xs font-bold uppercase">Local Model Status</p>
                      <p className="text-sm font-bold">{embeddingStatusLabel}</p>
                      <p className="text-xs text-gray-600">
                        {localEmbeddingModelId || "BAAI/bge-m3"}
                      </p>
                      {embeddingStatus?.size_mb ? (
                        <p className="text-xs text-gray-600">
                          Size: {embeddingStatus.size_mb} MB
                        </p>
                      ) : null}
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        onClick={refreshEmbeddingStatus}
                        isLoading={embeddingStatusLoading}
                      >
                        Check
                      </Button>
                      <Button
                        type="button"
                        variant="primary"
                        size="sm"
                        onClick={handleModelDownload}
                        isLoading={embeddingDownloadLoading}
                        disabled={downloadDisabled}
                      >
                        {downloadLabel}
                      </Button>
                    </div>
                  </div>
                  {embeddingStatus?.status === "downloading" && (
                    <div className="mt-3 space-y-2">
                      <Progress value={embeddingStatus.progress} />
                      <p className="text-xs text-gray-600">
                        {Math.round(embeddingStatus.progress)}% complete
                      </p>
                    </div>
                  )}
                  {embeddingStatusMessage ? (
                    <p className="mt-2 text-xs font-bold text-red-600">
                      {embeddingStatusMessage}
                    </p>
                  ) : null}
                </div>
              </div>
            )}
          </section>

          <div className="pt-4">
            <Button
              type="submit"
              variant="primary"
              className="w-full"
              isLoading={saving}
            >
              Save Configuration
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
