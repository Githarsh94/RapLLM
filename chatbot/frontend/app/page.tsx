"use client";

import { useState, useEffect } from "react";
import ConversationList from "@/components/ConversationList";
import ChatInterface from "@/components/ChatInterface";
import {
  type Conversation,
  type Message,
  createConversation,
  listConversations,
  getConversation,
  sendMessage,
  cancelConversation,
} from "@/lib/api";

export default function Home() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  const [activeConversation, setActiveConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [sendError, setSendError] = useState<string | null>(null);

  useEffect(() => {
    listConversations().then(setConversations).catch(console.error);
  }, []);

  useEffect(() => {
    if (!activeConversationId) {
      setActiveConversation(null);
      return;
    }
    getConversation(activeConversationId).then(setActiveConversation).catch(console.error);
  }, [activeConversationId]);

  const handleNewConversation = async () => {
    const conv = await createConversation();
    setConversations((prev) => [{ ...conv, message_count: 0 }, ...prev]);
    setActiveConversationId(conv.id);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
  };

  const handleCancelConversation = async (id: string) => {
    await cancelConversation(id);
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "cancelled" as const } : c))
    );
    if (activeConversation?.id === id) {
      setActiveConversation((prev) =>
        prev ? { ...prev, status: "cancelled" as const } : null
      );
    }
  };

  const handleSendMessage = async (content: string, model: string | null) => {
    if (!activeConversationId || !activeConversation) return;
    setSendError(null);

    const optimisticUserMsg: Message = {
      id: crypto.randomUUID(),
      conversation_id: activeConversationId,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    };

    setActiveConversation((prev) =>
      prev ? { ...prev, messages: [...(prev.messages ?? []), optimisticUserMsg] } : null
    );
    setIsLoading(true);

    try {
      const assistantMsg = await sendMessage(activeConversationId, content, model ?? undefined);
      setActiveConversation((prev) =>
        prev ? { ...prev, messages: [...(prev.messages ?? []), assistantMsg] } : null
      );
      setConversations((prev) =>
        prev.map((c) =>
          c.id === activeConversationId
            ? { ...c, message_count: (c.message_count ?? 0) + 2 }
            : c
        )
      );
    } catch (err) {
      console.error("Failed to send message:", err);
      setSendError(err instanceof Error ? err.message : "Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <main className="flex h-screen overflow-hidden">
      <ConversationList
        conversations={conversations}
        activeConversationId={activeConversationId}
        onSelect={handleSelectConversation}
        onNew={handleNewConversation}
        onCancel={handleCancelConversation}
      />
      <ChatInterface
        conversation={activeConversation}
        isLoading={isLoading}
        onSendMessage={handleSendMessage}
        errorMessage={sendError}
        onDismissError={() => setSendError(null)}
      />
    </main>
  );
}
