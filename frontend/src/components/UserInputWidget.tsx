import { useState } from "react";

interface Props {
  question: string;
  options?: { label: string; description: string }[];
  inputType: "text" | "password" | "choice";
  resolved?: boolean;
  onSubmit: (value: string) => void;
}

export function UserInputWidget({ question, options, inputType, resolved, onSubmit }: Props) {
  const [value, setValue] = useState("");
  const [showPassword, setShowPassword] = useState(false);

  if (resolved) {
    return (
      <div className="mb-6 max-w-2xl">
        <div className="bg-surface-low rounded-lg p-6">
          <p className="text-sm text-on-surface-variant">{question}</p>
          <p className="text-xs text-outline italic mt-1">Answered</p>
        </div>
      </div>
    );
  }

  if (inputType === "choice" && options) {
    return (
      <div className="mb-6 max-w-2xl">
        <div className="bg-surface-lowest rounded-lg p-8 shadow-[0_4px_20px_-4px_rgba(45,52,51,0.04)] space-y-4">
          <p className="text-sm font-medium text-on-surface">{question}</p>
          <div className="flex flex-col gap-2">
            {options.map((opt) => (
              <button
                key={opt.label}
                onClick={() => onSubmit(opt.label)}
                className="text-left px-4 py-3 bg-surface-low rounded-lg hover:bg-surface-high transition-colors"
              >
                <span className="text-sm font-semibold text-on-surface">{opt.label}</span>
                {opt.description && (
                  <span className="text-xs text-on-surface-variant block mt-0.5">{opt.description}</span>
                )}
              </button>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mb-6 max-w-2xl">
      <div className="bg-surface-lowest rounded-lg p-8 shadow-[0_4px_20px_-4px_rgba(45,52,51,0.04)] space-y-6">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-on-surface-variant">
            {inputType === "password" ? "key" : "help_outline"}
          </span>
          <p className="text-sm font-medium text-on-surface">{question}</p>
        </div>
        <form
          onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSubmit(value.trim()); }}
          className="space-y-4"
        >
          <div className="relative">
            <input
              type={inputType === "password" && !showPassword ? "password" : "text"}
              value={value}
              onChange={(e) => setValue(e.target.value)}
              placeholder={inputType === "password" ? "sk-••••••••••••••••••••••••" : "Type your answer..."}
              className="w-full bg-surface-low border-0 border-b border-outline-variant/15 py-4 px-0 focus:ring-0 focus:border-primary focus:bg-surface-lowest transition-all placeholder:text-outline-variant/40 font-mono text-sm"
            />
            {inputType === "password" && (
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-0 top-1/2 -translate-y-1/2 text-on-surface-variant hover:text-primary transition-colors"
              >
                <span className="material-symbols-outlined">
                  {showPassword ? "visibility_off" : "visibility"}
                </span>
              </button>
            )}
          </div>
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!value.trim()}
              className="text-primary text-sm font-semibold hover:underline decoration-2 underline-offset-4 disabled:opacity-40 disabled:no-underline"
            >
              Confirm
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
