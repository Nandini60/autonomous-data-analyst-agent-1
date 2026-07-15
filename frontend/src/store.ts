import { create } from 'zustand';
import type { Theme } from './theme';
import type { User, Session, Message } from './api';

export interface ToastMessage {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
}

interface Store {
  user: User | null;
  theme: Theme;
  sessions: Session[];
  currentSessionId: string | null;
  messages: Message[];
  isLoading: boolean;
  agentReady: boolean;
  
  // Sidebar state
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (b: boolean) => void;
  
  // Toast notifications
  toasts: ToastMessage[];
  addToast: (message: string, type?: 'success' | 'error' | 'info') => void;
  removeToast: (id: string) => void;
  
  // Settings modal
  settingsOpen: boolean;
  setSettingsOpen: (b: boolean) => void;

  setUser: (u: User | null) => void;
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
  setSessions: (s: Session[]) => void;
  setCurrentSession: (id: string | null) => void;
  setMessages: (m: Message[]) => void;
  addMessage: (m: Message) => void;
  setLoading: (b: boolean) => void;
  setAgentReady: (b: boolean) => void;
  logout: () => void;
}

const savedTheme = (typeof window !== 'undefined'
  ? (localStorage.getItem('distill-theme') as Theme)
  : null) || 'dark';

export const useStore = create<Store>((set) => ({
  user: null,
  theme: savedTheme,
  sessions: [],
  currentSessionId: null,
  messages: [],
  isLoading: false,
  agentReady: false,
  
  sidebarCollapsed: false,
  setSidebarCollapsed: (sidebarCollapsed) => set({ sidebarCollapsed }),
  
  toasts: [],
  addToast: (message, type = 'info') => set((state) => {
    const id = Math.random().toString(36).substring(2, 9);
    // Auto remove toast after 4s
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 4000);
    return { toasts: [...state.toasts, { id, message, type }] };
  }),
  removeToast: (id) => set((state) => ({ toasts: state.toasts.filter((t) => t.id !== id) })),
  
  settingsOpen: false,
  setSettingsOpen: (settingsOpen) => set({ settingsOpen }),

  setUser: (user) => set({ user }),
  setTheme: (theme) => {
    localStorage.setItem('distill-theme', theme);
    set({ theme });
  },
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === 'dark' ? 'light' : 'dark';
      localStorage.setItem('distill-theme', next);
      return { theme: next };
    }),
  setSessions: (sessions) => set({ sessions }),
  setCurrentSession: (currentSessionId) => set({ currentSessionId }),
  setMessages: (messages) => set({ messages }),
  addMessage: (m) => set((s) => ({ messages: [...s.messages, m] })),
  setLoading: (isLoading) => set({ isLoading }),
  setAgentReady: (agentReady) => set({ agentReady }),
  logout: () => {
    set({ user: null, sessions: [], currentSessionId: null, messages: [], isLoading: false });
  },
}));
