import type { Conversation } from "@/lib/api";

interface Props {
  conversations: Conversation[];
  activeConversationId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onCancel: (id: string) => void;
}

export default function ConversationList({
  conversations,
  activeConversationId,
  onSelect,
  onNew,
  onCancel,
}: Props) {
  const handleCancel = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (window.confirm("Cancel this conversation?")) {
      onCancel(id);
    }
  };

  return (
    <aside className="w-64 bg-gray-900 border-r border-gray-800 flex flex-col h-screen flex-shrink-0">
      <div className="p-4 border-b border-gray-800">
        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3">
          Conversations
        </p>
        <button
          onClick={onNew}
          className="w-full bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium py-2 px-3 rounded-lg transition-colors"
        >
          + New Chat
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        {conversations.length === 0 ? (
          <p className="text-gray-600 text-sm text-center py-8">No conversations yet</p>
        ) : (
          conversations.map((conv) => (
            <div
              key={conv.id}
              onClick={() => onSelect(conv.id)}
              className={`group flex items-start justify-between p-3 rounded-lg mb-1 cursor-pointer transition-colors ${
                conv.id === activeConversationId ? "bg-gray-700" : "hover:bg-gray-800"
              } ${conv.status === "cancelled" ? "opacity-50" : ""}`}
            >
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-200 truncate">{conv.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  {conv.message_count !== undefined && (
                    <span className="text-xs text-gray-500">
                      {conv.message_count} msg{conv.message_count !== 1 ? "s" : ""}
                    </span>
                  )}
                  {conv.status === "cancelled" && (
                    <span className="text-xs bg-gray-700 text-gray-400 px-1.5 py-0.5 rounded">
                      cancelled
                    </span>
                  )}
                </div>
              </div>
              {conv.status === "active" && (
                <button
                  onClick={(e) => handleCancel(e, conv.id)}
                  title="Cancel conversation"
                  className="ml-2 text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 text-xs font-bold"
                >
                  ✕
                </button>
              )}
            </div>
          ))
        )}
      </div>
    </aside>
  );
}
