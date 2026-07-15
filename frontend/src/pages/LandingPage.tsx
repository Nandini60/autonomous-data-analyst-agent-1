import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  FileText,
  Database,
  Sparkles,
  Shield,
  Play,
  Volume2,
  Upload,
  MessageSquare,
  BarChart3,
  ChevronRight,
} from 'lucide-react';
import { useStore } from '../store';

/* ─── Design Tokens ──────────────────────────────────────────── */
const tk = {
  bg: '#0a0a0f',
  surface: '#12121a',
  border: 'rgba(255,255,255,0.08)',
  accent1: '#7c6fe8',   // purple
  accent2: '#2dd4bf',   // teal
  textPrimary: '#f5f5f7',
  textSecondary: '#9a9aa8',
  textMuted: '#6b6b78',
  gradient: 'linear-gradient(135deg, #7c6fe8, #2dd4bf)',
};

/* ─── Shared animation variants ──────────────────────────────── */
const fadeUp = {
  hidden: { opacity: 0, y: 60 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.08, duration: 0.4, ease: 'easeOut' as const },
  }),
};

const sectionVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.08 } },
};

/* ─── Data ───────────────────────────────────────────────────── */
const steps = [
  {
    num: '1',
    title: 'Ingest',
    desc: 'Upload CSVs, PDFs, DOCX, or spreadsheets. Schema and content are auto-detected.',
    Icon: Upload,
    color: tk.accent1,
  },
  {
    num: '2',
    title: 'Distill',
    desc: 'The agent extracts structure, builds embeddings, and preps SQL-ready tables in seconds.',
    Icon: Sparkles,
    color: tk.accent2,
  },
  {
    num: '3',
    title: 'Respond',
    desc: 'Ask anything in natural language. Get answers, charts, or voice playback instantly.',
    Icon: MessageSquare,
    color: '#a78bfa',
  },
];

const capabilities = [
  {
    title: 'SQL generation',
    desc: 'Turns natural-language questions into query-ready SQL against your indexed tables. No syntax knowledge required — just ask, and Distill writes the query for you.',
    Icon: Database,
    color: tk.accent1,
  },
  {
    title: 'PDF parsing',
    desc: 'Extracts text, tables, and layout from both scanned and native PDFs with high fidelity. Complex multi-column documents and embedded images are handled automatically.',
    Icon: FileText,
    color: '#f472b6',
  },
  {
    title: 'Data visualization',
    desc: 'Renders bar charts, line graphs, and scatter plots straight from a conversational prompt. No dashboard setup needed — visuals are generated on the fly.',
    Icon: BarChart3,
    color: tk.accent2,
  },
  {
    title: 'Voice answers',
    desc: 'Reads results back out loud for hands-free review and accessibility. Ideal for summarizing lengthy documents while you multitask.',
    Icon: Volume2,
    color: '#a78bfa',
  },
  {
    title: 'Smart upload',
    desc: 'Detects file type, encoding, and schema automatically — no manual column mapping required. Drag-and-drop any supported format and start querying in seconds.',
    Icon: Upload,
    color: '#fbbf24',
  },
  {
    title: 'Secure analysis',
    desc: 'All documents are encrypted in transit and at rest during processing. Your data never leaves the analysis sandbox and is purged on session end.',
    Icon: Shield,
    color: '#34d399',
  },
];

const footerLinks = [
  { heading: 'Product', links: ['Features', 'Pricing', 'Changelog', 'Roadmap'] },
  { heading: 'Resources', links: ['Documentation', 'API reference', 'Community', 'Blog'] },
  { heading: 'Company', links: ['About', 'Careers', 'Contact', 'Privacy policy'] },
];

/* ─── Component ──────────────────────────────────────────────── */
interface Props {
  onNavigate: (p: string) => void;
}

export default function LandingPage({ onNavigate }: Props) {
  const user = useStore((s) => s.user);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handler = () => setScrolled(window.scrollY > 50);
    window.addEventListener('scroll', handler, { passive: true });
    return () => window.removeEventListener('scroll', handler);
  }, []);

  return (
    <div
      className="min-h-screen w-full flex flex-col overflow-x-hidden"
      style={{
        background: tk.bg,
        color: tk.textPrimary,
        fontFamily: "'Inter', 'Geist', system-ui, sans-serif",
        fontWeight: 400,
        lineHeight: 1.6,
      }}
    >
      {/* ── Nav ─────────────────────────────────────────────── */}
      <nav
        className="fixed top-0 left-0 right-0 z-50 transition-all duration-300"
        style={{
          height: 72,
          borderBottom: scrolled ? `1px solid ${tk.border}` : '1px solid transparent',
          background: scrolled ? 'rgba(10,10,15,0.8)' : 'transparent',
          backdropFilter: scrolled ? 'blur(16px)' : 'none',
          WebkitBackdropFilter: scrolled ? 'blur(16px)' : 'none',
        }}
      >
        <div
          className="h-full flex items-center justify-between mx-auto"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          {/* Logo */}
          <div
            className="flex items-center gap-2.5 cursor-pointer select-none"
            onClick={() => onNavigate('landing')}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round">
              <path d="M4 4c4 4 6 12 8 16" stroke={tk.accent1} />
              <path d="M20 4c-4 4-6 12-8 16" stroke={tk.accent2} />
              <path d="M12 4v16" stroke={tk.textPrimary} />
            </svg>
            <span style={{ fontSize: 18, fontWeight: 500, color: tk.textPrimary, letterSpacing: '-0.02em' }}>
              Distill
            </span>
          </div>

          {/* Center links — hidden on mobile */}
          <div className="hidden md:flex items-center gap-8">
            {[
              { label: 'Features', href: '#capabilities' },
              { label: 'How it works', href: '#how-it-works' },
              { label: 'About', href: '#cta' },
            ].map((l) => (
              <a
                key={l.label}
                href={l.href}
                className="no-underline transition-colors duration-150"
                style={{ color: tk.textSecondary, fontSize: 14, fontWeight: 500 }}
                onMouseEnter={(e) => (e.currentTarget.style.color = tk.textPrimary)}
                onMouseLeave={(e) => (e.currentTarget.style.color = tk.textSecondary)}
              >
                {l.label}
              </a>
            ))}
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-3">
            {user ? (
              <motion.button
                whileHover={{ scale: 1.03 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onNavigate('chat')}
                className="border-0 cursor-pointer"
                style={{
                  background: tk.gradient,
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 500,
                  padding: '10px 22px',
                  borderRadius: 8,
                }}
              >
                Go to Workspace
              </motion.button>
            ) : (
              <>
                <button
                  onClick={() => onNavigate('login')}
                  className="bg-transparent border-0 cursor-pointer transition-colors duration-150"
                  style={{ color: tk.textSecondary, fontSize: 14, fontWeight: 500 }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = tk.textPrimary)}
                  onMouseLeave={(e) => (e.currentTarget.style.color = tk.textSecondary)}
                >
                  Sign in
                </button>
                <motion.button
                  whileHover={{ scale: 1.03, boxShadow: `0 0 24px ${tk.accent1}40` }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onNavigate('register')}
                  className="border-0 cursor-pointer"
                  style={{
                    background: tk.gradient,
                    color: '#fff',
                    fontSize: 14,
                    fontWeight: 500,
                    padding: '10px 22px',
                    borderRadius: 8,
                    transition: 'box-shadow 150ms ease',
                  }}
                >
                  Get started
                </motion.button>
              </>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero ────────────────────────────────────────────── */}
      <section style={{ paddingTop: 160, paddingBottom: 96 }}>
        <motion.div
          initial="hidden"
          animate="visible"
          variants={sectionVariants}
          className="flex flex-col items-center text-center mx-auto"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          {/* Badge pill */}
          <motion.div
            variants={fadeUp}
            custom={0}
            className="inline-flex items-center gap-2 mb-8"
            style={{
              padding: '6px 16px',
              borderRadius: 999,
              border: `1px solid ${tk.accent1}30`,
              background: `${tk.accent1}08`,
              color: tk.accent2,
              fontSize: 13,
              fontWeight: 500,
              letterSpacing: '0.02em',
            }}
          >
            <Sparkles size={14} />
            Next-gen document intelligence
          </motion.div>

          {/* Headline */}
          <motion.h1
            variants={fadeUp}
            custom={1}
            style={{
              fontSize: 'clamp(36px, 5vw, 48px)',
              fontWeight: 500,
              lineHeight: 1.15,
              letterSpacing: '-0.03em',
              margin: 0,
              maxWidth: 720,
              color: tk.textPrimary,
            }}
          >
            Turn any document{' '}
            <span
              style={{
                background: tk.gradient,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
              }}
            >
              into a conversation
            </span>
          </motion.h1>

          {/* Subhead */}
          <motion.p
            variants={fadeUp}
            custom={2}
            style={{
              fontSize: 16,
              color: tk.textSecondary,
              maxWidth: 520,
              marginTop: 20,
              marginBottom: 0,
            }}
          >
            Upload a CSV, PDF, or spreadsheet. Distill parses it, indexes it, and lets you ask questions in plain language.
          </motion.p>

          {/* CTA buttons */}
          <motion.div
            variants={fadeUp}
            custom={3}
            className="flex items-center gap-4"
            style={{ marginTop: 40 }}
          >
            {user ? (
              <motion.button
                whileHover={{ scale: 1.03, boxShadow: `0 0 28px ${tk.accent1}35` }}
                whileTap={{ scale: 0.97 }}
                onClick={() => onNavigate('chat')}
                className="flex items-center gap-2 border-0 cursor-pointer"
                style={{
                  background: tk.gradient,
                  color: '#fff',
                  fontSize: 15,
                  fontWeight: 500,
                  padding: '14px 32px',
                  borderRadius: 8,
                  transition: 'box-shadow 150ms ease',
                }}
              >
                Go to Workspace
                <ArrowRight size={16} />
              </motion.button>
            ) : (
              <>
                <motion.button
                  whileHover={{ scale: 1.03, boxShadow: `0 0 28px ${tk.accent1}35` }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onNavigate('register')}
                  className="flex items-center gap-2 border-0 cursor-pointer"
                  style={{
                    background: tk.gradient,
                    color: '#fff',
                    fontSize: 15,
                    fontWeight: 500,
                    padding: '14px 32px',
                    borderRadius: 8,
                    transition: 'box-shadow 150ms ease',
                  }}
                >
                  Start free
                  <ArrowRight size={16} />
                </motion.button>
                <motion.button
                  whileHover={{ scale: 1.03 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => onNavigate('login')}
                  className="flex items-center gap-2 cursor-pointer"
                  style={{
                    background: 'transparent',
                    color: tk.textPrimary,
                    fontSize: 15,
                    fontWeight: 500,
                    padding: '14px 32px',
                    borderRadius: 8,
                    border: `1px solid ${tk.border}`,
                    transition: 'border-color 150ms ease',
                  }}
                  onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.2)')}
                  onMouseLeave={(e) => (e.currentTarget.style.borderColor = tk.border)}
                >
                  <Play size={14} />
                  Watch demo
                </motion.button>
              </>
            )}
          </motion.div>

          {/* Product mockup */}
          <motion.div
            variants={fadeUp}
            custom={4}
            className="relative w-full mx-auto"
            style={{ marginTop: 72, maxWidth: 900 }}
          >
            {/* Soft glow BEHIND the image */}
            <div
              className="absolute pointer-events-none"
              style={{
                inset: '15% 10%',
                background: `radial-gradient(ellipse at center, ${tk.accent1}18, ${tk.accent2}10, transparent 70%)`,
                filter: 'blur(60px)',
                zIndex: 0,
              }}
            />
            <div
              className="relative overflow-hidden"
              style={{
                borderRadius: 12,
                border: `1px solid ${tk.border}`,
                background: tk.surface,
                zIndex: 1,
              }}
            >
              <img
                src="/distill_dashboard_mockup.jpg"
                alt="Distill product dashboard"
                className="w-full h-auto block"
                style={{ opacity: 0.92 }}
              />
            </div>
          </motion.div>
        </motion.div>
      </section>

      {/* ── Stats strip ─────────────────────────────────────── */}
      <section style={{ padding: '48px 0', borderTop: `1px solid ${tk.border}`, borderBottom: `1px solid ${tk.border}` }}>
        <div
          className="mx-auto flex flex-wrap items-center justify-center gap-12 md:gap-20"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          {[
            { value: '10+', label: 'File formats supported' },
            { value: '<3s', label: 'Average parse time' },
            { value: '99.5%', label: 'Extraction accuracy' },
            { value: 'E2E', label: 'Encrypted pipeline' },
          ].map((stat) => (
            <div key={stat.label} className="flex flex-col items-center text-center gap-1">
              <span style={{ fontSize: 28, fontWeight: 500, color: tk.textPrimary, letterSpacing: '-0.02em' }}>
                {stat.value}
              </span>
              <span style={{ fontSize: 13, color: tk.textMuted, fontWeight: 400 }}>
                {stat.label}
              </span>
            </div>
          ))}
        </div>
      </section>

      {/* ── How Distill Works ───────────────────────────────── */}
      <section id="how-it-works" style={{ padding: '96px 0' }}>
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          variants={sectionVariants}
          className="mx-auto"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          <motion.div variants={fadeUp} custom={0} className="text-center" style={{ marginBottom: 64 }}>
            <h2
              style={{
                fontSize: 'clamp(32px, 4vw, 40px)',
                fontWeight: 500,
                letterSpacing: '-0.02em',
                margin: '0 0 12px',
                color: tk.textPrimary,
              }}
            >
              How Distill works
            </h2>
            <p style={{ fontSize: 16, color: tk.textSecondary, margin: 0 }}>
              Three steps from raw document to answers.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 md:gap-8 relative overflow-hidden">
            {/* Connecting line on desktop */}
            <div
              className="absolute hidden md:block"
              style={{
                top: 44,
                left: '20%',
                right: '20%',
                height: 1,
                background: `linear-gradient(90deg, transparent, ${tk.border}, ${tk.border}, transparent)`,
              }}
            />

            {steps.map((step, i) => {
              const StepIcon = step.Icon;
              return (
                <motion.div
                  key={step.title}
                  variants={fadeUp}
                  custom={i + 1}
                  className="flex flex-col items-center text-center relative z-10"
                  style={{ padding: '32px 24px' }}
                >
                  {/* Icon circle */}
                  <div
                    className="flex items-center justify-center"
                    style={{
                      width: 56,
                      height: 56,
                      borderRadius: 14,
                      background: `${step.color}12`,
                      border: `1px solid ${step.color}25`,
                      marginBottom: 24,
                    }}
                  >
                    <StepIcon size={24} style={{ color: step.color }} />
                  </div>
                  <h3
                    style={{
                      fontSize: 18,
                      fontWeight: 500,
                      margin: '0 0 8px',
                      color: tk.textPrimary,
                    }}
                  >
                    {step.num}. {step.title}
                  </h3>
                  <p
                    style={{
                      fontSize: 15,
                      color: tk.textSecondary,
                      margin: 0,
                      maxWidth: 280,
                    }}
                  >
                    {step.desc}
                  </p>

                  {/* Arrow between steps on desktop */}
                  {i < steps.length - 1 && (
                    <div
                      className="absolute hidden md:flex items-center justify-center"
                      style={{
                        right: -16,
                        top: 44,
                        width: 32,
                        height: 32,
                      }}
                    >
                      <ChevronRight size={18} style={{ color: tk.textMuted }} />
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </section>

      {/* ── Capabilities ────────────────────────────────────── */}
      <section id="capabilities" style={{ padding: '96px 0' }}>
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          variants={sectionVariants}
          className="mx-auto"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          <motion.div variants={fadeUp} custom={0} className="text-center" style={{ marginBottom: 64 }}>
            <h2
              style={{
                fontSize: 'clamp(32px, 4vw, 40px)',
                fontWeight: 500,
                letterSpacing: '-0.02em',
                margin: '0 0 12px',
                color: tk.textPrimary,
              }}
            >
              Capabilities
            </h2>
            <p style={{ fontSize: 16, color: tk.textSecondary, margin: 0 }}>
              Everything you need for document-driven intelligence.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {capabilities.map((cap, i) => {
              const CapIcon = cap.Icon;
              return (
                <motion.div
                  key={cap.title}
                  variants={fadeUp}
                  custom={i + 1}
                  className="group cursor-default"
                  style={{
                    background: tk.surface,
                    border: `1px solid ${tk.border}`,
                    borderRadius: 12,
                    padding: '28px 24px',
                    transition: 'transform 200ms ease, border-color 200ms ease, box-shadow 200ms ease',
                  }}
                  whileHover={{
                    y: -4,
                    borderColor: 'rgba(255,255,255,0.15)',
                    boxShadow: `0 16px 40px rgba(0,0,0,0.3)`,
                  }}
                >
                  <div
                    className="flex items-center justify-center"
                    style={{
                      width: 40,
                      height: 40,
                      borderRadius: 10,
                      background: `${cap.color}12`,
                      border: `1px solid ${cap.color}20`,
                      marginBottom: 16,
                    }}
                  >
                    <CapIcon size={18} style={{ color: cap.color }} />
                  </div>
                  <h3
                    style={{
                      fontSize: 16,
                      fontWeight: 500,
                      margin: '0 0 8px',
                      color: tk.textPrimary,
                    }}
                  >
                    {cap.title}
                  </h3>
                  <p
                    style={{
                      fontSize: 14,
                      color: tk.textSecondary,
                      margin: 0,
                      lineHeight: 1.6,
                    }}
                  >
                    {cap.desc}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </motion.div>
      </section>

      {/* ── Closing CTA ─────────────────────────────────────── */}
      <section id="cta" style={{ padding: '96px 0' }}>
        <motion.div
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: '-80px' }}
          variants={sectionVariants}
          className="mx-auto"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          <motion.div
            variants={fadeUp}
            custom={0}
            className="flex flex-col items-center text-center relative overflow-hidden"
            style={{
              background: tk.surface,
              borderRadius: 16,
              padding: 'clamp(40px, 6vw, 72px) clamp(24px, 4vw, 64px)',
              border: `1px solid ${tk.border}`,
              /* subtle gradient border glow */
              boxShadow: `inset 0 0 0 1px rgba(124,111,232,0.08), 0 0 80px rgba(124,111,232,0.06)`,
            }}
          >
            {/* Faint gradient accent top-line */}
            <div
              className="absolute top-0 left-0 right-0"
              style={{
                height: 1,
                background: tk.gradient,
                opacity: 0.4,
              }}
            />

            <h3
              style={{
                fontSize: 'clamp(24px, 3.5vw, 32px)',
                fontWeight: 500,
                letterSpacing: '-0.02em',
                margin: '0 0 12px',
                color: tk.textPrimary,
              }}
            >
              Ready to distill your documents?
            </h3>
            <p
              style={{
                fontSize: 16,
                color: tk.textSecondary,
                margin: '0 0 32px',
                maxWidth: 480,
              }}
            >
              Create a free sandbox account and start chatting with your PDFs, CSVs, and spreadsheets.
            </p>
            <motion.button
              whileHover={{ scale: 1.03, boxShadow: `0 0 28px ${tk.accent1}35` }}
              whileTap={{ scale: 0.97 }}
              onClick={() => onNavigate('register')}
              className="flex items-center gap-2 border-0 cursor-pointer"
              style={{
                background: tk.gradient,
                color: '#fff',
                fontSize: 15,
                fontWeight: 500,
                padding: '14px 32px',
                borderRadius: 8,
                transition: 'box-shadow 150ms ease',
              }}
            >
              Get started now
              <ArrowRight size={16} />
            </motion.button>
          </motion.div>
        </motion.div>
      </section>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer
        style={{
          borderTop: `1px solid ${tk.border}`,
          padding: '64px 0 40px',
        }}
      >
        <div
          className="mx-auto grid grid-cols-2 md:grid-cols-5 gap-10 md:gap-8"
          style={{ maxWidth: 1120, padding: '0 24px', margin: '0 auto' }}
        >
          {/* Logo column */}
          <div className="col-span-2">
            <div className="flex items-center gap-2 mb-4">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round">
                <path d="M4 4c4 4 6 12 8 16" stroke={tk.accent1} />
                <path d="M20 4c-4 4-6 12-8 16" stroke={tk.accent2} />
                <path d="M12 4v16" stroke={tk.textMuted} />
              </svg>
              <span style={{ fontSize: 16, fontWeight: 500, color: tk.textSecondary }}>
                Distill
              </span>
            </div>
            <p style={{ fontSize: 14, color: tk.textMuted, maxWidth: 260, margin: 0, lineHeight: 1.6 }}>
              Autonomous document intelligence — parse, index, and converse with any file.
            </p>
          </div>

          {/* Link columns */}
          {footerLinks.map((col) => (
            <div key={col.heading}>
              <h4
                style={{
                  fontSize: 13,
                  fontWeight: 500,
                  color: tk.textSecondary,
                  margin: '0 0 16px',
                  letterSpacing: '0.03em',
                  textTransform: 'uppercase',
                }}
              >
                {col.heading}
              </h4>
              <ul className="list-none p-0 m-0 flex flex-col gap-2.5">
                {col.links.map((link) => (
                  <li key={link}>
                    <button
                      className="bg-transparent border-0 p-0 cursor-pointer transition-colors duration-150"
                      style={{ color: tk.textMuted, fontSize: 14, fontWeight: 400 }}
                      onMouseEnter={(e) => (e.currentTarget.style.color = tk.textSecondary)}
                      onMouseLeave={(e) => (e.currentTarget.style.color = tk.textMuted)}
                    >
                      {link}
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Copyright */}
        <div
          className="mx-auto"
          style={{
            maxWidth: 1120,
            padding: '32px 24px 0',
            borderTop: `1px solid ${tk.border}`,
            marginTop: 48,
            margin: '48px auto 0',
          }}
        >
          <p style={{ fontSize: 13, color: tk.textMuted, margin: 0 }}>
            &copy; {new Date().getFullYear()} Distill — Autonomous Document Intelligence. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
