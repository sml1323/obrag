import { request } from "./client";
import { Topic } from "../types/sessions";

export async function listTopics(): Promise<Topic[]> {
  return request<Topic[]>("/topics");
}

export async function createTopic(data: Topic): Promise<Topic> {
  return request<Topic>("/topics", {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function deleteTopic(topicId: number): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`/topics/${topicId}`, {
    method: "DELETE",
  });
}
