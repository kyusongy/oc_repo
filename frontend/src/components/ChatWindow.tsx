import { useEffect, useRef } from "react";
import type { ChatMessage, ClientMessage } from "../types";
import { MessageBubble } from "./MessageBubble";
import { ApprovalCard } from "./ApprovalCard";
import { UserInputWidget } from "./UserInputWidget";
import { TerminalOutput } from "./TerminalOutput";
import { ThinkingIndicator } from "./ThinkingIndicator";
import { AutoApprovedCard } from "./AutoApprovedCard";
import { ToolStartCard } from "./ToolStartCard";

interface Props {
  messages: ChatMessage[];
  onSend: (msg: ClientMessage) => void;
  isThinking?: boolean;
  currentTool?: { name: string; description: string } | null;
}

export function ChatWindow({ messages, onSend, isThinking, currentTool }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, currentTool, isThinking]);

  return (
    <div className="flex-1 overflow-y-auto px-8 py-8">
      <div className="max-w-4xl mx-auto">
        {messages.length === 0 && (
          <div className="text-center text-on-surface-variant/40 mt-20">
            <span className="material-symbols-outlined text-5xl mb-4 block">smart_toy</span>
            <p className="text-lg font-headline">Waiting for repository...</p>
          </div>
        )}

        {messages.map((msg, i) => {
          switch (msg.kind) {
            case "agent":
              return <div key={i} className="animate-fade-in"><MessageBubble role="agent" text={msg.text} /></div>;
            case "user":
              return <div key={i} className="animate-fade-in"><MessageBubble role="user" text={msg.text} /></div>;
            case "approval":
              return (
                <div key={i} className="animate-fade-in">
                  <ApprovalCard
                    command={msg.command}
                    description={msg.description}
                    resolved={msg.resolved}
                    onApprove={() => onSend({ type: "approval", request_id: msg.request_id, approved: true })}
                    onDeny={() => onSend({ type: "approval", request_id: msg.request_id, approved: false })}
                  />
                </div>
              );
            case "input":
              return (
                <div key={i} className="animate-fade-in">
                  <UserInputWidget
                    question={msg.question}
                    options={msg.options}
                    inputType={msg.input_type}
                    resolved={msg.resolved}
                    onSubmit={(value) => onSend({ type: "user_input", request_id: msg.request_id, value })}
                  />
                </div>
              );
            case "output":
              return <div key={i} className="animate-fade-in"><TerminalOutput stream={msg.stream} text={msg.text} /></div>;
            case "auto_approved":
              return <AutoApprovedCard key={i} command={msg.command} description={msg.description} />;
          }
        })}

        {currentTool && <ToolStartCard toolName={currentTool.name} description={currentTool.description} />}
        {isThinking && !currentTool && <ThinkingIndicator />}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
