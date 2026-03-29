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

  if (resolved) {
    return (
      <div className="mb-3 mx-2 border border-gray-200 bg-gray-50 rounded-lg p-4">
        <p className="text-sm text-gray-700">{question}</p>
        <p className="text-xs text-gray-500 italic mt-1">Answered</p>
      </div>
    );
  }

  if (inputType === "choice" && options) {
    return (
      <div className="mb-3 mx-2 border border-blue-200 bg-blue-50 rounded-lg p-4">
        <p className="text-sm text-gray-700 mb-3">{question}</p>
        <div className="flex flex-col gap-2">
          {options.map((opt) => (
            <button key={opt.label} onClick={() => onSubmit(opt.label)} className="text-left px-3 py-2 bg-white border border-gray-200 rounded-md hover:bg-blue-100 hover:border-blue-300 transition-colors">
              <span className="text-sm font-medium">{opt.label}</span>
              {opt.description && <span className="text-xs text-gray-500 block">{opt.description}</span>}
            </button>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="mb-3 mx-2 border border-blue-200 bg-blue-50 rounded-lg p-4">
      <p className="text-sm text-gray-700 mb-2">{question}</p>
      <form onSubmit={(e) => { e.preventDefault(); if (value.trim()) onSubmit(value.trim()); }} className="flex gap-2">
        <input type={inputType === "password" ? "password" : "text"} value={value} onChange={(e) => setValue(e.target.value)} placeholder={inputType === "password" ? "••••••••" : "Type your answer..."} className="flex-1 px-3 py-2 rounded-md border border-gray-300 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500" />
        <button type="submit" disabled={!value.trim()} className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors">
          Submit
        </button>
      </form>
    </div>
  );
}
