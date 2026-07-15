import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, FileText, ArrowRight, HelpCircle, Database } from 'lucide-react';
import { useStore } from '../store';
import { themes } from '../theme';
import Sidebar from '../components/Sidebar';
import ChatMessage from '../components/ChatMessage';
import ChatInput from '../components/ChatInput';
import FileUpload from '../components/FileUpload';
import TypingIndicator from '../components/TypingIndicator';
import AgentAvatar from '../components/AgentAvatar';
import SettingsPanel from '../components/SettingsPanel';
import Toast from '../components/Toast';
import * as api from '../api';

export default function ChatPage({ onNavigate }: { onNavigate?: (p: string) => void }) {
  const theme = useStore((s) => s.theme);
  const t = themes[theme];
  const isDark = theme === 'dark';

  const {
    user,
    sessions,
    currentSessionId,
    messages,
    isLoading,
    setSessions,
    setCurrentSession,
    setMessages,
    addMessage,
    setLoading,
    addToast,
  } = useStore();

  const [isUploading, setIsUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [inspectorOpen, setInspectorOpen] = useState(false);
  const [schemaData, setSchemaData] = useState<{ schema: string; tables: string[] } | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  /* ── auto-scroll to bottom ──────────────────────────── */
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  /* ── load sessions on mount ─────────────────────────── */
  const refreshSessions = useCallback(async () => {
    if (!user) return;
    try {
      const s = await api.getSessions(user.username);
      setSessions(s);
    } catch { /* ignore */ }
  }, [user, setSessions]);

  useEffect(() => {
    refreshSessions();
  }, [refreshSessions]);

  /* ── handlers ───────────────────────────────────────── */
  const handleSend = useCallback(
    async (text: string) => {
      if (!user || !currentSessionId) return;
      addMessage({ role: 'user', content: text, metadata: {}, timestamp: new Date().toISOString() });
      setLoading(true);
      try {
        const res = await api.sendChat(user.username, currentSessionId, text);
        addMessage({
          role: 'assistant',
          content: res.answer,
          metadata: {
            tools_used: res.tools_used,
            confidence: res.confidence,
            sql: res.sql,
            sources: res.sources,
            figures_json: res.figures_json,
            execution_time: res.execution_time,
            warnings: res.warnings,
          },
          timestamp: new Date().toISOString(),
        });
        refreshSessions();
      } catch (err: unknown) {
        addToast(err instanceof Error ? err.message : 'Failed to send message', 'error');
      } finally {
        setLoading(false);
      }
    },
    [user, currentSessionId, addMessage, setLoading, refreshSessions, addToast],
  );

  const handleUpload = useCallback(
    async (file: File) => {
      if (!user) return;
      setIsUploading(true);
      setUploadProgress(0);
      const interval = setInterval(() => {
        setUploadProgress((p) => Math.min(p + Math.random() * 18, 92));
      }, 400);
      try {
        const res = await api.uploadFile(file, user.username);
        clearInterval(interval);
        setUploadProgress(100);
        if (res.session_id) {
          setCurrentSession(res.session_id);
          const msgs = await api.getMessages(res.session_id);
          setMessages(msgs);
        }
        addToast(res.message || 'File uploaded successfully!', 'success');
        refreshSessions();
      } catch (err: unknown) {
        clearInterval(interval);
        addToast(err instanceof Error ? err.message : 'Upload failed', 'error');
      } finally {
        setIsUploading(false);
        setUploadProgress(0);
      }
    },
    [user, setCurrentSession, setMessages, refreshSessions, addToast],
  );

  const handleRegenerate = useCallback(async () => {
    if (!user || !currentSessionId || messages.length < 2) return;
    const lastUserMsg = [...messages].reverse().find((m) => m.role === 'user');
    if (!lastUserMsg) return;
    setLoading(true);
    try {
      const res = await api.sendChat(user.username, currentSessionId, lastUserMsg.content);
      addMessage({
        role: 'assistant',
        content: res.answer,
        metadata: {
          tools_used: res.tools_used,
          confidence: res.confidence,
          sql: res.sql,
          sources: res.sources,
          figures_json: res.figures_json,
          execution_time: res.execution_time,
          warnings: res.warnings,
        },
        timestamp: new Date().toISOString(),
      });
    } catch (err: unknown) {
      addToast(err instanceof Error ? err.message : 'Regeneration failed', 'error');
    } finally {
      setLoading(false);
    }
  }, [user, currentSessionId, messages, addMessage, setLoading, addToast]);

  const handleDelete = useCallback(
    (idx: number) => {
      setMessages(messages.filter((_, i) => i !== idx));
    },
    [messages, setMessages],
  );

  /* ── current session info ───────────────────────────── */
  const activeSession = sessions.find((s) => s.id === currentSessionId);

  /* ── fetch schema details for spreadsheet sessions ──── */
  useEffect(() => {
    if (activeSession?.document_name && (
      activeSession.document_name.toLowerCase().endsWith('.csv') ||
      activeSession.document_name.toLowerCase().endsWith('.xlsx') ||
      activeSession.document_name.toLowerCase().endsWith('.xls')
    )) {
      api.getSchema().then((data) => {
        setSchemaData(data);
      }).catch(() => setSchemaData(null));
    } else {
      setSchemaData(null);
    }
  }, [activeSession]);

  /* ── parse schema string ────────────────────────────── */
  const parsedSchema = useMemo(() => {
    if (!schemaData?.schema) return [];
    const sections = schemaData.schema.split('TABLE: ').filter(Boolean);
    return sections.map((sec) => {
      const lines = sec.split('\n').filter(Boolean);
      const header = lines[0];
      const tableName = header.split(' (')[0];
      const rowInfo = header.includes('(') ? header.slice(header.indexOf('(')) : '';
      const columns = lines.slice(1).map((line) => {
        const cleaned = line.trim();
        const parts = cleaned.split(' — e.g. ');
        const nameAndType = parts[0];
        const sample = parts[1] || '';
        const name = nameAndType.split(' (')[0];
        const type = nameAndType.includes('(') ? nameAndType.slice(nameAndType.indexOf('(')).replace(/[()]/g, '') : '';
        return { name, type, sample };
      });
      return { tableName, rowInfo, columns };
    });
  }, [schemaData]);

  /* ── sample queries for empty state ─────────────────── */
  const sampleQueries = [
    'What are the top 5 products by revenue?',
    'Summarise Q3 performance vs Q2.',
    'Show me a chart of monthly sales trends.',
  ];

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: t.bg }}>
      <Sidebar onNavigate={onNavigate} />

      {/* Main content area */}
      <div className="flex-1 flex flex-col min-w-0">
        {!currentSessionId ? (
          /* ──────────── Dashboard (no session selected) ──────────── */
          <div className="flex-1 overflow-y-auto" style={{ background: isDark ? '#0a0a0f' : t.bg }}>
            <motion.div
              initial="hidden"
              animate="visible"
              variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.08 } } }}
              className="mx-auto w-full"
              style={{ maxWidth: 960, padding: '48px 32px' }}
            >
              {/* Greeting header */}
              <motion.div
                variants={{ hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } } }}
                style={{ marginBottom: 40 }}
              >
                <h1
                  style={{
                    fontSize: 28,
                    fontWeight: 500,
                    color: isDark ? '#f5f5f7' : t.textPrimary,
                    margin: '0 0 8px',
                    letterSpacing: '-0.02em',
                  }}
                >
                  Welcome back, {user?.display_name || user?.username || 'User'}
                </h1>
                <p style={{ fontSize: 15, color: isDark ? '#9a9aa8' : t.textMuted, margin: 0 }}>
                  Upload a document or resume a previous conversation.
                </p>
              </motion.div>

              {/* Grid: Upload + Quick Stats */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-5" style={{ marginBottom: 40 }}>
                {/* Upload card */}
                <motion.div
                  variants={{ hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } } }}
                  className="lg:col-span-7"
                  style={{
                    background: isDark ? '#12121a' : t.surface,
                    border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : t.border}`,
                    borderRadius: 12,
                    padding: '28px 24px',
                  }}
                >
                  <h2
                    style={{
                      fontSize: 15,
                      fontWeight: 500,
                      color: isDark ? '#f5f5f7' : t.textPrimary,
                      margin: '0 0 20px',
                    }}
                  >
                    Upload a document
                  </h2>
                  <FileUpload
                    onUpload={handleUpload}
                    isUploading={isUploading}
                    progress={uploadProgress}
                    variant="full"
                  />
                </motion.div>

                {/* Stats card */}
                <motion.div
                  variants={{ hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } } }}
                  className="lg:col-span-5 flex flex-col gap-5"
                  style={{
                    background: isDark ? '#12121a' : t.surface,
                    border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : t.border}`,
                    borderRadius: 12,
                    padding: '28px 24px',
                  }}
                >
                  <h2
                    style={{
                      fontSize: 15,
                      fontWeight: 500,
                      color: isDark ? '#f5f5f7' : t.textPrimary,
                      margin: 0,
                    }}
                  >
                    Workspace
                  </h2>

                  <div className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center"
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 10,
                        background: isDark ? 'rgba(124,111,232,0.12)' : `${t.accentAgent}18`,
                        border: `1px solid ${isDark ? 'rgba(124,111,232,0.2)' : 'transparent'}`,
                      }}
                    >
                      <FileText size={18} style={{ color: isDark ? '#7c6fe8' : t.accentAgent }} />
                    </div>
                    <div>
                      <div style={{ fontSize: 20, fontWeight: 500, color: isDark ? '#f5f5f7' : t.textPrimary, letterSpacing: '-0.02em' }}>
                        {sessions.length}
                      </div>
                      <div style={{ fontSize: 12, color: isDark ? '#6b6b78' : t.textMuted, fontWeight: 400 }}>
                        Active sessions
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div
                      className="flex items-center justify-center"
                      style={{
                        width: 40,
                        height: 40,
                        borderRadius: 10,
                        background: isDark ? 'rgba(45,212,191,0.12)' : `${t.accentSignal}18`,
                        border: `1px solid ${isDark ? 'rgba(45,212,191,0.2)' : 'transparent'}`,
                      }}
                    >
                      <Sparkles size={18} style={{ color: isDark ? '#2dd4bf' : t.accentSignal }} />
                    </div>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 500, color: isDark ? '#f5f5f7' : t.textPrimary }}>
                        SQL · RAG · Charts · Voice
                      </div>
                      <div style={{ fontSize: 12, color: isDark ? '#6b6b78' : t.textMuted, fontWeight: 400 }}>
                        Available capabilities
                      </div>
                    </div>
                  </div>

                  <div
                    className="flex items-start gap-2.5 mt-auto"
                    style={{
                      padding: '12px 14px',
                      borderRadius: 8,
                      background: isDark ? 'rgba(45,212,191,0.06)' : `${t.accentSignal}08`,
                      border: `1px solid ${isDark ? 'rgba(45,212,191,0.1)' : 'transparent'}`,
                    }}
                  >
                    <HelpCircle size={14} className="shrink-0 mt-0.5" style={{ color: isDark ? '#2dd4bf' : t.accentSignal }} />
                    <p style={{ fontSize: 12, color: isDark ? '#9a9aa8' : t.textMuted, margin: 0, lineHeight: 1.5 }}>
                      Upload a CSV, PDF, or spreadsheet. Distill parses and indexes it so you can chat with your data.
                    </p>
                  </div>
                </motion.div>
              </div>

              {/* Recent chats */}
              {sessions.length > 0 && (
                <motion.div
                  variants={{ hidden: { opacity: 0, y: 40 }, visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } } }}
                >
                  <h2
                    style={{
                      fontSize: 15,
                      fontWeight: 500,
                      color: isDark ? '#f5f5f7' : t.textPrimary,
                      margin: '0 0 16px',
                    }}
                  >
                    Recent conversations
                  </h2>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {sessions.slice(0, 3).map((s) => (
                      <motion.div
                        key={s.id}
                        whileHover={{
                          y: -4,
                          borderColor: isDark ? 'rgba(255,255,255,0.12)' : t.border,
                          boxShadow: isDark ? '0 12px 32px rgba(0,0,0,0.4)' : `0 6px 20px ${t.accentAgent}08`,
                        }}
                        onClick={() => {
                          setCurrentSession(s.id);
                          api.getMessages(s.id).then(setMessages).catch(() => setMessages([]));
                        }}
                        className="cursor-pointer transition-all duration-200"
                        style={{
                          background: isDark ? '#12121a' : t.surface,
                          border: `1px solid ${isDark ? 'rgba(255,255,255,0.08)' : t.border}`,
                          borderRadius: 12,
                          padding: '20px',
                        }}
                      >
                        <div className="flex items-center gap-2" style={{ marginBottom: 10 }}>
                          <FileText size={14} style={{ color: isDark ? '#2dd4bf' : t.accentSignal }} />
                          <span
                            className="truncate"
                            style={{ fontSize: 14, fontWeight: 500, color: isDark ? '#f5f5f7' : t.textPrimary }}
                          >
                            {s.title || 'New Chat'}
                          </span>
                        </div>
                        {s.document_name && (
                          <p className="truncate" style={{ fontSize: 12, color: isDark ? '#6b6b78' : t.textMuted, margin: '0 0 8px' }}>
                            {s.document_name}
                          </p>
                        )}
                        <div className="flex items-center justify-between" style={{ marginTop: 12 }}>
                          <span style={{ fontSize: 12, color: isDark ? '#6b6b78' : t.textMuted, fontWeight: 400 }}>
                            {s.message_count} messages
                          </span>
                          <span
                            className="flex items-center gap-1"
                            style={{ fontSize: 12, fontWeight: 500, color: isDark ? '#2dd4bf' : t.accentSignal }}
                          >
                            Resume <ArrowRight size={12} />
                          </span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </motion.div>
              )}
            </motion.div>
          </div>
        ) : (
          /* ──────────── Active session ──────────── */
          <>
            {/* Header bar */}
            <div
              className="flex items-center justify-between px-6 shrink-0"
              style={{
                height: 56,
                borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : t.border}`,
                background: isDark ? '#0e0e16' : t.bg,
              }}
            >
              <div className="flex items-center gap-2.5">
                <div
                  className="flex items-center justify-center"
                  style={{
                    width: 28,
                    height: 28,
                    borderRadius: 8,
                    background: isDark ? 'rgba(45,212,191,0.1)' : `${t.accentSignal}12`,
                  }}
                >
                  <Sparkles size={14} style={{ color: isDark ? '#2dd4bf' : t.accentSignal }} />
                </div>
                <span
                  className="truncate"
                  style={{ fontSize: 14, fontWeight: 500, color: isDark ? '#f5f5f7' : t.textPrimary }}
                >
                  {activeSession?.title || 'Chat'}
                </span>
              </div>
              <div className="flex items-center gap-2.5">
                {activeSession?.document_name && (
                  <>
                    <button
                      onClick={() => setInspectorOpen(!inspectorOpen)}
                      className="flex items-center gap-1.5 cursor-pointer transition-all duration-150"
                      style={{
                        fontSize: 12,
                        fontWeight: 500,
                        padding: '6px 12px',
                        borderRadius: 8,
                        border: `1px solid ${inspectorOpen ? (isDark ? 'rgba(45,212,191,0.3)' : t.accentSignal) : (isDark ? 'rgba(255,255,255,0.08)' : t.border)}`,
                        background: inspectorOpen ? (isDark ? 'rgba(45,212,191,0.08)' : `${t.accentSignal}10`) : (isDark ? '#12121a' : t.surface),
                        color: inspectorOpen ? (isDark ? '#2dd4bf' : t.accentSignal) : (isDark ? '#9a9aa8' : t.textMuted),
                      }}
                    >
                      <Database size={12} />
                      Schema Inspector
                    </button>
                    <span
                      className="flex items-center gap-1.5 font-mono"
                      style={{
                        fontSize: 12,
                        padding: '6px 12px',
                        borderRadius: 8,
                        border: `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : t.border}`,
                        background: isDark ? '#12121a' : t.surface,
                        color: isDark ? '#2dd4bf' : t.accentSignal,
                      }}
                    >
                      📄 {activeSession.document_name}
                    </span>
                  </>
                )}
              </div>
            </div>

            <div className="flex-1 flex overflow-hidden" style={{ background: isDark ? '#0a0a0f' : t.bg }}>
              {/* Chat sub-container */}
              <div className="flex-1 flex flex-col min-w-0 relative h-full">
                {/* Scrollable messages */}
                <div ref={scrollRef} className="flex-1 overflow-y-auto w-full pb-32">
                  <div className="max-w-3xl w-full mx-auto px-6 py-6 flex flex-col gap-5">
                    {messages.length === 0 && !isLoading ? (
                      /* Empty state */
                      <div className="flex flex-col items-center justify-center py-10 gap-6">
                        <AgentAvatar size="lg" />
                        <div className="text-center flex flex-col gap-2">
                          <h2 className="text-2xl font-bold font-heading" style={{ color: t.textPrimary }}>
                            {activeSession?.document_name ? 'Document Ready' : 'Start a Conversation'}
                          </h2>
                          <p className="text-sm max-w-md mx-auto" style={{ color: t.textMuted }}>
                            {activeSession?.document_name
                              ? `Ask Distill anything about your document, or type a query below.`
                              : 'To begin, upload a file (PDF, CSV, Excel, Word, or TXT) or ask a general query.'}
                          </p>
                        </div>

                        {/* Show File Upload if no document is active */}
                        {!activeSession?.document_name ? (
                          <div className="w-full max-w-md p-6 rounded-2xl border" style={{ background: t.surface, borderColor: t.border }}>
                            <FileUpload
                              onUpload={handleUpload}
                              isUploading={isUploading}
                              progress={uploadProgress}
                              variant="full"
                            />
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 px-4 py-2 rounded-xl border font-mono text-xs animate-pulse" style={{ background: `${t.accentSignal}08`, borderColor: `${t.accentSignal}20`, color: t.accentSignal }}>
                            <span>active doc:</span>
                            <strong className="truncate max-w-[200px]">{activeSession.document_name}</strong>
                          </div>
                        )}

                        {/* Show sample queries */}
                        <div className="grid gap-3 w-full max-w-md mt-2">
                          <span className="text-[10px] font-bold uppercase tracking-wider text-center" style={{ color: t.textMuted }}>
                            Suggested Prompts
                          </span>
                          {sampleQueries.map((q) => (
                            <motion.button
                              key={q}
                              whileHover={{ scale: 1.01, borderColor: t.accentSignal, boxShadow: `0 4px 12px ${t.accentSignal}08` }}
                              whileTap={{ scale: 0.99 }}
                              onClick={() => handleSend(q)}
                              className="text-left px-5 py-3.5 rounded-xl border text-sm cursor-pointer transition-all"
                              style={{
                                background: t.surface,
                                borderColor: t.border,
                                color: t.textPrimary,
                              }}
                            >
                              {q}
                            </motion.button>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <AnimatePresence>
                        {messages.map((msg, idx) => (
                          <ChatMessage
                            key={idx}
                            message={msg}
                            index={idx}
                            onCopy={() => addToast('Copied to clipboard', 'info')}
                            onRegenerate={msg.role === 'assistant' && idx === messages.length - 1 ? handleRegenerate : undefined}
                            onDelete={() => handleDelete(idx)}
                          />
                        ))}
                      </AnimatePresence>
                    )}
                    <TypingIndicator visible={isLoading} />
                  </div>
                </div>

                {/* Chat input container */}
                <div 
                  className="absolute bottom-0 left-0 right-0 py-6 px-6 shrink-0 flex justify-center pointer-events-none z-10"
                  style={{
                    background: isDark
                      ? 'linear-gradient(to top, #0a0a0f 0%, rgba(10,10,15,0.7) 50%, rgba(10,10,15,0) 100%)'
                      : 'linear-gradient(to top, rgba(247,248,250,0.95) 0%, rgba(247,248,250,0.7) 50%, rgba(247,248,250,0) 100%)'
                  }}
                >
                  <div className="max-w-3xl w-full pointer-events-auto" style={{ filter: isDark ? 'drop-shadow(0 12px 40px rgba(0,0,0,0.45))' : 'drop-shadow(0 12px 40px rgba(0,0,0,0.06))' }}>
                    <ChatInput onSend={handleSend} onUpload={handleUpload} disabled={isLoading} />
                  </div>
                </div>
              </div>

              {/* Inspector panel */}
              <AnimatePresence>
                {inspectorOpen && activeSession?.document_name && (
                  <motion.div
                    initial={{ width: 0, opacity: 0 }}
                    animate={{ width: 340, opacity: 1 }}
                    exit={{ width: 0, opacity: 0 }}
                    className="h-full border-l flex flex-col shrink-0 overflow-y-auto theme-transition"
                    style={{ background: t.surface, borderColor: t.border }}
                  >
                    <div className="p-4 border-b flex items-center justify-between" style={{ borderColor: t.border }}>
                      <span className="text-xs font-bold uppercase tracking-wider font-heading" style={{ color: t.textPrimary }}>Document Inspector</span>
                      <button onClick={() => setInspectorOpen(false)} className="text-xs font-bold cursor-pointer hover:opacity-80" style={{ color: t.textMuted }}>Close</button>
                    </div>
                    <div className="p-5 flex flex-col gap-5">
                      {/* File Card */}
                      <div>
                        <h3 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: t.textMuted }}>Active File</h3>
                        <div className="p-3.5 rounded-xl border flex items-center gap-3" style={{ background: t.bg, borderColor: t.border }}>
                          <FileText size={20} style={{ color: t.accentSignal }} />
                          <div className="min-w-0">
                            <p className="text-xs font-bold truncate" style={{ color: t.textPrimary }}>{activeSession.document_name}</p>
                            <p className="text-[10px]" style={{ color: t.textMuted }}>Ready for analytical queries</p>
                          </div>
                        </div>
                      </div>

                      {/* Tables & Schema list */}
                      {schemaData && (
                        <div>
                          <h3 className="text-[10px] font-bold uppercase tracking-wider mb-2" style={{ color: t.textMuted }}>Database Tables & Schema</h3>
                          <div className="flex flex-col gap-3.5">
                            {parsedSchema.map((tbl) => (
                              <div key={tbl.tableName} className="p-3.5 rounded-xl border" style={{ background: t.bg, borderColor: t.border }}>
                                <div className="flex items-center justify-between mb-2">
                                  <div className="flex items-center gap-1.5">
                                    <Database size={13} style={{ color: t.accentAgent }} />
                                    <span className="text-xs font-mono font-bold truncate" style={{ color: t.textPrimary }}>{tbl.tableName}</span>
                                  </div>
                                  <span className="text-[10px] font-mono" style={{ color: t.textMuted }}>{tbl.rowInfo.replace(/[()]/g, '')}</span>
                                </div>
                                <div className="flex flex-col gap-2 pt-1.5 border-t" style={{ borderColor: `${t.border}50` }}>
                                  {tbl.columns.map((col) => (
                                    <div key={col.name} className="flex flex-col gap-0.5">
                                      <div className="flex items-center justify-between text-[11px] font-mono">
                                        <span className="font-semibold cursor-pointer hover:underline" style={{ color: t.textPrimary }} onClick={() => {
                                          navigator.clipboard.writeText(col.name);
                                          addToast(`Copied column "${col.name}"`, 'success');
                                        }} title="Click to copy column name">{col.name}</span>
                                        <span className="px-1 py-0.2 rounded text-[9px] font-bold uppercase" style={{ background: `${t.accentSignal}18`, color: t.accentSignal }}>{col.type}</span>
                                      </div>
                                      {col.sample && (
                                        <span className="text-[10px] truncate" style={{ color: t.textMuted }}>e.g. {col.sample}</span>
                                      )}
                                    </div>
                                  ))}
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </>
        )}
      </div>

      <SettingsPanel />
      <Toast />
    </div>
  );
}
