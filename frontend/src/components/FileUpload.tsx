import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { motion } from 'framer-motion';
import { Upload, FileText, FileSpreadsheet } from 'lucide-react';
import DistillLine from './DistillLine';
import { useStore } from '../store';
import { themes } from '../theme';

interface Props {
  onUpload: (file: File) => void;
  isUploading: boolean;
  progress: number;
  variant?: 'full' | 'compact';
}

const ACCEPT: Record<string, string[]> = {
  'text/csv': ['.csv'],
  'application/pdf': ['.pdf'],
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
  'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
  'text/plain': ['.txt'],
};

export default function FileUpload({
  onUpload,
  isUploading,
  progress,
  variant = 'full',
}: Props) {
  const t = themes[useStore((s) => s.theme)];
  const [fileName, setFileName] = useState<string | null>(null);

  const onDrop = useCallback(
    (accepted: File[]) => {
      const file = accepted[0];
      if (!file) return;
      setFileName(file.name);
      onUpload(file);
    },
    [onUpload],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPT,
    multiple: false,
    disabled: isUploading,
  });

  /* ── Compact variant ── */
  if (variant === 'compact') {
    return (
      <button
        type="button"
        {...getRootProps()}
        className="inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors"
        style={{
          background: t.elevated,
          color: t.textMuted,
          border: `1px solid ${t.border}`,
        }}
      >
        <input {...getInputProps()} />
        <Upload size={14} />
        Upload File
      </button>
    );
  }

  /* ── Full variant ── */
  const isSpreadsheet = fileName
    ? /\.(csv|xlsx)$/i.test(fileName)
    : false;
  const FileIcon = isSpreadsheet ? FileSpreadsheet : FileText;

  return (
    <motion.div
      {...(getRootProps() as any)}
      className="rounded-xl flex flex-col items-center justify-center gap-3 p-8 cursor-pointer transition-colors"
      style={{
        border: `2px dashed ${isDragActive ? t.accentSignal : t.border}`,
        background: isDragActive ? `${t.accentSignal}08` : 'transparent',
      }}
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
    >
      <input {...getInputProps()} />

      {isUploading ? (
        /* Uploading state */
        <>
          <FileIcon size={32} style={{ color: t.accentAgent }} />
          {fileName && (
            <span
              className="text-sm font-medium truncate max-w-[200px]"
              style={{ color: t.textPrimary }}
            >
              {fileName}
            </span>
          )}
          <DistillLine variant="progress" progress={progress} className="w-48" />
          <span className="text-xs" style={{ color: t.textMuted }}>
            Processing…
          </span>
        </>
      ) : (
        /* Idle state */
        <>
          <Upload size={32} style={{ color: t.textMuted }} />
          <span className="text-sm font-medium" style={{ color: t.textPrimary }}>
            Drop a file or click to browse
          </span>
          <span className="text-xs" style={{ color: t.textMuted }}>
            CSV, PDF, DOCX, XLSX, TXT
          </span>
        </>
      )}
    </motion.div>
  );
}
