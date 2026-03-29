import { useEffect, useState } from "react";
import type { ProjectInfo } from "../types";

interface Props {
  onRelaunch: (project: ProjectInfo) => void;
  onView: (project: ProjectInfo) => void;
}

export function ProjectList({ onRelaunch, onView }: Props) {
  const [projects, setProjects] = useState<ProjectInfo[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchProjects = async () => {
    try {
      const res = await fetch("/api/projects");
      if (res.ok) {
        setProjects(await res.json());
      }
    } catch {
      // Backend not running yet
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchProjects(); }, []);

  const handleStop = async (name: string) => {
    await fetch(`/api/projects/${encodeURIComponent(name)}/stop`, { method: "POST" });
    fetchProjects();
  };

  const handleRemove = async (name: string) => {
    if (!window.confirm(`Remove ${name}? This will stop the app and delete all files.`)) return;
    await fetch(`/api/projects/${encodeURIComponent(name)}`, { method: "DELETE" });
    fetchProjects();
  };

  if (loading || projects.length === 0) return null;

  return (
    <div className="w-full max-w-3xl mx-auto px-6 pb-12 z-10 relative">
      <div className="flex items-center gap-4 mb-6">
        <h2 className="font-headline font-bold text-lg text-on-surface">Your Projects</h2>
        <div className="flex-1 h-px bg-surface-high"></div>
      </div>

      <div className="space-y-3">
        {projects.map((p) => (
          <div
            key={p.name}
            className="bg-surface-lowest rounded-lg p-6 shadow-[0_4px_20px_-4px_rgba(45,52,51,0.04)] flex items-center justify-between gap-4"
          >
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-3 mb-1">
                <button onClick={() => onView(p)} className="font-headline font-bold text-on-surface truncate hover:text-tertiary transition-colors">
                  {p.name}
                </button>
                <span className={`flex items-center gap-1.5 text-[10px] font-body uppercase tracking-widest ${p.status === "running" ? "text-emerald-600" : "text-on-surface-variant"}`}>
                  <span className={`w-1.5 h-1.5 rounded-full ${p.status === "running" ? "bg-emerald-500" : "bg-outline-variant"}`}></span>
                  {p.status}
                </span>
              </div>
              <p className="text-xs font-mono text-on-surface-variant truncate">{p.url}</p>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              {p.status === "running" ? (
                <button
                  onClick={() => handleStop(p.name)}
                  className="px-3 py-1.5 text-xs font-semibold text-error bg-error/10 rounded-md hover:bg-error/20 transition-colors"
                >
                  Stop
                </button>
              ) : (
                <button
                  onClick={() => onRelaunch(p)}
                  className="signature-cta px-3 py-1.5 text-xs font-semibold text-on-primary rounded-md"
                >
                  Relaunch
                </button>
              )}
              <button
                onClick={() => handleRemove(p.name)}
                className="px-3 py-1.5 text-xs font-semibold text-on-surface-variant bg-surface-high rounded-md hover:bg-surface-highest transition-colors"
              >
                Remove
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
