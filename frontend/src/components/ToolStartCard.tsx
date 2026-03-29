interface Props {
  toolName: string;
  description: string;
}

export function ToolStartCard({ toolName: _toolName, description }: Props) {
  return (
    <div className="mb-3 max-w-2xl animate-fade-in">
      <div className="flex items-center gap-3 px-4 py-3 bg-tertiary/5 rounded-lg text-sm">
        <span className="material-symbols-outlined text-tertiary text-base animate-spin">progress_activity</span>
        <span className="text-on-surface-variant">{description}</span>
      </div>
    </div>
  );
}
