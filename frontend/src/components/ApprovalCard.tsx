interface Props {
  command: string;
  description: string;
  resolved?: boolean;
  onApprove: () => void;
  onDeny: () => void;
}

export function ApprovalCard({ command, description, resolved, onApprove, onDeny }: Props) {
  return (
    <div className="mb-6 max-w-2xl">
      <div className="bg-surface-lowest rounded-lg p-8 shadow-[0_12px_32px_-4px_rgba(45,52,51,0.06)] relative overflow-hidden">
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-tertiary"></div>

        <div className="flex items-start justify-between mb-6">
          <div className="space-y-1">
            <span className="text-[10px] font-body uppercase tracking-[0.1em] text-tertiary font-bold">
              Action Required
            </span>
            <h2 className="text-lg font-headline font-bold text-on-surface tracking-tight">
              Command Approval
            </h2>
          </div>
          <span className="material-symbols-outlined text-tertiary text-2xl">verified_user</span>
        </div>

        <div className="space-y-4 mb-6">
          <div className="bg-surface-low p-4 rounded-md border-l-2 border-primary">
            <p className="text-[10px] font-body uppercase tracking-widest text-on-surface-variant mb-2">Command</p>
            <code className="font-mono text-sm text-primary-dim font-semibold break-all">{command}</code>
          </div>
          <div>
            <p className="text-[10px] font-body uppercase tracking-widest text-on-surface-variant mb-2">Description</p>
            <p className="text-on-surface leading-relaxed text-sm">{description}</p>
          </div>
        </div>

        {resolved ? (
          <p className="text-xs text-on-surface-variant italic">Responded</p>
        ) : (
          <div className="flex gap-4">
            <button
              onClick={onApprove}
              className="signature-cta text-on-primary px-6 py-2.5 rounded-lg text-sm font-semibold shadow-sm hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">check</span>
              Approve
            </button>
            <button
              onClick={onDeny}
              className="px-6 py-2.5 bg-surface-high text-on-surface rounded-lg text-sm font-semibold hover:bg-surface-highest transition-colors"
            >
              Deny
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
