import { useState } from "react";

interface Props {
  stream: "stdout" | "stderr";
  text: string;
}

export function TerminalOutput({ stream, text }: Props) {
  const [expanded, setExpanded] = useState(false);

  const lines = text.split("\n");
  const preview = lines.slice(0, 3).join("\n");
  const hasMore = lines.length > 3;

  return (
    <div className="mb-3 mx-2">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs text-gray-500 hover:text-gray-700 mb-1"
      >
        <span className={`transform transition-transform ${expanded ? "rotate-90" : ""}`}>
          ▶
        </span>
        <span>
          {stream === "stderr" ? "Error output" : "Terminal output"} ({lines.length} lines)
        </span>
      </button>
      <pre
        className={`text-xs font-mono p-3 rounded-lg overflow-x-auto ${
          stream === "stderr"
            ? "bg-red-50 text-red-800 border border-red-200"
            : "bg-gray-900 text-green-400"
        }`}
      >
        {expanded ? text : preview}
        {hasMore && !expanded && (
          <span className="text-gray-500">{"\n"}... click to expand</span>
        )}
      </pre>
    </div>
  );
}
