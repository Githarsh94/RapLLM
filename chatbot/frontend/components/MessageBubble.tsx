import type { Message } from "@/lib/api";

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const time = new Date(message.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  return (
    <div className={`flex mb-3 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex flex-col max-w-[70%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap break-words ${
            isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-800 text-gray-100 rounded-bl-sm"
          }`}
        >
          {message.content}
        </div>
        <span className="text-xs text-gray-600 mt-1 px-1">{time}</span>
      </div>
    </div>
  );
}
