import type { Message } from "@/lib/api";

interface TextPart {
  type: "text";
  text: string;
}

interface ImagePart {
  type: "image";
  data: string;
  mime_type: string;
}

interface WarningPart {
  type: "warning";
  text: string;
}

type GeminiPart = TextPart | ImagePart | WarningPart;

function parseContent(content: string): GeminiPart[] {
  try {
    const parsed = JSON.parse(content);
    if (parsed.__gemini_parts && Array.isArray(parsed.parts)) {
      return parsed.parts as GeminiPart[];
    }
  } catch {}
  return [{ type: "text", text: content }];
}

interface Props {
  message: Message;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";
  const time = new Date(message.created_at).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  const parts = parseContent(message.content);

  return (
    <div className={`flex mb-3 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex flex-col max-w-[70%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed ${
            isUser
              ? "bg-blue-600 text-white rounded-br-sm"
              : "bg-gray-800 text-gray-100 rounded-bl-sm"
          }`}
        >
          {parts.map((part, i) =>
            part.type === "image" ? (
              <img
                key={i}
                src={`data:${part.mime_type};base64,${part.data}`}
                alt="Generated image"
                className="rounded-lg max-w-full mt-1"
              />
            ) : part.type === "warning" ? null : (
              <p key={i} className="whitespace-pre-wrap break-words">
                {part.text}
              </p>
            )
          )}
        </div>
        <span className="text-xs text-gray-600 mt-1 px-1">{time}</span>
      </div>
    </div>
  );
}
