import { motion, AnimatePresence } from 'framer-motion';
import { X, CheckCircle, AlertCircle, Info } from 'lucide-react';
import { themes } from '../theme';
import { useStore } from '../store';

const iconMap = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
} as const;

const borderColorMap = {
  success: '#22C55E',
  error: '#EF4444',
  info: '#3B82F6',
} as const;

export default function Toast() {
  const theme = useStore((s) => s.theme);
  const toasts = useStore((s) => s.toasts);
  const removeToast = useStore((s) => s.removeToast);
  const t = themes[theme];

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 24,
        right: 24,
        zIndex: 50,
        display: 'flex',
        flexDirection: 'column',
        gap: 8,
        pointerEvents: 'none',
      }}
    >
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = iconMap[toast.type];
          const borderColor = borderColorMap[toast.type];

          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 10, scale: 0.95 }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              style={{
                pointerEvents: 'auto',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '10px 14px',
                borderRadius: 10,
                background: t.surface,
                borderLeft: `3px solid ${borderColor}`,
                boxShadow: `0 4px 16px ${t.bg}88`,
                color: t.textPrimary,
                fontSize: 13,
                minWidth: 240,
                maxWidth: 360,
              }}
            >
              <Icon size={16} style={{ color: borderColor, flexShrink: 0 }} />
              <span style={{ flex: 1 }}>{toast.message}</span>
              <button
                onClick={() => removeToast(toast.id)}
                aria-label="Close toast"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  background: 'none',
                  border: 'none',
                  color: t.textMuted,
                  cursor: 'pointer',
                  padding: 2,
                  flexShrink: 0,
                }}
              >
                <X size={14} />
              </button>
            </motion.div>
          );
        })}
      </AnimatePresence>
    </div>
  );
}
