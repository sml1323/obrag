export interface Topic {
  id?: number;
  title: string;
  created_at?: string;
}

export interface ChatSession {
  id: string;
  topic_id?: number;
  title: string;
  created_at?: string;
}

export interface SessionCreate {
  title: string;
  topic_id?: number;
}

export interface SessionUpdate {
  title?: string;
  topic_id?: number | null;
}

export interface Message {
  id?: number;
  session_id?: string;
  role: "user" | "assistant";
  content: string;
  created_at?: string;
}
