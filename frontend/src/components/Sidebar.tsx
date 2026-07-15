import { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import {
  Plus, Search, FileText, MessageSquare,
  Trash2, Edit2, Check, X,
  Settings, LogOut, ChevronLeft, ChevronRight,
} from 'lucide-react';
import { useStore } from '../store';
import { themes } from '../theme';
import * as api from '../api';

/* ── helpers ─────────────────────────────────────────── */

function daysBetween(a: Date, b: Date) {
  const msPerDay = 86_400_000;
  const startOfA = new Date(a.getFullYear(), a.getMonth(), a.getDate()).getTime();
  const startOfB = new Date(b.getFullYear(), b.getMonth(), b.getDate()).getTime();
  return Math.floor((startOfA - startOfB) / msPerDay);
}

type DateGroup = 'Today' | 'Yesterday' | 'Older';

function groupLabel(dateStr: string): DateGroup {
  const diff = daysBetween(new Date(), new Date(dateStr));
  if (diff === 0) return 'Today';
  if (diff === 1) return 'Yesterday';
  return 'Older';
}

/* ── component ───────────────────────────────────────── */

export default function Sidebar({ onNavigate }: { onNavigate?: (p: string) => void }) {
  const t = themes[useStore((s) => s.theme)];
  const {
    user, sessions, currentSessionId,
    setSessions, setCurrentSession, setMessages,
    sidebarCollapsed, setSidebarCollapsed,
    setSettingsOpen, logout, addToast,
  } = useStore();

  const [search, setSearch] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  /* ── fetch sessions on mount / user change ── */
  const refreshSessions = useCallback(async () => {
    if (!user) return;
    try {
      const list = await api.getSessions(user.username);
      setSessions(list);
    } catch {
      /* silent */
    }
  }, [user, setSessions]);

  useEffect(() => { refreshSessions(); }, [refreshSessions]);

  /* ── actions ── */
  const handleNewChat = async () => {
    if (!user) return;
    try {
      const { id } = await api.createSession(user.username);
      await refreshSessions();
      setCurrentSession(id);
      setMessages([]);
    } catch {
      addToast('Failed to create session', 'error');
    }
  };

  const handleSelect = async (id: string) => {
    setCurrentSession(id);
    try {
      const msgs = await api.getMessages(id);
      setMessages(msgs);
    } catch {
      addToast('Failed to load messages', 'error');
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteSession(id);
      await refreshSessions();
      if (currentSessionId === id) {
        setCurrentSession(null);
        setMessages([]);
      }
      addToast('Session deleted', 'success');
    } catch {
      addToast('Failed to delete session', 'error');
    }
  };

  const handleRenameStart = (id: string, currentTitle: string) => {
    setEditingId(id);
    setEditTitle(currentTitle);
  };

  const handleRenameConfirm = async () => {
    if (!editingId) return;
    try {
      await api.renameSession(editingId, editTitle);
      await refreshSessions();
      addToast('Session renamed', 'success');
    } catch {
      addToast('Failed to rename session', 'error');
    }
    setEditingId(null);
  };

  const handleRenameCancel = () => { setEditingId(null); };

  /* ── filter & group ── */
  const filtered = sessions.filter((s) =>
    s.title.toLowerCase().includes(search.toLowerCase()),
  );

  const groups: Record<DateGroup, typeof filtered> = { Today: [], Yesterday: [], Older: [] };
  for (const s of filtered) {
    groups[groupLabel(s.updated_at)].push(s);
  }

  const expanded = !sidebarCollapsed;
  const width = expanded ? 260 : 64;

  return (
    <motion.aside
      animate={{ width }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      style={{
        position: 'relative',
        width,
        flexShrink: 0,
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        background: t.surface,
        borderRight: `1px solid ${t.border}`,
        zIndex: 40,
        overflow: 'hidden',
      }}
    >
      {/* ── toggle button ── */}
      <button
        onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
        style={{
          position: 'absolute',
          top: 12,
          right: 8,
          width: 28,
          height: 28,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: 8,
          background: 'transparent',
          border: 'none',
          color: t.textMuted,
          cursor: 'pointer',
          zIndex: 2,
        }}
      >
        {expanded ? <ChevronLeft size={16} /> : <ChevronRight size={16} />}
      </button>

      {/* ── logo area ── */}
      <div
        onClick={() => onNavigate?.('landing')}
        style={{
          padding: '16px 14px 8px',
          display: 'flex',
          alignItems: 'center',
          gap: 10,
          cursor: onNavigate ? 'pointer' : 'default',
        }}
      >
        <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
          <path d="M16 4 L8 18 L16 28" stroke={t.accentSignal} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <path d="M16 4 L24 18 L16 28" stroke={t.accentAgent} strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" fill="none" />
          <path d="M10 10 L22 10 L16 28" stroke={t.textMuted} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" opacity="0.5" />
        </svg>
        {expanded && (
          <span
            style={{
              fontFamily: 'var(--font-heading, "Inter", sans-serif)',
              fontSize: 20,
              fontWeight: 700,
              color: t.textPrimary,
              letterSpacing: '-0.02em',
              whiteSpace: 'nowrap',
            }}
          >
            Distill
          </span>
        )}
      </div>

      {/* ── new chat button ── */}
      <div style={{ padding: '4px 10px 8px' }}>
        <button
          onClick={handleNewChat}
          style={{
            width: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: expanded ? 'flex-start' : 'center',
            gap: 8,
            padding: expanded ? '10px 14px' : '10px 0',
            borderRadius: 12,
            border: 'none',
            background: `linear-gradient(135deg, ${t.accentSignal}, ${t.accentAgent})`,
            color: '#fff',
            fontWeight: 600,
            fontSize: 13,
            cursor: 'pointer',
            whiteSpace: 'nowrap',
          }}
        >
          <Plus size={16} />
          {expanded && 'New Chat'}
        </button>
      </div>

      {/* ── search ── */}
      {expanded && (
        <div style={{ padding: '0 10px 8px' }}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 8,
              padding: '8px 12px',
              borderRadius: 12,
              background: t.elevated,
            }}
          >
            <Search size={14} style={{ color: t.textMuted, flexShrink: 0 }} />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search…"
              style={{
                background: 'transparent',
                border: 'none',
                outline: 'none',
                color: t.textPrimary,
                fontSize: 13,
                width: '100%',
              }}
            />
          </div>
        </div>
      )}

      {/* ── session list ── */}
      <div
        style={{
          flex: 1,
          overflowY: 'auto',
          overflowX: 'hidden',
          paddingLeft: 8,
          paddingRight: 8,
        }}
      >
        {(Object.keys(groups) as DateGroup[]).map((label) => {
          const items = groups[label];
          if (items.length === 0) return null;
          return (
            <div key={label}>
              {expanded && (
                <div
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    color: t.textMuted,
                    marginTop: 16,
                    marginBottom: 4,
                    paddingLeft: 8,
                    paddingRight: 8,
                    letterSpacing: '0.06em',
                  }}
                >
                  {label}
                </div>
              )}

              {items.map((s) => {
                const active = s.id === currentSessionId;
                const isEditing = editingId === s.id;
                const isHovered = hoveredId === s.id;
                const Icon = s.document_name ? FileText : MessageSquare;

                return (
                  <div
                    key={s.id}
                    onMouseEnter={() => setHoveredId(s.id)}
                    onMouseLeave={() => setHoveredId(null)}
                    onClick={() => { if (!isEditing) handleSelect(s.id); }}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 8,
                      padding: '8px 10px',
                      borderRadius: 12,
                      cursor: 'pointer',
                      background: active
                        ? `${t.accentSignal}1A`
                        : isHovered
                          ? t.elevated
                          : 'transparent',
                      borderLeft: active ? `3px solid ${t.accentSignal}` : '3px solid transparent',
                      transition: 'background 0.15s',
                      marginBottom: 2,
                      position: 'relative',
                    }}
                  >
                    <Icon size={16} style={{ color: active ? t.accentSignal : t.textMuted, flexShrink: 0 }} />

                    {expanded && !isEditing && (
                      <span
                        style={{
                          flex: 1,
                          fontSize: 13,
                          color: t.textPrimary,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                        }}
                      >
                        {s.title}
                      </span>
                    )}

                    {expanded && isEditing && (
                      <>
                        <input
                          autoFocus
                          value={editTitle}
                          onClick={(e) => e.stopPropagation()}
                          onChange={(e) => setEditTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleRenameConfirm();
                            if (e.key === 'Escape') handleRenameCancel();
                          }}
                          style={{
                            flex: 1,
                            fontSize: 13,
                            color: t.textPrimary,
                            background: t.elevated,
                            border: `1px solid ${t.border}`,
                            borderRadius: 6,
                            padding: '2px 6px',
                            outline: 'none',
                          }}
                        />
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRenameConfirm(); }}
                          style={{ background: 'none', border: 'none', color: t.success, cursor: 'pointer', padding: 2, display: 'flex' }}
                        >
                          <Check size={14} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRenameCancel(); }}
                          style={{ background: 'none', border: 'none', color: t.error, cursor: 'pointer', padding: 2, display: 'flex' }}
                        >
                          <X size={14} />
                        </button>
                      </>
                    )}

                    {/* message count badge */}
                    {expanded && !isEditing && s.message_count > 0 && (
                      <span
                        style={{
                          fontSize: 10,
                          fontWeight: 600,
                          color: t.textMuted,
                          background: t.elevated,
                          borderRadius: 8,
                          padding: '1px 6px',
                          flexShrink: 0,
                        }}
                      >
                        {s.message_count}
                      </span>
                    )}

                    {/* hover actions */}
                    {expanded && isHovered && !isEditing && (
                      <div style={{ display: 'flex', gap: 2, flexShrink: 0 }}>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleRenameStart(s.id, s.title); }}
                          style={{
                            width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'none', border: 'none', color: t.textMuted, cursor: 'pointer', borderRadius: 6,
                          }}
                        >
                          <Edit2 size={13} />
                        </button>
                        <button
                          onClick={(e) => { e.stopPropagation(); handleDelete(s.id); }}
                          style={{
                            width: 24, height: 24, display: 'flex', alignItems: 'center', justifyContent: 'center',
                            background: 'none', border: 'none', color: t.error, cursor: 'pointer', borderRadius: 6,
                          }}
                        >
                          <Trash2 size={13} />
                        </button>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          );
        })}
      </div>

      {/* ── bottom user area ── */}
      <div
        style={{
          borderTop: `1px solid ${t.border}`,
          padding: 12,
          display: 'flex',
          flexDirection: 'column',
          gap: 8,
        }}
      >
        {/* user info */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: '50%',
              background: `linear-gradient(135deg, ${t.accentSignal}, ${t.accentAgent})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#fff',
              fontWeight: 700,
              fontSize: 14,
              flexShrink: 0,
            }}
          >
            {user ? user.display_name.charAt(0).toUpperCase() : '?'}
          </div>

          {expanded && (
            <div style={{ overflow: 'hidden', flex: 1 }}>
              <div
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  color: t.textPrimary,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {user ? user.display_name : 'Guest'}
              </div>
              <div
                style={{
                  fontSize: 11,
                  color: t.textMuted,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                @{user ? user.username : '—'}
              </div>
            </div>
          )}
        </div>

        {/* action buttons */}
        <div style={{ display: 'flex', gap: 4 }}>
          <button
            onClick={() => setSettingsOpen(true)}
            title="Settings"
            style={{
              flex: expanded ? 1 : undefined,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '8px 0',
              borderRadius: 10,
              border: 'none',
              background: t.elevated,
              color: t.textMuted,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
            }}
          >
            <Settings size={15} />
            {expanded && 'Settings'}
          </button>

          <button
            onClick={logout}
            title="Logout"
            style={{
              flex: expanded ? 1 : undefined,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: 6,
              padding: '8px 0',
              borderRadius: 10,
              border: 'none',
              background: t.elevated,
              color: t.error,
              cursor: 'pointer',
              fontSize: 12,
              fontWeight: 500,
            }}
          >
            <LogOut size={15} />
            {expanded && 'Logout'}
          </button>
        </div>
      </div>
    </motion.aside>
  );
}
