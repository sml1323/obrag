import { useState, useCallback, useRef } from 'react';

interface UseSSEReturn<T> {
  data: T[];
  isStreaming: boolean;
  error: Error | null;
  startStream: (url: string, body: object, onData?: (chunk: T) => void) => Promise<void>;
  stopStream: () => void;
}

export function useSSE<T>(): UseSSEReturn<T> {
  const [data, setData] = useState<T[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(async (url: string, body: object, onData?: (chunk: T) => void) => {
    // Cancel previous stream if active
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setIsStreaming(true);
    setError(null);
    setData([]);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
        signal: abortController.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      if (!response.body) {
        throw new Error('Response body is unavailable');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || !trimmed.startsWith('data: ')) continue;
          
          const dataStr = trimmed.slice(6);
          if (dataStr === '[DONE]') continue;

          try {
            const parsed = JSON.parse(dataStr) as T;
            setData(prev => [...prev, parsed]);
            onData?.(parsed);
          } catch {
            console.warn('Failed to parse SSE line:', line);
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setError(err instanceof Error ? err : new Error('Unknown SSE error'));
        console.error('SSE Error:', err);
      }
    } finally {
      setIsStreaming(false);
      abortControllerRef.current = null;
    }
  }, []);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setIsStreaming(false);
    }
  }, []);

  return { data, isStreaming, error, startStream, stopStream };
}
