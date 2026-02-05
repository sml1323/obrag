"use client";

import { EmbeddingScope } from "@/components/embedding/embedding-scope";

export default function EmbeddingPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-black mb-6 uppercase">Embedding</h1>
      <EmbeddingScope />
    </div>
  );
}
