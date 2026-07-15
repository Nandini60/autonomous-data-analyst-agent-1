import { themes } from '../theme';
import { useStore } from '../store';

interface ConfidenceRingProps {
  value: number;
  size?: number;
}

export default function ConfidenceRing({ value, size = 32 }: ConfidenceRingProps) {
  const theme = useStore((s) => s.theme);
  const t = themes[theme];

  const clamped = Math.min(100, Math.max(0, value));
  const color = clamped >= 80 ? t.success : clamped >= 50 ? t.warning : t.error;

  const strokeWidth = 3;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (clamped / 100) * circumference;

  return (
    <div style={{ position: 'relative', width: size, height: size, flexShrink: 0 }}>
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={t.border}
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{ transition: 'stroke-dashoffset 0.4s ease' }}
        />
      </svg>
      <span
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: 'monospace',
          fontSize: size * 0.3,
          fontWeight: 600,
          color: t.textPrimary,
        }}
      >
        {clamped}
      </span>
    </div>
  );
}
