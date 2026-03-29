import ReactMarkdown from "react-markdown";

interface Props {
  role: "agent" | "user";
  text: string;
}

export function MessageBubble({ role, text }: Props) {
  const isAgent = role === "agent";

  return (
    <div className={`flex ${isAgent ? "justify-start" : "justify-end"} mb-3`}>
      <div
        className={`max-w-[80%] px-4 py-3 rounded-2xl ${
          isAgent
            ? "bg-gray-100 text-gray-900 rounded-bl-sm"
            : "bg-blue-600 text-white rounded-br-sm"
        }`}
      >
        {isAgent ? (
          <div className="prose prose-sm max-w-none prose-p:my-1 prose-ul:my-1 prose-li:my-0">
            <ReactMarkdown>{text}</ReactMarkdown>
          </div>
        ) : (
          <p className="text-sm whitespace-pre-wrap">{text}</p>
        )}
      </div>
    </div>
  );
}
