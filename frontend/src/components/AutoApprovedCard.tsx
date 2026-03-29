interface Props {
  command: string;
  description: string;
}

export function AutoApprovedCard({ command, description }: Props) {
  return (
    <div className="mb-3 max-w-2xl animate-fade-in">
      <div className="flex items-center gap-3 px-4 py-3 bg-surface-low rounded-lg text-sm">
        <span className="material-symbols-outlined text-emerald-500 text-base" style={{ fontVariationSettings: "'FILL' 1" }}>
          check_circle
        </span>
        <div className="min-w-0 flex-1">
          <span className="text-on-surface-variant">{description}</span>
        </div>
        <code className="text-xs font-mono text-outline truncate max-w-[200px]">{command}</code>
      </div>
    </div>
  );
}
