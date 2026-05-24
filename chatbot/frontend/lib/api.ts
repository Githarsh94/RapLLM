export interface Conversation {
  id: string;
  title: string;
  status: "active" | "cancelled";
  created_at: string;
  updated_at: string;
  message_count?: number;
  messages?: Message[];
}

export interface Message {
  id: string;
  conversation_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

const API_BASE = "/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function createConversation(title = "New Conversation"): Promise<Conversation> {
  return request("/conversations", {
    method: "POST",
    body: JSON.stringify({ title }),
  });
}

export async function listConversations(): Promise<Conversation[]> {
  return request("/conversations");
}

export async function getConversation(id: string): Promise<Conversation> {
  return request(`/conversations/${id}`);
}

export async function sendMessage(conversationId: string, content: string, model?: string): Promise<Message> {
  return request(`/conversations/${conversationId}/messages`, {
    method: "POST",
    body: JSON.stringify({ content, model: model ?? null }),
  });
}

export async function cancelConversation(id: string): Promise<Conversation> {
  return request(`/conversations/${id}/cancel`, { method: "PATCH" });
}
