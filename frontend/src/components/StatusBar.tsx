import type { Phase } from "../types";

const PHASE_LABELS: Record<Phase, string> = {
  idle: "Ready",
  scanning: "Scanning repo...",
  installing: "Installing...",
  launching: "Launching...",
  done: "Done!",
  error: "Error",
};

const PHASE_COLORS: Record<Phase, string> = {
  idle: "bg-gray-200 text-gray-600",
  scanning: "bg-yellow-100 text-yellow-800",
  installing: "bg-blue-100 text-blue-800",
  launching: "bg-purple-100 text-purple-800",
  done: "bg-green-100 text-green-800",
  error: "bg-red-100 text-red-800",
};

interface Props {
  phase: Phase;
  message?: string;
  progress?: number;
}

export function StatusBar({ phase, message, progress }: Props) {
  if (phase === "idle") return null;

  return (
    <div className={`px-4 py-2 text-sm font-medium ${PHASE_COLORS[phase]}`}>
      <div className="flex items-center justify-between">
        <span>{message || PHASE_LABELS[phase]}</span>
        {progress != null && (
          <span className="text-xs">{Math.round(progress)}%</span>
        )}
      </div>
      {progress != null && (
        <div className="mt-1 h-1 bg-black/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-current rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}
    </div>
  );
}
