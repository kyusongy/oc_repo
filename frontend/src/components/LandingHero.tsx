import { useState } from "react";

interface Props {
  onSubmit: (url: string) => void;
  autoMode: boolean;
  onToggleMode: () => void;
}

export function LandingHero({ onSubmit, autoMode, onToggleMode }: Props) {
  const [url, setUrl] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) onSubmit(url.trim());
  };

  return (
    <main className="py-20 flex flex-col items-center justify-center px-6 relative overflow-hidden">
      {/* Background blurs */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full h-full pointer-events-none opacity-40">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary-container/20 blur-[120px] rounded-full"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-tertiary-container/10 blur-[120px] rounded-full"></div>
      </div>

      <section className="max-w-3xl w-full flex flex-col items-center text-center space-y-12 z-10">
        <div className="space-y-4">
          <span className="font-body uppercase tracking-[0.1em] text-primary font-semibold opacity-80 text-xs">
            One-Click Installer
          </span>
          <h1 className="text-5xl lg:text-6xl font-headline font-extrabold tracking-tight text-on-surface leading-tight">
            Install. Configure. <span className="text-tertiary">Launch.</span>
          </h1>
          <p className="text-on-surface-variant max-w-xl mx-auto leading-relaxed text-lg">
            Paste any GitHub repository URL and let the agent handle the rest — dependencies, configuration, and launch. No terminal skills needed.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="w-full max-w-2xl space-y-6">
          <div className="group relative flex items-center p-2 bg-surface-lowest rounded-xl shadow-[0_12px_32px_-4px_rgba(45,52,51,0.06)] ring-1 ring-outline-variant/10 focus-within:ring-primary/30 transition-all duration-300">
            <div className="pl-4 flex items-center pointer-events-none text-on-surface-variant/50">
              <span className="material-symbols-outlined text-2xl">link</span>
            </div>
            <input
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full bg-transparent border-none focus:ring-0 focus:outline-none text-on-surface text-lg font-body px-4 py-4 placeholder:text-on-surface-variant/40"
              placeholder="Paste a GitHub repository URL..."
            />
            <button
              type="submit"
              disabled={!url.trim()}
              className="signature-cta text-on-primary px-8 py-4 rounded-lg font-headline font-bold text-sm tracking-wide shadow-lg hover:shadow-xl hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
            >
              Install
              <span className="material-symbols-outlined text-lg">arrow_forward</span>
            </button>
          </div>

          <div className="flex flex-wrap justify-center gap-x-8 gap-y-3 px-4">
            <div className="flex items-center gap-2 text-on-surface-variant/60 text-sm">
              <span className="material-symbols-outlined text-[18px]">verified</span>
              <span>Automatic setup</span>
            </div>
            <div className="flex items-center gap-2 text-on-surface-variant/60 text-sm">
              <span className="material-symbols-outlined text-[18px]">account_tree</span>
              <span>Dependency installation</span>
            </div>
            <div className="flex items-center gap-2 text-on-surface-variant/60 text-sm">
              <span className="material-symbols-outlined text-[18px]">rocket_launch</span>
              <span>One-click launch</span>
            </div>
          </div>

          <div className="flex items-center justify-center gap-3 mt-4">
            <span className={`text-sm font-body ${!autoMode ? 'text-on-surface font-semibold' : 'text-on-surface-variant'}`}>
              Safe Mode
            </span>
            <button
              type="button"
              onClick={(e) => { e.preventDefault(); onToggleMode(); }}
              className={`relative w-12 h-6 rounded-full transition-colors ${autoMode ? 'bg-tertiary' : 'bg-outline-variant'}`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow-sm transition-transform ${autoMode ? 'translate-x-6' : ''}`} />
            </button>
            <span className={`text-sm font-body ${autoMode ? 'text-on-surface font-semibold' : 'text-on-surface-variant'}`}>
              Auto Mode
            </span>
          </div>
        </form>
      </section>
    </main>
  );
}
