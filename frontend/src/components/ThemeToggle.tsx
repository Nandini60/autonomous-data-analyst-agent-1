import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { themes } from '../theme';
import { useStore } from '../store';

export default function ThemeToggle() {
  const theme = useStore((s) => s.theme);
  const toggleTheme = useStore((s) => s.toggleTheme);
  const t = themes[theme];

  return (
    <motion.button
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      onClick={toggleTheme}
      aria-label="Toggle theme"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        width: 36,
        height: 36,
        borderRadius: 12,
        background: t.surface,
        border: `1px solid ${t.border}`,
        color: t.textPrimary,
        cursor: 'pointer',
      }}
    >
      {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
    </motion.button>
  );
}
