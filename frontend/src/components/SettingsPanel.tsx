import { motion, AnimatePresence } from 'framer-motion';
import { X, Moon, Sun } from 'lucide-react';
import { useStore } from '../store';
import { themes } from '../theme';

export default function SettingsPanel() {
  const t = themes[useStore((s) => s.theme)];
  const { theme, user, settingsOpen, setSettingsOpen, toggleTheme } = useStore();

  const isDark = theme === 'dark';

  return (
    <AnimatePresence>
      {settingsOpen && (
        /* ── backdrop ── */
        <motion.div
          key="settings-backdrop"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={() => setSettingsOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(0,0,0,0.5)',
            zIndex: 50,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
          }}
        >
          {/* ── panel ── */}
          <motion.div
            key="settings-panel"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            transition={{ duration: 0.2 }}
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: 448,
              width: '100%',
              borderRadius: 16,
              background: t.surface,
              border: `1px solid ${t.border}`,
              padding: 24,
              position: 'relative',
            }}
          >
            {/* ── header ── */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
              <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: t.textPrimary }}>Settings</h2>
              <button
                onClick={() => setSettingsOpen(false)}
                style={{
                  width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center',
                  borderRadius: 8, border: 'none', background: t.elevated, color: t.textMuted, cursor: 'pointer',
                }}
              >
                <X size={16} />
              </button>
            </div>

            {/* ── appearance ── */}
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: 16,
                marginBottom: 16,
                borderBottom: `1px solid ${t.border}`,
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {isDark ? <Moon size={18} style={{ color: t.accentAgent }} /> : <Sun size={18} style={{ color: t.warning }} />}
                <span style={{ fontSize: 14, fontWeight: 500, color: t.textPrimary }}>
                  {isDark ? 'Dark Mode' : 'Light Mode'}
                </span>
              </div>

              {/* toggle switch */}
              <button
                onClick={toggleTheme}
                style={{
                  width: 44,
                  height: 24,
                  borderRadius: 12,
                  border: 'none',
                  background: isDark ? t.accentAgent : t.accentSignal,
                  position: 'relative',
                  cursor: 'pointer',
                  transition: 'background 0.2s',
                  padding: 0,
                }}
              >
                <motion.div
                  animate={{ x: isDark ? 22 : 2 }}
                  transition={{ type: 'spring', stiffness: 400, damping: 25 }}
                  style={{
                    width: 20,
                    height: 20,
                    borderRadius: '50%',
                    background: '#fff',
                    position: 'absolute',
                    top: 2,
                    left: 0,
                  }}
                />
              </button>
            </div>

            {/* ── account ── */}
            <div
              style={{
                paddingBottom: 16,
                marginBottom: 16,
                borderBottom: `1px solid ${t.border}`,
              }}
            >
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: t.textMuted, marginBottom: 12, letterSpacing: '0.06em' }}>
                Account
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div
                  style={{
                    width: 40,
                    height: 40,
                    borderRadius: '50%',
                    background: `linear-gradient(135deg, ${t.accentSignal}, ${t.accentAgent})`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#fff',
                    fontWeight: 700,
                    fontSize: 16,
                    flexShrink: 0,
                  }}
                >
                  {user ? user.display_name.charAt(0).toUpperCase() : '?'}
                </div>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: t.textPrimary }}>
                    {user ? user.display_name : 'Guest'}
                  </div>
                  <div style={{ fontSize: 12, color: t.textMuted }}>
                    @{user ? user.username : '—'}
                  </div>
                </div>
              </div>
            </div>

            {/* ── about ── */}
            <div>
              <div style={{ fontSize: 11, fontWeight: 700, textTransform: 'uppercase', color: t.textMuted, marginBottom: 8, letterSpacing: '0.06em' }}>
                About
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: t.textPrimary, marginBottom: 4 }}>
                Distill v1.0
              </div>
              <div style={{ fontSize: 13, color: t.textMuted, lineHeight: 1.5 }}>
                An autonomous data analyst agent that helps you explore, query, and visualise your datasets through natural conversation.
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
