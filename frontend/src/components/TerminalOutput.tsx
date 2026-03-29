import { useState } from "react";

interface Props {
  stream: "stdout" | "stderr";
  text: string;
}

export function TerminalOutput({ stream, text }: Props) {
  const [expanded, setExpanded] = useState(false);

  const lines = text.split("\n");
  const preview = lines.slice(0, 4).join("\n");
  const hasMore = lines.length > 4;

  return (
    <div className="mb-4 max-w-2xl">
      <div className="bg-inverse-surface rounded-lg overflow-hidden">
        <div className="px-4 py-2 flex items-center justify-between border-b border-white/5">
          <div className="flex items-center gap-3">
            <div className="flex gap-1.5">
              <div className="w-2 h-2 rounded-full bg-error/40"></div>
              <div className="w-2 h-2 rounded-full bg-amber-400/40"></div>
              <div className="w-2 h-2 rounded-full bg-emerald-400/40"></div>
            </div>
            <span className="text-[10px] font-mono text-on-surface-variant/60 uppercase tracking-widest">
              {stream === "stderr" ? "Error Output" : "Terminal"}
            </span>
          </div>
          {hasMore && (
            <button
              onClick={() => setExpanded(!expanded)}
              className="text-on-surface-variant/60 hover:text-white transition-colors"
            >
              <span className="material-symbols-outlined text-sm">
                {expanded ? "keyboard_arrow_up" : "keyboard_arrow_down"}
              </span>
            </button>
          )}
        </div>
        <pre className={`p-4 font-mono text-xs leading-relaxed overflow-x-auto ${
          stream === "stderr" ? "text-red-400" : "text-primary-container"
        } ${expanded ? "max-h-96" : "max-h-32"} overflow-y-auto transition-all`}>
          {expanded ? text : preview}
          {hasMore && !expanded && (
            <span className="text-on-surface-variant/30">{"\n"}... {lines.length - 4} more lines</span>
          )}
        </pre>
      </div>
    </div>
  );
}
