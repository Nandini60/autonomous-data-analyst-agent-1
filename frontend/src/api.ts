const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
  username: string;
  display_name: string;
  avatar_color: string;
  created_at: string;
}

export interface Session {
  id: string;
  username: string;
  title: string;
  document_name: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface Message {
  role: 'user' | 'assistant';
  content: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface ChatResponse {
  answer: string;
  tools_used: string[];
  confidence: number;
  sql: string | null;
  sources: string[];
  figures_json: any[];
  execution_time: number;
  warnings: string[];
}

export interface UploadResponse {
  success: boolean;
  file_type: string;
  message: string;
  session_id?: string;
  table_name?: string;
  row_count?: number;
  columns?: string[];
  chunks_added?: number;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || 'Request failed');
  }
  return res.json();
}

export async function login(username: string, password: string) {
  return request<{ success: boolean; message: string; user?: User }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ username, password }),
  });
}

export async function register(username: string, password: string, displayName: string) {
  return request<{ success: boolean; message: string }>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ username, password, display_name: displayName }),
  });
}

export async function getSessions(username: string) {
  return request<Session[]>(`/api/sessions?username=${encodeURIComponent(username)}`);
}

export async function createSession(username: string, title = 'New Chat', documentName = '') {
  return request<{ id: string }>('/api/sessions', {
    method: 'POST',
    body: JSON.stringify({ username, title, document_name: documentName }),
  });
}

export async function deleteSession(id: string) {
  return request<{ ok: boolean }>(`/api/sessions/${id}`, { method: 'DELETE' });
}

export async function renameSession(id: string, title: string) {
  return request<{ ok: boolean }>(`/api/sessions/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  });
}

export async function getMessages(sessionId: string) {
  return request<Message[]>(`/api/sessions/${sessionId}/messages`);
}

export async function sendChat(username: string, sessionId: string, question: string) {
  return request<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ username, session_id: sessionId, question }),
  });
}

export async function uploadFile(file: File, username: string): Promise<UploadResponse> {
  const form = new FormData();
  form.append('file', file);
  form.append('username', username);
  const res = await fetch(`${BASE}/api/upload`, { method: 'POST', body: form });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

export async function getSchema() {
  return request<{ schema: string; tables: string[] }>('/api/schema');
}

export async function checkHealth() {
  return request<{ status: string; agent_ready: boolean }>('/api/health');
}
