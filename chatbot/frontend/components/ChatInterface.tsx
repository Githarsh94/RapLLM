"use client";

import { useState, useRef, useEffect } from "react";
import type { Conversation } from "@/lib/api";
import MessageBubble from "./MessageBubble";

// Models confirmed available on the free tier (API key, no billing required)
const GEMINI_MODELS = [
  { id: "", label: "Default" },
  { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash" },
  { id: "gemini-3.5-flash", label: "Gemini 3.5 Flash" },
];

function friendlyError(raw: string): string {
  if (raw.includes("RESOURCE_EXHAUSTED"))
    return "Rate limit exceeded — you've hit your API quota. Wait a moment and try again.";
  if (raw.includes("NOT_FOUND"))
    return "Model not found or not supported by your API plan.";
  if (raw.includes("UNAVAILABLE"))
    return "Model is currently unavailable due to high demand. Try again later.";
  return raw;
}

interface Props {
  conversation: Conversation | null;
  isLoading: boolean;
  onSendMessage: (content: string, model: string | null) => void;
  errorMessage?: string | null;
  onDismissError?: () => void;
}

function extractWarningText(messages: Conversation["messages"]): string | null {
  if (!messages) return null;
  for (const msg of messages) {
    try {
      const parsed = JSON.parse(msg.content);
      if (parsed.__gemini_parts && Array.isArray(parsed.parts)) {
        const warning = parsed.parts.find((p: { type: string }) => p.type === "warning");
        if (warning) return warning.text;
      }
    } catch {}
  }
  return null;
}

export default function ChatInterface({ conversation, isLoading, onSendMessage, errorMessage, onDismissError }: Props) {
  const [input, setInput] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [showWarning, setShowWarning] = useState(false);
  const [warningText, setWarningText] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setShowWarning(false);
    setWarningText("");
  }, [conversation?.id]);

  useEffect(() => {
    if (!showWarning) {
      const text = extractWarningText(conversation?.messages);
      if (text) {
        setWarningText(text);
        setShowWarning(true);
      }
    }
  }, [conversation?.messages]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [conversation?.messages, isLoading]);

  const handleSend = () => {
    const trimmed = input.trim();
    if (!trimmed || isLoading) return;
    onSendMessage(trimmed, selectedModel || null);
    setInput("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isCancelled = conversation?.status === "cancelled";

  if (!conversation) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-950">
        <div className="text-center">
          <p className="text-gray-600 text-lg">Select or start a conversation</p>
          <p className="text-gray-700 text-sm mt-1">
            Choose from the sidebar or click &quot;New Chat&quot;
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-gray-950 min-w-0">
      <div className="px-6 py-4 border-b border-gray-800 flex items-center gap-3 flex-shrink-0">
        <h2 className="text-gray-200 font-medium truncate">{conversation.title}</h2>
        {isCancelled && (
          <span className="text-xs bg-gray-800 text-gray-400 px-2 py-1 rounded-full flex-shrink-0">
            Cancelled
          </span>
        )}
      </div>

      {showWarning && (
        <div className="flex items-start gap-3 px-4 py-3 bg-amber-950 border-b border-amber-700 text-amber-300 text-sm flex-shrink-0">
          <span className="flex-1 leading-relaxed">⚠️ {warningText}</span>
          <button
            onClick={() => setShowWarning(false)}
            className="flex-shrink-0 text-amber-400 hover:text-amber-200 transition-colors mt-0.5"
            aria-label="Dismiss warning"
          >
            ✕
          </button>
        </div>
      )}

      {errorMessage && (
        <div className="flex items-start gap-3 px-4 py-3 bg-red-950 border-b border-red-800 text-red-300 text-sm flex-shrink-0">
          <span className="flex-1 leading-relaxed">❌ {friendlyError(errorMessage)}</span>
          <button
            onClick={onDismissError}
            className="flex-shrink-0 text-red-400 hover:text-red-200 transition-colors mt-0.5"
            aria-label="Dismiss error"
          >
            ✕
          </button>
        </div>
      )}

      <div className="flex-1 overflow-y-auto px-6 py-4">
        {(!conversation.messages || conversation.messages.length === 0) && (
          <p className="text-gray-600 text-sm text-center py-8">Send a message to get started</p>
        )}
        {conversation.messages?.map((msg) => (
          <MessageBubble key={msg.id} message={msg} />
        ))}
        {isLoading && (
          <div className="flex gap-1 py-2 pl-2 items-center">
            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:0ms]" />
            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:150ms]" />
            <span className="w-2 h-2 bg-gray-500 rounded-full animate-bounce [animation-delay:300ms]" />
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <div className="px-6 py-4 border-t border-gray-800 flex-shrink-0">
        {isCancelled ? (
          <p className="text-center text-gray-500 text-sm py-2">
            This conversation has been cancelled. Start a new one from the sidebar.
          </p>
        ) : (
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="bg-gray-800 text-gray-300 text-xs rounded-lg px-2 py-1 border border-gray-700 outline-none focus:ring-1 focus:ring-blue-600 cursor-pointer"
              >
                {GEMINI_MODELS.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.label}
                  </option>
                ))}
              </select>
            </div>
            <div className="flex gap-3 items-end">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Type a message… (Enter to send, Shift+Enter for new line)"
                rows={1}
                className="flex-1 bg-gray-800 text-gray-100 placeholder-gray-500 rounded-xl px-4 py-3 resize-none outline-none focus:ring-2 focus:ring-blue-600 text-sm"
                style={{ maxHeight: "120px" }}
              />
              <button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 disabled:text-gray-500 text-white font-medium px-4 py-3 rounded-xl transition-colors text-sm flex-shrink-0"
              >
                Send
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
