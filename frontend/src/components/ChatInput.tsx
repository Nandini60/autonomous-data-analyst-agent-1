import { useState, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { SendHorizontal, Mic, Square, Paperclip } from 'lucide-react';
import DistillLine from './DistillLine';
import { useStore } from '../store';
import { themes } from '../theme';

interface Props {
  onSend: (text: string) => void;
  onUpload?: (file: File) => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, onUpload, disabled = false }: Props) {
  const theme = useStore((s) => s.theme);
  const isDark = theme === 'dark';
  const t = themes[theme];
  
  const [text, setText] = useState('');
  const [listening, setListening] = useState(false);
  const [focused, setFocused] = useState(false);
  const recognitionRef = useRef<any>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && onUpload) {
      onUpload(file);
    }
  };

  const triggerUpload = () => {
    fileInputRef.current?.click();
  };

  const autoGrow = useCallback(() => {
    const ta = textareaRef.current;
    if (!ta) return;
    ta.style.height = '40px';
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  }, []);

  const handleSend = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    if (textareaRef.current) textareaRef.current.style.height = '40px';
  }, [text, disabled, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  const toggleMic = useCallback(() => {
    if (listening) {
      recognitionRef.current?.stop();
      setListening(false);
      return;
    }

    const SpeechRecognitionCtor =
      (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition;
    if (!SpeechRecognitionCtor) return;

    const recognition = new SpeechRecognitionCtor();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setText((prev) => (prev ? `${prev} ${transcript}` : transcript));
      autoGrow();
    };

    recognition.onend = () => setListening(false);
    recognition.onerror = () => setListening(false);

    recognitionRef.current = recognition;
    recognition.start();
    setListening(true);
  }, [listening, autoGrow]);

  const canSend = text.trim().length > 0 && !disabled;

  return (
    <div
      className="flex flex-col gap-2 p-3 transition-all duration-200"
      style={{
        background: isDark ? '#12121a' : t.surface,
        border: `1px solid ${focused ? (isDark ? 'rgba(124,111,232,0.4)' : t.accentAgent) : (isDark ? 'rgba(255,255,255,0.06)' : t.border)}`,
        borderRadius: 14,
        boxShadow: focused
          ? (isDark ? '0 8px 32px rgba(0,0,0,0.5), 0 0 0 1px rgba(124,111,232,0.1)' : `0 8px 32px ${t.accentAgent}08`)
          : '0 8px 32px rgba(0,0,0,0.3)',
      }}
    >
      {/* Waveform indicator when listening */}
      <AnimatePresence>
        {listening && (
          <motion.div
            className="flex items-center gap-2 px-1"
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
          >
            <span
              className="w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: '#ef4444' }}
            />
            <DistillLine variant="waveform" className="flex-1" />
          </motion.div>
        )}
      </AnimatePresence>

      {/* Input row */}
      <div className="flex items-end gap-2">
        {/* File upload */}
        {onUpload && (
          <>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileChange}
              accept=".csv,.pdf,.docx,.xlsx,.xls,.txt"
              className="hidden"
            />
            <button
              type="button"
              onClick={triggerUpload}
              disabled={disabled}
              className="flex items-center justify-center rounded-xl flex-shrink-0 transition-all hover:bg-white/5 active:scale-95 cursor-pointer"
              style={{
                width: 40,
                height: 40,
                background: '#1a1a24',
                border: '1px solid rgba(255,255,255,0.05)',
                color: '#9a9aa8',
              }}
              title="Upload file"
            >
              <Paperclip size={16} />
            </button>
          </>
        )}

        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => {
            setText(e.target.value);
            autoGrow();
          }}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={handleKeyDown}
          placeholder="Ask Distill a question..."
          rows={1}
          className="flex-1 resize-none outline-none text-[14px] leading-relaxed py-2 font-body"
          style={{
            background: 'transparent',
            color: '#f5f5f7',
            minHeight: 40,
            maxHeight: 180,
          }}
        />

        {/* Mic button */}
        <button
          type="button"
          onClick={toggleMic}
          className="flex items-center justify-center rounded-xl flex-shrink-0 transition-all hover:scale-105 active:scale-95 cursor-pointer"
          style={{
            width: 40,
            height: 40,
            background: listening ? '#ef4444' : '#1a1a24',
            border: listening ? 'none' : '1px solid rgba(255,255,255,0.05)',
            color: listening ? '#fff' : '#9a9aa8',
          }}
          title="Speech input"
        >
          {listening ? <Square size={14} /> : <Mic size={16} />}
        </button>

        {/* Send button */}
        <button
          type="button"
          onClick={handleSend}
          disabled={!canSend}
          className="flex items-center justify-center rounded-xl flex-shrink-0 transition-all active:scale-95"
          style={{
            width: 40,
            height: 40,
            background: canSend ? 'linear-gradient(135deg, #7c6fe8, #2dd4bf)' : '#1a1a24',
            border: canSend ? 'none' : '1px solid rgba(255,255,255,0.05)',
            color: canSend ? '#fff' : '#6b6b78',
            cursor: canSend ? 'pointer' : 'not-allowed',
            transition: 'box-shadow 150ms ease, opacity 150ms ease',
          }}
          title="Send message"
        >
          <SendHorizontal size={16} />
        </button>
      </div>
    </div>
  );
}
