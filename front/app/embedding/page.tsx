"use client";

import { EmbeddingScope } from "@/components/embedding/embedding-scope";
import { EmbeddingVisualization } from "@/components/embedding/embedding-visualization";

export default function EmbeddingPage() {
  return (
    <div className="p-6 space-y-8">
      <h1 className="text-3xl font-black mb-6 uppercase">Embedding</h1>
      <EmbeddingScope />
      <EmbeddingVisualization />
    </div>
  );
}
