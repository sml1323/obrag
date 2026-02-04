import { request } from "./client";
import {
  ChatSession,
  Message,
  SessionCreate,
  SessionUpdate,
} from "../types/sessions";

export async function listSessions(
  topicId?: number,
  offset: number = 0,
  limit: number = 100,
): Promise<ChatSession[]> {
  const params = new URLSearchParams();
  if (topicId) params.append("topic_id", topicId.toString());
  params.append("offset", offset.toString());
  params.append("limit", limit.toString());

  return request<ChatSession[]>(`/sessions?${params.toString()}`);
}

export async function createSession(data: SessionCreate): Promise<ChatSession> {
  return request<ChatSession>("/sessions", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function updateSession(
  sessionId: string,
  data: SessionUpdate,
): Promise<ChatSession> {
  return request<ChatSession>(`/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify(data),
  });
}

export async function deleteSession(
  sessionId: string,
): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/sessions/${sessionId}`, {
    method: "DELETE",
  });
}

export async function getSessionMessages(
  sessionId: string,
): Promise<Message[]> {
  return request<Message[]>(`/sessions/${sessionId}/messages`);
}

export async function addMessage(
  sessionId: string,
  data: Message,
): Promise<Message> {
  return request<Message>(`/sessions/${sessionId}/messages`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}
