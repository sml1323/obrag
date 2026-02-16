"use client";

import React, { useState, useMemo } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SourceChunk } from '@/lib/types/chat';
import { getDocumentContent } from '@/lib/api/vault';
import { ChevronDown, ChevronUp, FileText, Loader2, Tag, Calendar } from 'lucide-react';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';

interface FrontmatterData {
  tags?: string[];
  create?: string;
  [key: string]: unknown;
}

function parseFrontmatter(content: string): { frontmatter: FrontmatterData | null; body: string } {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) return { frontmatter: null, body: content };

  const raw = match[1];
  const body = match[2];
  const data: FrontmatterData = {};

  let currentKey = '';
  let inArray = false;
  const arrayValues: string[] = [];

  for (const line of raw.split('\n')) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    if (inArray && trimmed.startsWith('- ')) {
      arrayValues.push(trimmed.slice(2).trim());
      continue;
    }

    if (inArray && currentKey) {
      data[currentKey] = arrayValues.length > 0 ? [...arrayValues] : [];
      inArray = false;
      arrayValues.length = 0;
    }

    const colonIdx = trimmed.indexOf(':');
    if (colonIdx > 0) {
      currentKey = trimmed.slice(0, colonIdx).trim();
      const value = trimmed.slice(colonIdx + 1).trim();
      if (!value) {
        inArray = true;
      } else {
        data[currentKey] = value;
      }
    }
  }

  if (inArray && currentKey) {
    data[currentKey] = arrayValues.length > 0 ? [...arrayValues] : [];
  }

  return { frontmatter: data, body };
}

interface SourcesAccordionProps {
  sources: SourceChunk[];
}

export function SourcesAccordion({ sources }: SourcesAccordionProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const [selectedSource, setSelectedSource] = useState('');
  const [documentContent, setDocumentContent] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const parsed = useMemo(() => parseFrontmatter(documentContent), [documentContent]);

  if (!sources || sources.length === 0) return null;

  const handleSourceClick = async (source: SourceChunk) => {
    setSelectedSource(source.source);
    setSheetOpen(true);
    setIsLoading(true);
    setLoadError(null);
    setDocumentContent('');

    try {
      const doc = await getDocumentContent(source.source, source.relative_path);
      setDocumentContent(doc.content);
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : 'Failed to load document');
    } finally {
      setIsLoading(false);
    }
  };

  const tags = Array.isArray(parsed.frontmatter?.tags) ? parsed.frontmatter.tags : [];
  const createdAt = parsed.frontmatter?.create;

  return (
    <>
      <div className="mt-4 border-2 border-black bg-white shadow-[4px_4px_0px_#000000]">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex w-full items-center justify-between p-3 bg-gray-100 hover:bg-gray-200 transition-colors font-bold border-b-2 border-black"
        >
          <span className="flex items-center gap-2">
            📚 SOURCES ({sources.length})
          </span>
          {isOpen ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>

        {isOpen && (
          <div className="p-3 space-y-3">
            {sources.map((source, idx) => (
              <button
                key={idx}
                onClick={() => handleSourceClick(source)}
                className="w-full text-left border-2 border-black p-3 bg-yellow-50 hover:bg-yellow-100 transition-colors cursor-pointer shadow-[2px_2px_0px_#000000] hover:shadow-[3px_3px_0px_#000000] active:shadow-none active:translate-x-[2px] active:translate-y-[2px]"
              >
                <div className="flex items-center justify-between mb-1">
                  <div className="flex items-center gap-1.5 font-bold text-sm overflow-hidden">
                    <FileText className="h-4 w-4 shrink-0" />
                    <span className="truncate">{source.source}</span>
                  </div>
                  <div className="text-xs font-mono bg-black text-white px-1.5 py-0.5 shrink-0 ml-2">
                    {(source.score * 100).toFixed(0)}%
                  </div>
                </div>
                <p className="text-gray-700 line-clamp-2 text-xs font-mono">
                  {source.content}
                </p>
              </button>
            ))}
          </div>
        )}
      </div>

      <Sheet open={sheetOpen} onOpenChange={setSheetOpen}>
        <SheetContent
          side="right"
          showCloseButton={false}
          className="!w-[65vw] !max-w-[65vw] border-l-3 border-black shadow-[-6px_0px_0px_#000000] p-0 flex flex-col gap-0"
        >
          <SheetHeader className="px-6 pt-5 pb-3 border-b-3 border-black bg-[#4ECDC4] shrink-0">
            <div className="flex items-center justify-between">
              <SheetTitle className="flex items-center gap-2 font-black text-lg tracking-tight text-black">
                <FileText className="h-5 w-5" />
                {selectedSource}
              </SheetTitle>
              <button
                onClick={() => setSheetOpen(false)}
                className="px-3 py-1 bg-black text-white font-bold text-xs hover:bg-gray-800 border-2 border-black shadow-[2px_2px_0px_rgba(0,0,0,0.3)] active:shadow-none active:translate-x-[1px] active:translate-y-[1px] transition-all"
              >
                ESC
              </button>
            </div>

            {(tags.length > 0 || createdAt) && (
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {tags.map((tag) => (
                  <span
                    key={tag}
                    className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-bold bg-white border-2 border-black shadow-[1px_1px_0px_#000000]"
                  >
                    <Tag className="h-3 w-3" />
                    {tag}
                  </span>
                ))}
                {createdAt && (
                  <span className="inline-flex items-center gap-1 px-2 py-0.5 text-xs font-mono text-black/70">
                    <Calendar className="h-3 w-3" />
                    {String(createdAt)}
                  </span>
                )}
              </div>
            )}
          </SheetHeader>

          <ScrollArea className="flex-1 min-h-0">
            <div className="px-8 py-6">
              {isLoading && (
                <div className="flex items-center justify-center py-16">
                  <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              )}

              {loadError && (
                <div className="border-2 border-red-500 bg-red-50 p-4 text-red-700 font-mono text-sm">
                  {loadError}
                </div>
              )}

              {!isLoading && !loadError && documentContent && (
                <article className="prose prose-base max-w-none prose-headings:font-black prose-headings:tracking-tight prose-h1:text-2xl prose-h1:border-b-2 prose-h1:border-black prose-h1:pb-2 prose-h2:text-xl prose-h3:text-lg prose-code:bg-gray-100 prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded prose-code:text-sm prose-code:font-mono prose-code:before:content-none prose-code:after:content-none prose-pre:bg-gray-900 prose-pre:text-gray-100 prose-pre:border-2 prose-pre:border-black prose-pre:shadow-[3px_3px_0px_#000000] prose-pre:overflow-x-auto prose-a:text-blue-600 prose-a:font-semibold prose-a:underline-offset-2 prose-blockquote:border-l-4 prose-blockquote:border-black prose-blockquote:bg-yellow-50 prose-blockquote:py-1 prose-blockquote:not-italic prose-table:border-2 prose-table:border-black prose-th:border prose-th:border-black prose-th:bg-gray-100 prose-th:px-3 prose-th:py-1.5 prose-td:border prose-td:border-black prose-td:px-3 prose-td:py-1.5 prose-img:border-2 prose-img:border-black prose-img:shadow-[3px_3px_0px_#000000] prose-hr:border-black prose-li:marker:text-black">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {parsed.body}
                  </ReactMarkdown>
                </article>
              )}
            </div>
          </ScrollArea>
        </SheetContent>
      </Sheet>
    </>
  );
}
