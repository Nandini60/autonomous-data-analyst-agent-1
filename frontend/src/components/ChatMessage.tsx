import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Clipboard,
  RotateCcw,
  Trash2,
  ChevronDown,
  ChevronUp,
  Clock,
  Database,
  AlertTriangle,
  Check,
  Sparkles,
} from 'lucide-react';
import AgentAvatar from './AgentAvatar';
import ConfidenceRing from './ConfidenceRing';
import ToolBadge from './ToolBadge';
import { useStore } from '../store';
import { themes } from '../theme';
import type { Message } from '../api';

interface Props {
  message: Message;
  index: number;
  onCopy?: () => void;
  onRegenerate?: () => void;
  onDelete?: () => void;
}

/** Basic markdown parser */
function renderContent(raw: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const regex = /(\*\*(.+?)\*\*|`(.+?)`)/g;
  let lastIndex = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = regex.exec(raw)) !== null) {
    if (match.index > lastIndex) {
      nodes.push(...textWithBreaks(raw.slice(lastIndex, match.index), key));
      key += 10;
    }

    if (match[2] !== undefined) {
      nodes.push(<strong key={`b${key++}`} className="font-bold text-[#f5f5f7]">{match[2]}</strong>);
    } else if (match[3] !== undefined) {
      nodes.push(
        <code
          key={`c${key++}`}
          className="px-1.5 py-0.5 rounded text-xs font-mono font-medium text-[#2dd4bf] bg-[#1a1a24] border border-white/5"
        >
          {match[3]}
        </code>,
      );
    }
    lastIndex = match.index + match[0].length;
  }

  if (lastIndex < raw.length) {
    nodes.push(...textWithBreaks(raw.slice(lastIndex), key));
  }

  return nodes;
}

function textWithBreaks(text: string, startKey: number): React.ReactNode[] {
  const parts = text.split('\n');
  const out: React.ReactNode[] = [];
  parts.forEach((p, i) => {
    if (i > 0) out.push(<br key={`br${startKey + i}`} />);
    if (p) out.push(<span key={`t${startKey + i}`}>{p}</span>);
  });
  return out;
}

export default function ChatMessage({
  message,
  index,
  onCopy,
  onRegenerate,
  onDelete,
}: Props) {
  const theme = useStore((s) => s.theme);
  const isDark = theme === 'dark';
  const t = themes[theme];

  const [hovered, setHovered] = useState(false);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);
  const [sqlExpanded, setSqlExpanded] = useState(false);
  const [warningsExpanded, setWarningsExpanded] = useState(false);
  const [copied, setCopied] = useState(false);

  const isUser = message.role === 'user';
  const meta = message.metadata ?? {};
  const toolsUsed: string[] = meta.tools_used ?? [];
  const confidence: number | undefined = meta.confidence;
  const executionTime: number | undefined = meta.execution_time;
  const sources: string[] = meta.sources ?? [];

  const handleCopy = () => {
    if (!message.content) return;
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    if (onCopy) onCopy();
    setTimeout(() => setCopied(false), 2000);
  };

  const handleCopySql = (sql: string, e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(sql);
    useStore.getState().addToast('SQL copied to clipboard', 'success');
  };

  return (
    <motion.div
      className={`flex gap-4 max-w-full ${isUser ? 'justify-end' : 'justify-start'}`}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut', delay: index * 0.04 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Assistant Avatar */}
      {!isUser && (
        <div className="flex-shrink-0 mt-0.5">
          <AgentAvatar size="sm" />
        </div>
      )}

      <div className="flex flex-col gap-2 relative group" style={{ maxWidth: '82%' }}>
        {/* Bubble */}
        <div
          className={`px-5 py-3.5 text-[14px] leading-relaxed transition-all duration-150 ${
            isUser
              ? 'rounded-2xl rounded-tr-sm text-[#f5f5f7] font-medium'
              : 'rounded-2xl rounded-tl-sm text-[#e4e4e9]'
          }`}
          style={{
            background: isUser
              ? 'linear-gradient(135deg, #7c6fe8, #6366f1)'
              : '#12121a',
            border: isDark ? '1px solid rgba(255,255,255,0.06)' : `1px solid ${t.border}`,
            boxShadow: isUser
              ? '0 4px 14px rgba(124,111,232,0.15)'
              : '0 4px 16px rgba(0,0,0,0.12)',
          }}
        >
          {renderContent(message.content)}
        </div>

        {/* SQL Query box */}
        {!isUser && meta.sql && (
          <div
            className="border rounded-xl overflow-hidden mt-1 transition-all"
            style={{
              borderColor: isDark ? 'rgba(255,255,255,0.06)' : t.border,
              background: '#12121a',
            }}
          >
            <button
              onClick={() => setSqlExpanded(!sqlExpanded)}
              className="w-full flex items-center justify-between px-4 py-2.5 text-xs font-semibold cursor-pointer transition-colors"
              style={{
                color: '#f5f5f7',
                background: '#1a1a24',
                borderBottom: sqlExpanded ? `1px solid ${isDark ? 'rgba(255,255,255,0.06)' : t.border}` : 'none',
              }}
            >
              <div className="flex items-center gap-2">
                <Database size={13} style={{ color: '#2dd4bf' }} />
                <span className="font-medium tracking-tight">View SQL Query</span>
              </div>
              <div className="flex items-center gap-2">
                {sqlExpanded && (
                  <span
                    onClick={(e) => handleCopySql(meta.sql, e)}
                    className="text-[10px] font-medium px-2 py-0.5 rounded bg-white/5 border border-white/10 hover:bg-white/10 transition-colors"
                    style={{ color: '#2dd4bf' }}
                  >
                    Copy
                  </span>
                )}
                {sqlExpanded ? <ChevronUp size={13} style={{ color: '#9a9aa8' }} /> : <ChevronDown size={13} style={{ color: '#9a9aa8' }} />}
              </div>
            </button>
            {sqlExpanded && (
              <pre
                className="p-4 text-[11px] font-mono overflow-x-auto text-[#2dd4bf] leading-relaxed"
                style={{
                  background: '#0d0d12',
                }}
              >
                {meta.sql}
              </pre>
            )}
          </div>
        )}

        {/* Warning messages */}
        {!isUser && meta.warnings && meta.warnings.length > 0 && (
          <div
            className="border rounded-xl overflow-hidden mt-1"
            style={{
              borderColor: 'rgba(245,158,11,0.2)',
              background: 'rgba(245,158,11,0.03)',
            }}
          >
            <button
              onClick={() => setWarningsExpanded(!warningsExpanded)}
              className="w-full flex items-center justify-between px-4 py-2 text-xs font-semibold cursor-pointer"
              style={{ color: '#f59e0b' }}
            >
              <div className="flex items-center gap-2">
                <AlertTriangle size={13} />
                <span>Warnings ({meta.warnings.length})</span>
              </div>
              {warningsExpanded ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>
            {warningsExpanded && (
              <ul className="px-4 pb-3 flex flex-col gap-1 text-[11px] list-disc list-inside text-[#9a9aa8]">
                {meta.warnings.map((w: string, i: number) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Metadata section (Badges, Ring, Execution Time) */}
        {!isUser && (toolsUsed.length > 0 || confidence !== undefined || executionTime !== undefined) && (
          <div className="flex flex-wrap items-center gap-3 px-1 mt-0.5">
            {toolsUsed.map((tool) => (
              <ToolBadge key={tool} tool={tool} />
            ))}

            {confidence !== undefined && (
              <div className="flex items-center gap-1.5">
                <ConfidenceRing value={confidence} size={28} />
                <span style={{ fontSize: 11, color: '#9a9aa8', fontWeight: 500 }}>Confidence</span>
              </div>
            )}

            {executionTime !== undefined && (
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-[#6b6b78]">
                <Clock size={11} />
                {executionTime.toFixed(2)}s
              </span>
            )}
          </div>
        )}

        {/* Sources list */}
        {!isUser && sources.length > 0 && (
          <div className="px-1">
            <button
              type="button"
              onClick={() => setSourcesExpanded((v) => !v)}
              className="inline-flex items-center gap-1.5 text-[11px] font-medium transition-colors hover:text-[#2dd4bf] cursor-pointer"
              style={{ color: '#7c6fe8' }}
            >
              <Sparkles size={11} />
              <span>{sources.length} document source{sources.length > 1 ? 's' : ''}</span>
              {sourcesExpanded ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
            </button>

            {sourcesExpanded && (
              <div
                className="mt-1.5 p-3 rounded-xl border flex flex-col gap-1 text-[11px] font-mono"
                style={{
                  background: '#12121a',
                  borderColor: 'rgba(255,255,255,0.06)',
                  color: '#9a9aa8',
                }}
              >
                {sources.map((src, i) => (
                  <div key={i} className="truncate flex items-center gap-2">
                    <span className="text-[#6b6b78]">{i + 1}.</span>
                    <span className="truncate" title={src}>{src}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Action Row - Clean modern ChatGPT/Claude style buttons overlay */}
        <div
          className="flex gap-1 px-1.5 py-1 rounded-lg items-center transition-all duration-200"
          style={{
            position: 'absolute',
            bottom: -28,
            [isUser ? 'right' : 'left']: 0,
            opacity: hovered ? 1 : 0,
            pointerEvents: hovered ? 'auto' : 'none',
          }}
        >
          <button
            type="button"
            onClick={handleCopy}
            className="flex items-center justify-center rounded-md transition-all hover:bg-white/5 cursor-pointer"
            style={{ width: 24, height: 24, color: copied ? '#2dd4bf' : '#9a9aa8', border: '1px solid rgba(255,255,255,0.05)', background: '#12121a' }}
            title="Copy response"
          >
            {copied ? <Check size={12} /> : <Clipboard size={12} />}
          </button>
          {onRegenerate && !isUser && (
            <button
              type="button"
              onClick={onRegenerate}
              className="flex items-center justify-center rounded-md transition-all hover:bg-white/5 cursor-pointer"
              style={{ width: 24, height: 24, color: '#9a9aa8', border: '1px solid rgba(255,255,255,0.05)', background: '#12121a' }}
              title="Regenerate message"
            >
              <RotateCcw size={12} />
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={onDelete}
              className="flex items-center justify-center rounded-md transition-all hover:bg-white/5 cursor-pointer"
              style={{ width: 24, height: 24, color: '#ef4444', border: '1px solid rgba(255,255,255,0.05)', background: '#12121a' }}
              title="Delete message"
            >
              <Trash2 size={12} />
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
