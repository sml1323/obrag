import { BACKEND_URL, request } from "./client";
import { ChatRequest, ChatResponse, SSEEvent } from "../types/chat";

export async function askQuestion(data: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>("/chat", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function* streamChat(
  data: ChatRequest,
): AsyncGenerator<SSEEvent, void, unknown> {
  const response = await fetch(`${BACKEND_URL}/chat/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const json = await response.json().catch(() => ({}));
    throw new Error(json.detail || "Streaming failed");
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("No reader available");

  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || !trimmed.startsWith("data: ")) continue;

      const dataStr = trimmed.substring(6);
      if (dataStr === "[DONE]") continue;

      try {
        const event: SSEEvent = JSON.parse(dataStr);
        yield event;
      } catch (e) {
        console.error("Failed to parse SSE event", e, dataStr);
      }
    }
  }
}
