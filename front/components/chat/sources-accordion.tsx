import React, { useState } from 'react';
import { SourceChunk } from '@/lib/types/chat';
import { ChevronDown, ChevronUp, FileText } from 'lucide-react';

interface SourcesAccordionProps {
  sources: SourceChunk[];
}

export function SourcesAccordion({ sources }: SourcesAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 border-2 border-black bg-white shadow-[4px_4px_0px_#000000]">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex w-full items-center justify-between p-3 bg-gray-100 hover:bg-gray-200 transition-colors font-bold border-b-2 border-black"
      >
        <span className="flex items-center gap-2">
          📚 Sources ({sources.length})
        </span>
        {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {isOpen && (
        <div className="p-3 space-y-3">
          {sources.map((source, idx) => (
            <div key={idx} className="border border-black p-2 bg-yellow-50 text-sm">
              <div className="flex items-center justify-between mb-1">
                <div className="flex items-center gap-1 font-semibold text-xs overflow-hidden">
                  <FileText className="h-3 w-3" />
                  <span className="truncate max-w-[200px]">{source.source}</span>
                </div>
                <div className="text-xs font-mono bg-black text-white px-1">
                  {(source.score * 100).toFixed(0)}%
                </div>
              </div>
              <p className="text-gray-700 line-clamp-2 text-xs font-mono">
                {source.content}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
