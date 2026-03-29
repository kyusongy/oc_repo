import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, ClientMessage, Phase, ProjectInfo, ServerMessage } from "./types";
import { useWebSocket } from "./hooks/useWebSocket";
import { LandingHero } from "./components/LandingHero";
import { StatusBar } from "./components/StatusBar";
import { ChatWindow } from "./components/ChatWindow";
import { SuccessScreen } from "./components/SuccessScreen";
import { ProjectList } from "./components/ProjectList";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [progress, setProgress] = useState<number | undefined>();
  const [started, setStarted] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [currentProject, setCurrentProject] = useState<ProjectInfo | null>(null);
  const [autoMode, setAutoMode] = useState(true);
  const [isThinking, setIsThinking] = useState(false);
  const [currentTool, setCurrentTool] = useState<{ name: string; description: string } | null>(null);
  const saveTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);

  // Save history when messages change (only once project is known)
  useEffect(() => {
    if (!currentProject || messages.length === 0) return;

    clearTimeout(saveTimeoutRef.current);
    saveTimeoutRef.current = setTimeout(() => {
      fetch(`/api/projects/${encodeURIComponent(currentProject.name)}/history`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(messages),
      }).catch(() => {});
    }, 1000);

    return () => clearTimeout(saveTimeoutRef.current);
  }, [messages, currentProject]);

  const handleMessage = useCallback((msg: ServerMessage) => {
    switch (msg.type) {
      case "agent_message":
        setIsThinking(false);
        setCurrentTool(null);
        setMessages((prev) => [...prev, { kind: "agent", text: msg.text }]);
        break;
      case "approval_request":
        setIsThinking(false);
        setCurrentTool(null);
        setMessages((prev) => [...prev, { kind: "approval", request_id: msg.request_id, command: msg.command, description: msg.description }]);
        break;
      case "user_input_request":
        setIsThinking(false);
        setCurrentTool(null);
        setMessages((prev) => [...prev, { kind: "input", request_id: msg.request_id, question: msg.question, options: msg.options, input_type: msg.input_type }]);
        break;
      case "command_output":
        setCurrentTool(null);
        setMessages((prev) => [...prev, { kind: "output", stream: msg.stream, text: msg.text }]);
        break;
      case "status_update":
        setPhase(msg.phase as Phase);
        setStatusMessage(msg.message);
        setProgress(msg.progress);
        break;
      case "done":
        setIsThinking(false);
        setCurrentTool(null);
        setPhase(msg.success ? "done" : "error");
        setStatusMessage(msg.message);
        break;
      case "project_saved":
        setCurrentProject(msg.project);
        break;
      case "auto_approved":
        setIsThinking(false);
        setCurrentTool(null);
        setMessages((prev) => [...prev, { kind: "auto_approved", command: msg.command, description: msg.description }]);
        break;
      case "tool_start":
        // Transient — replaces previous, not added to message history
        setCurrentTool({ name: msg.tool_name, description: msg.description });
        setIsThinking(false);
        break;
    }
  }, []);

  const { send, connected } = useWebSocket(handleMessage);

  const handleGoHome = () => {
    setStarted(false);
    setPhase("idle");
    setMessages([]);
    setCurrentProject(null);
    setCurrentTool(null);
    setIsThinking(false);
    setStatusMessage("");
    setProgress(undefined);
    setChatInput("");
  };

  const handleViewProject = async (project: ProjectInfo) => {
    setStarted(true);
    setCurrentProject(project);

    try {
      const res = await fetch(`/api/projects/${encodeURIComponent(project.name)}/history`);
      if (res.ok) {
        const history = await res.json();
        if (history.length > 0) {
          setMessages(history);
          setPhase("done");
          setStatusMessage(`${project.name} — viewing session history`.toUpperCase());
          return;
        }
      }
    } catch {}

    setMessages([]);
    setPhase("done");
    setStatusMessage(`${project.name} is installed`.toUpperCase());
  };

  const handleRelaunch = (project: ProjectInfo) => {
    setStarted(true);
    setPhase("scanning");
    setCurrentProject(null);
    setMessages([{ kind: "user", text: `Relaunch ${project.name}` }]);
    send({ type: "start", url: project.url, path: project.path, auto_mode: autoMode });
  };

  const handleUrlSubmit = (url: string) => {
    setStarted(true);
    setPhase("scanning");
    setIsThinking(true);
    setMessages([{ kind: "user", text: url }]);
    send({ type: "start", url, auto_mode: autoMode });
  };

  const handleSend = (msg: ClientMessage) => {
    if (msg.type === "approval" || msg.type === "user_input") {
      setMessages((prev) =>
        prev.map((m) => {
          if ((m.kind === "approval" || m.kind === "input") && m.request_id === msg.request_id) {
            return { ...m, resolved: true };
          }
          return m;
        })
      );
    }
    send(msg);
  };

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim()) return;
    setMessages((prev) => [...prev, { kind: "user", text: chatInput }]);
    send({ type: "message", text: chatInput });
    setChatInput("");
    setIsThinking(true);
    // Drop out of success screen into chat view so user sees agent response
    if (phase === "done") {
      setPhase("installing");
    }
  };

  return (
    <div className="h-screen flex flex-col bg-surface">
      {/* Header */}
      <header className="bg-surface/80 backdrop-blur-md sticky top-0 z-50 shadow-sm">
        <div className="flex justify-between items-center w-full px-6 py-4">
          <div className="flex items-center gap-4">
            <button onClick={handleGoHome} className="text-xl font-bold tracking-tighter text-on-surface font-headline hover:text-tertiary transition-colors">oc_repo</button>
            {started && (
              <>
                <div className="bg-surface-low h-5 w-px mx-2"></div>
                <div className="flex items-center gap-2 px-3 py-1 bg-tertiary/10 rounded-full">
                  <span className={`w-2 h-2 rounded-full ${phase === "done" ? "bg-emerald-500" : phase === "error" ? "bg-error" : "bg-tertiary animate-pulse"}`}></span>
                  <span className="text-[10px] font-body uppercase tracking-widest text-on-surface-variant">
                    {phase === "idle" ? "Ready" : phase}
                  </span>
                </div>
              </>
            )}
          </div>
          <div className="flex items-center gap-4">
            <button className="text-primary hover:text-on-surface transition-colors p-1">
              <span className="material-symbols-outlined">help</span>
            </button>
            <div className={`w-2.5 h-2.5 rounded-full ${connected ? "bg-emerald-500" : "bg-error"}`} title={connected ? "Connected" : "Disconnected"} />
          </div>
        </div>
        <div className="bg-surface-low h-px w-full"></div>
      </header>

      {/* Status bar */}
      <StatusBar phase={phase} message={statusMessage} progress={progress} />

      {/* Main content */}
      {!started ? (
        <>
          <LandingHero onSubmit={handleUrlSubmit} autoMode={autoMode} onToggleMode={() => setAutoMode(!autoMode)} />
          <ProjectList onRelaunch={handleRelaunch} onView={handleViewProject} />
          <footer className="w-full py-8 px-6 border-t border-outline-variant/10">
            <div className="max-w-7xl mx-auto flex justify-between items-center">
              <p className="text-xs font-body uppercase tracking-widest text-on-surface-variant/40">
                &copy; 2026 One-Click Repo
              </p>
            </div>
          </footer>
        </>
      ) : phase === "done" && currentProject ? (
        <SuccessScreen
          project={currentProject}
          lastAgentMessage={messages.filter((m) => m.kind === "agent").pop()?.text || ""}
          chatInput={chatInput}
          onChatInputChange={setChatInput}
          onChatSubmit={handleChatSubmit}
          onGoHome={handleGoHome}
        />
      ) : (
        <>
          <ChatWindow messages={messages} onSend={handleSend} isThinking={isThinking} currentTool={currentTool} />

          {/* Chat input */}
          <footer className="bg-surface p-4 border-t border-outline-variant/10 z-10">
            <form onSubmit={handleChatSubmit} className="max-w-4xl mx-auto">
              <div className="flex items-center gap-3 bg-surface-low rounded-xl p-2 focus-within:bg-surface-lowest focus-within:ring-1 focus-within:ring-primary/20 transition-all">
                <input
                  type="text"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder="Ask a question or type a message..."
                  className="flex-1 bg-transparent border-none focus:ring-0 focus:outline-none py-3 px-4 text-on-surface placeholder:text-on-surface-variant/50 font-body"
                />
                <button
                  type="submit"
                  disabled={!chatInput.trim()}
                  className="signature-cta text-on-primary p-2.5 rounded-lg shadow-sm transition-all active:scale-95 flex items-center justify-center disabled:opacity-40"
                >
                  <span className="material-symbols-outlined">send</span>
                </button>
              </div>
            </form>
          </footer>
        </>
      )}
    </div>
  );
}
