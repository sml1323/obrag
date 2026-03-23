"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { checkHealth } from "@/lib/api/health";
import { getSettings } from "@/lib/api/settings";

interface SystemInfo {
  backendOnline: boolean;
  llmProvider: string | null;
  llmModel: string | null;
  embeddingProvider: string | null;
  embeddingModel: string | null;
}

const POLL_HEALTHY = 30_000;
const POLL_RETRY = 2_000;

export function SystemStatus() {
  const [info, setInfo] = useState<SystemInfo>({
    backendOnline: false,
    llmProvider: null,
    llmModel: null,
    embeddingProvider: null,
    embeddingModel: null,
  });

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const schedule = useCallback((fn: () => void, ms: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(fn, ms);
  }, []);

  const refresh = useCallback(async () => {
    let online = false;
    try {
      const h = await checkHealth();
      online = h.status === "healthy";
    } catch {
      online = false;
    }

    if (online) {
      try {
        const s = await getSettings();
        setInfo({
          backendOnline: true,
          llmProvider: s.llm_provider,
          llmModel: s.llm_model,
          embeddingProvider: s.embedding_provider,
          embeddingModel: s.embedding_model,
        });
      } catch {
        setInfo((prev) => ({ ...prev, backendOnline: true }));
      }
    } else {
      setInfo((prev) => ({ ...prev, backendOnline: false }));
    }

    schedule(() => refresh(), online ? POLL_HEALTHY : POLL_RETRY);
  }, [schedule]);

  useEffect(() => {
    refresh();
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [refresh]);

  return (
    <div className="w-full flex flex-col gap-2">
      <div className="text-xs font-bold uppercase tracking-widest text-center">
        System Status
      </div>

      <div className="flex items-center gap-2 px-1">
        <span
          className={`inline-block w-2.5 h-2.5 rounded-full border-[2px] border-[#1a1a1a] flex-shrink-0 ${
            info.backendOnline ? "bg-[#22c55e]" : "bg-[#ef4444]"
          }`}
        />
        <span className="text-xs font-bold tracking-wide">
          {info.backendOnline ? "CONNECTED" : "OFFLINE"}
        </span>
      </div>

      {info.backendOnline && (
        <>
          <StatusRow
            label="LLM"
            value={
              info.llmProvider && info.llmModel
                ? `${info.llmProvider} / ${info.llmModel}`
                : "—"
            }
          />

          <StatusRow
            label="EMBED"
            value={
              info.embeddingProvider && info.embeddingModel
                ? `${info.embeddingProvider} / ${info.embeddingModel}`
                : "—"
            }
          />
        </>
      )}
    </div>
  );
}

function StatusRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col gap-0.5 px-1">
      <span className="text-[10px] font-bold uppercase tracking-wider opacity-50">
        {label}
      </span>
      <span className="text-[11px] font-mono font-semibold leading-tight truncate">
        {value}
      </span>
    </div>
  );
}
