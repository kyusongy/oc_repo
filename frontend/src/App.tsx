import { useCallback, useState } from "react";
import type { ChatMessage, ClientMessage, Phase, ServerMessage } from "./types";
import { useWebSocket } from "./hooks/useWebSocket";
import { UrlInput } from "./components/UrlInput";
import { StatusBar } from "./components/StatusBar";
import { ChatWindow } from "./components/ChatWindow";

export default function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [phase, setPhase] = useState<Phase>("idle");
  const [statusMessage, setStatusMessage] = useState("");
  const [progress, setProgress] = useState<number | undefined>();
  const [started, setStarted] = useState(false);
  const [chatInput, setChatInput] = useState("");

  const handleMessage = useCallback((msg: ServerMessage) => {
    switch (msg.type) {
      case "agent_message":
        setMessages((prev) => [...prev, { kind: "agent", text: msg.text }]);
        break;
      case "approval_request":
        setMessages((prev) => [...prev, { kind: "approval", request_id: msg.request_id, command: msg.command, description: msg.description }]);
        break;
      case "user_input_request":
        setMessages((prev) => [...prev, { kind: "input", request_id: msg.request_id, question: msg.question, options: msg.options, input_type: msg.input_type }]);
        break;
      case "command_output":
        setMessages((prev) => [...prev, { kind: "output", stream: msg.stream, text: msg.text }]);
        break;
      case "status_update":
        setPhase(msg.phase as Phase);
        setStatusMessage(msg.message);
        setProgress(msg.progress);
        break;
      case "done":
        setPhase(msg.success ? "done" : "error");
        setStatusMessage(msg.message);
        break;
    }
  }, []);

  const { send, connected } = useWebSocket(handleMessage);

  const handleUrlSubmit = (url: string) => {
    setStarted(true);
    setPhase("scanning");
    setMessages([{ kind: "user", text: url }]);
    send({ type: "start", url });
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
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-900">One-Click Repo</h1>
        <div className={`w-2 h-2 rounded-full ${connected ? "bg-green-500" : "bg-red-500"}`} title={connected ? "Connected" : "Disconnected"} />
      </header>

      <StatusBar phase={phase} message={statusMessage} progress={progress} />

      {!started && <UrlInput onSubmit={handleUrlSubmit} />}

      <ChatWindow messages={messages} onSend={handleSend} />

      {started && (
        <form onSubmit={handleChatSubmit} className="flex gap-2 p-4 border-t border-gray-200">
          <input type="text" value={chatInput} onChange={(e) => setChatInput(e.target.value)} placeholder="Type a message..." className="flex-1 px-4 py-2 rounded-lg border border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500" />
          <button type="submit" disabled={!chatInput.trim()} className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors">
            Send
          </button>
        </form>
      )}
    </div>
  );
}
