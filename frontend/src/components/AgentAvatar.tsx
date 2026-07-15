import { themes } from '../theme';
import { useStore } from '../store';

interface AgentAvatarProps {
  size?: 'sm' | 'md' | 'lg';
  thinking?: boolean;
}

const sizeMap = { sm: 28, md: 40, lg: 56 } as const;

export default function AgentAvatar({ size = 'md', thinking = false }: AgentAvatarProps) {
  const theme = useStore((s) => s.theme);
  const t = themes[theme];
  const px = sizeMap[size];

  return (
    <div
      style={{
        position: 'relative',
        width: px,
        height: px,
        flexShrink: 0,
      }}
    >
      {thinking && (
        <div
          className="animate-distill-pulse"
          style={{
            position: 'absolute',
            inset: -3,
            borderRadius: '50%',
            border: `2px solid ${t.accentSignal}`,
            opacity: 0.6,
          }}
        />
      )}
      <div
        style={{
          width: px,
          height: px,
          borderRadius: '50%',
          background: `linear-gradient(135deg, ${t.accentAgent}, ${t.accentSignal})`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#fff',
          overflow: 'hidden',
          border: `1.5px solid ${t.border}`,
        }}
      >
        <img
          src="/robot_mascot.jpg"
          alt="AI Agent"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
          onError={(e) => {
            (e.target as HTMLElement).style.display = 'none';
          }}
        />
      </div>
    </div>
  );
}
