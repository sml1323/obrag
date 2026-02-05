"use client"

import * as React from "react"
import { getSettings, updateSettings } from "@/lib/api/settings"
import type { SettingsUpdate } from "@/lib/types/settings"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { Button } from "@/components/ui/button"

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

  const [showLlmKey, setShowLlmKey] = React.useState(false)
  const [showEmbeddingKey, setShowEmbeddingKey] = React.useState(false)

  React.useEffect(() => {
    async function loadSettings() {
      try {
        setLoading(true)
        const data = await getSettings()
        setFormData({
          vault_path: data.vault_path || "",
          llm_provider: data.llm_provider || "openai",
          llm_model: data.llm_model || "",
          llm_api_key: data.llm_api_key || "",
          embedding_provider: data.embedding_provider || "openai",
          embedding_model: data.embedding_model || "",
          embedding_api_key: data.embedding_api_key || "",
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
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSuccess(null)

    try {
      await updateSettings(formData)
      setSuccess("Settings saved successfully!")
    } catch (err) {
      setError("Failed to save settings. Please check your inputs.")
      console.error(err)
    } finally {
      setSaving(false)
    }
  }

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
            <Select
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
                  label="API Key"
                  name="llm_api_key"
                  type={showLlmKey ? "text" : "password"}
                  value={formData.llm_api_key}
                  onChange={handleChange}
                  placeholder="sk-..."
                />
                <button
                  type="button"
                  onClick={() => setShowLlmKey(!showLlmKey)}
                  className="absolute right-0 top-0 text-xs font-bold uppercase underline hover:text-[#FF6B35]"
                >
                  {showLlmKey ? "Hide" : "Show"}
                </button>
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
            <Select
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
                    label="Embedding API Key"
                    name="embedding_api_key"
                    type={showEmbeddingKey ? "text" : "password"}
                    value={formData.embedding_api_key}
                    onChange={handleChange}
                    placeholder="sk-..."
                  />
                  <button
                    type="button"
                    onClick={() => setShowEmbeddingKey(!showEmbeddingKey)}
                    className="absolute right-0 top-0 text-xs font-bold uppercase underline hover:text-[#FF6B35]"
                  >
                    {showEmbeddingKey ? "Hide" : "Show"}
                  </button>
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
              <div className="animate-in fade-in slide-in-from-top-4 rounded border-2 border-dashed border-gray-300 bg-gray-50 p-4">
                <p className="text-sm text-gray-600">
                  <span className="font-bold">Recommended models:</span><br />
                  • BAAI/bge-m3 (1024d) - Best multilingual<br />
                  • dragonkue/BGE-m3-ko (1024d) - Korean optimized
                </p>
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
