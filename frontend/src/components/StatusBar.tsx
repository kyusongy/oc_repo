import type { Phase } from "../types";

interface Props {
  phase: Phase;
  message?: string;
  progress?: number;
}

export function StatusBar({ phase, message, progress }: Props) {
  if (phase === "idle") return null;

  const labels: Record<Phase, string> = {
    idle: "",
    scanning: "Scanning Repository...",
    installing: "Installing Dependencies...",
    launching: "Launching Application...",
    done: "Installation Complete!",
    error: "Error Occurred",
  };

  const isDone = phase === "done";
  const isError = phase === "error";

  return (
    <div className={`px-8 py-3 ${isDone ? "bg-tertiary/10" : isError ? "bg-error/10" : "bg-primary-container"}`}>
      <div className="max-w-4xl mx-auto flex items-center justify-between">
        <div className="flex items-center gap-3">
          {isDone ? (
            <span className="material-symbols-outlined text-tertiary text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
          ) : isError ? (
            <span className="material-symbols-outlined text-error text-sm">error</span>
          ) : (
            <span className="flex h-2 w-2 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
          )}
          <span className="text-xs font-body font-bold tracking-wider uppercase text-on-surface-variant">
            {message || labels[phase]}
          </span>
        </div>
        {progress != null && !isDone && (
          <div className="w-48 h-1 bg-surface-high rounded-full overflow-hidden">
            <div
              className="h-full bg-tertiary rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            />
          </div>
        )}
      </div>
    </div>
  );
}
