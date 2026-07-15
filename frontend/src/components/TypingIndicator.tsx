import { motion, AnimatePresence } from 'framer-motion';
import DistillLine from './DistillLine';
import AgentAvatar from './AgentAvatar';
import { useStore } from '../store';
import { themes } from '../theme';

interface Props {
  visible: boolean;
}

export default function TypingIndicator({ visible }: Props) {
  const t = themes[useStore((s) => s.theme)];

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="flex items-center gap-3"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.25 }}
        >
          <AgentAvatar size="sm" thinking />
          <span className="text-sm" style={{ color: t.textMuted }}>
            Analyzing…
          </span>
          <DistillLine variant="pulse" className="w-32" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
