// Messages FROM backend
export type ServerMessage =
  | { type: "agent_message"; text: string }
  | { type: "approval_request"; request_id: string; command: string; description: string }
  | { type: "user_input_request"; request_id: string; question: string; options?: { label: string; description: string }[]; input_type: "text" | "password" | "choice" }
  | { type: "command_output"; stream: "stdout" | "stderr"; text: string }
  | { type: "status_update"; phase: string; message: string; progress?: number }
  | { type: "done"; success: boolean; message: string }
  | { type: "project_saved"; project: ProjectInfo }
  | { type: "auto_approved"; command: string; description: string }
  | { type: "tool_start"; tool_name: string; description: string };

// Messages TO backend
export type ClientMessage =
  | { type: "start"; url: string; path?: string; auto_mode?: boolean }
  | { type: "message"; text: string }
  | { type: "approval"; request_id: string; approved: boolean }
  | { type: "user_input"; request_id: string; value: string };

// UI state for chat messages
export type ChatMessage =
  | { kind: "agent"; text: string }
  | { kind: "user"; text: string }
  | { kind: "approval"; request_id: string; command: string; description: string; resolved?: boolean }
  | { kind: "input"; request_id: string; question: string; options?: { label: string; description: string }[]; input_type: "text" | "password" | "choice"; resolved?: boolean }
  | { kind: "output"; stream: "stdout" | "stderr"; text: string }
  | { kind: "auto_approved"; command: string; description: string }
  | { kind: "tool_start"; tool_name: string; description: string };

export interface ProjectInfo {
  name: string;
  url: string;
  path: string;
  ports: number[];
  installed_at: string;
  status: "running" | "stopped";
  launch_url?: string;
}

export type Phase = "idle" | "scanning" | "installing" | "launching" | "done" | "error";
