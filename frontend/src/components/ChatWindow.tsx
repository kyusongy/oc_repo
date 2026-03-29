import { useEffect, useRef } from "react";
import type { ChatMessage, ClientMessage } from "../types";
import { MessageBubble } from "./MessageBubble";
import { ApprovalCard } from "./ApprovalCard";
import { UserInputWidget } from "./UserInputWidget";
import { TerminalOutput } from "./TerminalOutput";

interface Props {
  messages: ChatMessage[];
  onSend: (msg: ClientMessage) => void;
}

export function ChatWindow({ messages, onSend }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      {messages.length === 0 && (
        <div className="text-center text-gray-400 mt-20">
          <p className="text-lg">Paste a GitHub repo URL above to get started</p>
        </div>
      )}

      {messages.map((msg, i) => {
        switch (msg.kind) {
          case "agent":
            return <MessageBubble key={i} role="agent" text={msg.text} />;
          case "user":
            return <MessageBubble key={i} role="user" text={msg.text} />;
          case "approval":
            return (
              <ApprovalCard
                key={i}
                command={msg.command}
                description={msg.description}
                resolved={msg.resolved}
                onApprove={() => onSend({ type: "approval", request_id: msg.request_id, approved: true })}
                onDeny={() => onSend({ type: "approval", request_id: msg.request_id, approved: false })}
              />
            );
          case "input":
            return (
              <UserInputWidget
                key={i}
                question={msg.question}
                options={msg.options}
                inputType={msg.input_type}
                resolved={msg.resolved}
                onSubmit={(value) => onSend({ type: "user_input", request_id: msg.request_id, value })}
              />
            );
          case "output":
            return <TerminalOutput key={i} stream={msg.stream} text={msg.text} />;
        }
      })}

      <div ref={bottomRef} />
    </div>
  );
}
