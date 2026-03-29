export function ThinkingIndicator() {
  return (
    <div className="mb-6 max-w-2xl animate-fade-in">
      <div className="flex items-center gap-3 px-8 py-4">
        <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
          <span className="material-symbols-outlined text-primary text-sm">smart_toy</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-tertiary thinking-dot"></div>
          <div className="w-2 h-2 rounded-full bg-tertiary thinking-dot"></div>
          <div className="w-2 h-2 rounded-full bg-tertiary thinking-dot"></div>
        </div>
      </div>
    </div>
  );
}
