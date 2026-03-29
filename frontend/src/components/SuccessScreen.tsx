import { useState } from "react";
import ReactMarkdown from "react-markdown";
import type { ProjectInfo } from "../types";

interface Props {
  project: ProjectInfo;
  lastAgentMessage: string;
}

export function SuccessScreen({ project, lastAgentMessage }: Props) {
  const [stopping, setStopping] = useState(false);
  const [stopped, setStopped] = useState(false);

  const handleStop = async () => {
    setStopping(true);
    try {
      await fetch(`/api/projects/${encodeURIComponent(project.name)}/stop`, { method: "POST" });
      setStopped(true);
    } catch (e) {
      console.error("Failed to stop:", e);
    } finally {
      setStopping(false);
    }
  };

  const handleOpen = async () => {
    try {
      await fetch(`/api/projects/${encodeURIComponent(project.name)}/open`, { method: "POST" });
    } catch (e) {
      console.error("Failed to open:", e);
    }
  };

  const launchUrl = project.launch_url || (project.ports.length > 0 ? `http://localhost:${project.ports[0]}` : null);

  return (
    <main className="flex-1 overflow-y-auto">
      <div className="max-w-4xl mx-auto px-8 py-12 flex flex-col items-center">
        {/* Checkmark Hero */}
        <div className="mb-8 flex flex-col items-center text-center space-y-4">
          <div className="relative">
            <div className="absolute inset-0 bg-tertiary/20 blur-3xl rounded-full scale-150"></div>
            <div className="relative w-24 h-24 bg-surface-lowest rounded-full flex items-center justify-center shadow-xl">
              <span className="material-symbols-outlined text-tertiary text-5xl" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
            </div>
          </div>
          <h1 className="text-4xl font-headline font-extrabold tracking-tight text-on-surface">
            Launch Ready.
          </h1>
          <p className="text-on-surface-variant max-w-lg text-lg leading-relaxed">
            {project.name} has been successfully installed and deployed to your local environment.
          </p>
        </div>

        {/* Agent Summary Card */}
        <div className="w-full max-w-2xl bg-surface-lowest rounded-lg shadow-[0_12px_32px_-4px_rgba(45,52,51,0.06)] border-l-4 border-tertiary p-8 mb-8 relative overflow-hidden">
          <div className="flex gap-4 items-start">
            <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center flex-shrink-0">
              <span className="material-symbols-outlined text-primary">smart_toy</span>
            </div>
            <div className="space-y-3 min-w-0">
              <span className="text-[10px] font-body uppercase tracking-widest text-outline">System Agent</span>
              <div className="prose prose-sm max-w-none text-on-surface leading-relaxed [&_p]:my-1 [&_code]:bg-surface-low [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-primary-dim [&_code]:font-mono [&_code]:text-xs">
                <ReactMarkdown>{lastAgentMessage}</ReactMarkdown>
              </div>

              {launchUrl && (
                <div className="pt-4 flex flex-col items-center">
                  <a
                    href={launchUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="signature-cta text-on-primary px-10 py-4 rounded-lg font-headline font-bold text-lg shadow-lg hover:scale-[1.02] transition-transform flex items-center gap-3"
                  >
                    Launch App
                    <span className="material-symbols-outlined">rocket_launch</span>
                  </a>
                  <span className="mt-3 text-sm font-mono text-outline">{launchUrl}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Action Cards Grid */}
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
          {/* Stop App */}
          <div className="bg-surface-lowest rounded-lg p-8 shadow-[0_4px_20px_-4px_rgba(45,52,51,0.04)] flex flex-col justify-between">
            <div>
              <span className="material-symbols-outlined text-error mb-4 block text-3xl">stop_circle</span>
              <h3 className="font-headline text-xl font-bold mb-2">Stop App</h3>
              <p className="text-on-surface-variant text-sm leading-relaxed">
                Shut down the local development server and release occupied ports.
              </p>
            </div>
            <div className="mt-6">
              {stopped ? (
                <span className="text-emerald-600 font-bold text-sm flex items-center gap-2">
                  <span className="material-symbols-outlined text-sm" style={{ fontVariationSettings: "'FILL' 1" }}>check_circle</span>
                  Stopped
                </span>
              ) : (
                <button
                  onClick={handleStop}
                  disabled={stopping}
                  className="text-error font-bold text-sm hover:underline decoration-2 underline-offset-4 disabled:opacity-50"
                >
                  {stopping ? "Stopping..." : "Terminate Process"}
                </button>
              )}
            </div>
          </div>

          {/* Open Project Folder */}
          <div className="bg-surface-low rounded-lg p-8 flex flex-col justify-between">
            <div>
              <span className="material-symbols-outlined text-primary mb-4 block text-3xl">folder_open</span>
              <h3 className="font-headline text-xl font-bold mb-2">Open Project Folder</h3>
              <p className="text-on-surface-variant text-sm leading-relaxed">
                Access the source files directly in your local directory.
              </p>
              <p className="text-xs font-mono text-outline mt-2 break-all">{project.path}</p>
            </div>
            <div className="mt-6">
              <button
                onClick={handleOpen}
                className="text-primary font-bold text-sm hover:underline decoration-2 underline-offset-4 flex items-center gap-1"
              >
                <span className="material-symbols-outlined text-sm">open_in_new</span>
                Open in Finder
              </button>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <button
          onClick={() => window.location.reload()}
          className="text-primary text-sm font-semibold hover:underline decoration-2 underline-offset-4 flex items-center gap-2"
        >
          <span className="material-symbols-outlined text-sm">arrow_back</span>
          Back to Home
        </button>
      </div>
    </main>
  );
}
