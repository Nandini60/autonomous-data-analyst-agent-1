import { themes } from '../theme';
import { useStore } from '../store';

interface ToolBadgeProps {
  tool: string;
}

const toolColors: Record<string, string> = {
  SQL: '#3B82F6',
  RAG: '#10B981',
  CODE: '#F59E0B',
};

export default function ToolBadge({ tool }: ToolBadgeProps) {
  const theme = useStore((s) => s.theme);
  const t = themes[theme];

  const color = toolColors[tool.toUpperCase()] || t.accentAgent;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '2px 8px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        lineHeight: '18px',
        letterSpacing: '0.02em',
        color,
        background: `${color}26`,
      }}
    >
      {tool.toUpperCase()}
    </span>
  );
}
