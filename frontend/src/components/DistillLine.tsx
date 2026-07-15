import { motion } from 'framer-motion';
import { themes } from '../theme';
import { useStore } from '../store';

interface DistillLineProps {
  variant: 'sweep' | 'pulse' | 'progress' | 'waveform';
  progress?: number;
  className?: string;
}

export default function DistillLine({ variant, progress = 0, className = '' }: DistillLineProps) {
  const theme = useStore((s) => s.theme);
  const t = themes[theme];

  if (variant === 'sweep') {
    return (
      <div
        className={`animate-distill-sweep ${className}`}
        style={{
          height: 2,
          borderRadius: 1,
          background: `linear-gradient(90deg, ${t.accentAgent}, ${t.accentSignal})`,
          boxShadow: `0 0 8px ${t.accentSignal}44, 0 0 2px ${t.accentAgent}66`,
        }}
      />
    );
  }

  if (variant === 'pulse') {
    return (
      <div
        className={`animate-distill-pulse ${className}`}
        style={{
          height: 2,
          width: 48,
          borderRadius: 1,
          background: `linear-gradient(90deg, ${t.accentAgent}, ${t.accentSignal})`,
        }}
      />
    );
  }

  if (variant === 'progress') {
    return (
      <div
        className={className}
        style={{
          height: 2,
          borderRadius: 1,
          background: t.border,
          overflow: 'hidden',
        }}
      >
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          style={{
            height: '100%',
            borderRadius: 1,
            background: `linear-gradient(90deg, ${t.accentAgent}, ${t.accentSignal})`,
          }}
        />
      </div>
    );
  }

  // waveform
  const barHeights = [12, 20, 16, 22, 14];
  return (
    <div className={className} style={{ display: 'flex', alignItems: 'flex-end', gap: 2, height: 24 }}>
      {barHeights.map((h, i) => (
        <motion.div
          key={i}
          animate={{ height: [h * 0.4, h, h * 0.4] }}
          transition={{
            duration: 0.8,
            repeat: Infinity,
            delay: i * 0.1,
            ease: 'easeInOut',
          }}
          style={{
            width: 3,
            borderRadius: 1.5,
            background: `linear-gradient(180deg, ${t.accentSignal}, ${t.accentAgent})`,
          }}
        />
      ))}
    </div>
  );
}
