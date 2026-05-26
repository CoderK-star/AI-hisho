export interface Task {
  id: string;
  title: string;
  description: string;
  status: "pending" | "done";
  priority: "low" | "medium" | "high";
  due_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface Reminder {
  id: string;
  message: string;
  remind_at: string;
  is_recurring: boolean;
  recurrence_rule: string | null;
  fired: boolean;
  created_at: string;
}

export interface Memo {
  id: string;
  title: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface LogEntry {
  timestamp: string;
  session_id?: string;
  intent: string;
  input_summary: string;
  llm_route: string;
  cloud_escalated?: boolean;
  tools_called: string[];
  external_apis_called?: string[];
  result: string;
  requires_confirmation?: boolean;
}

export interface ConfirmPayload {
  title: string;
  description?: string;
  details?: Array<{ label: string; value: string; mono?: boolean }>;
  warning?: string;
  actionLabel?: string;
  destructive?: boolean;
  onConfirm: () => void;
}

export interface ConfirmHandle {
  open: (payload: ConfirmPayload) => void;
  close: () => void;
  props: {
    state: { open: boolean; payload: ConfirmPayload | null };
    close: () => void;
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  time: string;
  text: string;
  toolsCalled?: string[];
  confirmCard?: {
    kind: "task-added" | "reminder-added" | "memo-created";
    title: string;
    meta: string;
  };
}
