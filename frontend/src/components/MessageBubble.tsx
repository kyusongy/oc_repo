import ReactMarkdown from "react-markdown";

interface Props {
  role: "agent" | "user";
  text: string;
}

export function MessageBubble({ role, text }: Props) {
  if (role === "user") {
    return (
      <div className="flex justify-end mb-4">
        <div className="max-w-[70%] px-5 py-3 bg-primary text-on-primary rounded-2xl rounded-br-sm">
          <p className="text-sm whitespace-pre-wrap">{text}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 max-w-2xl">
      <div className="bg-surface-lowest rounded-lg p-8 shadow-[0_12px_32px_-4px_rgba(45,52,51,0.06)] border-l-4 border-tertiary relative overflow-hidden">
        <div className="flex items-start gap-4">
          <div className="w-10 h-10 rounded-full bg-primary-container flex items-center justify-center text-primary shrink-0">
            <span className="material-symbols-outlined">smart_toy</span>
          </div>
          <div className="space-y-2 min-w-0">
            <span className="font-headline font-bold text-on-surface text-sm">System Agent</span>
            <div className="prose prose-sm max-w-none text-on-surface leading-relaxed [&_p]:my-1 [&_ul]:my-1 [&_li]:my-0 [&_code]:bg-surface-low [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded [&_code]:text-primary-dim [&_code]:font-mono [&_code]:text-xs">
              <ReactMarkdown>{text}</ReactMarkdown>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
