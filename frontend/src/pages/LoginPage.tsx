import { useState } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Eye, EyeOff, LogIn } from 'lucide-react';
import { useStore } from '../store';
import * as api from '../api';

/* ─── Design Tokens (matching landing page) ─── */
const tk = {
  bg: '#0a0a0f',
  surface: '#12121a',
  border: 'rgba(255,255,255,0.08)',
  accent1: '#7c6fe8',
  accent2: '#2dd4bf',
  textPrimary: '#f5f5f7',
  textSecondary: '#9a9aa8',
  textMuted: '#6b6b78',
  gradient: 'linear-gradient(135deg, #7c6fe8, #2dd4bf)',
  error: '#ef4444',
  elevated: '#1a1a24',
};

interface Props {
  onNavigate: (p: string) => void;
}

export default function LoginPage({ onNavigate }: Props) {
  const setUser = useStore((s) => s.setUser);

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password.trim()) return;
    setError('');
    setLoading(true);
    try {
      const res = await api.login(username.trim(), password);
      if (res.success && res.user) {
        setUser(res.user);
        onNavigate('chat');
      } else {
        setError(res.message || 'Login failed');
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSocialLogin = (provider: string) => {
    useStore.getState().addToast(`Connecting with ${provider}...`, 'info');
  };

  const inputStyle = {
    background: tk.elevated,
    border: `1px solid ${tk.border}`,
    color: tk.textPrimary,
    borderRadius: 8,
    padding: '12px 16px',
    fontSize: 14,
    fontWeight: 400 as const,
    outline: 'none',
    width: '100%',
    fontFamily: "'Inter', sans-serif",
    transition: 'border-color 150ms ease',
  };

  return (
    <div
      className="min-h-screen w-full flex items-center justify-center overflow-x-hidden"
      style={{
        background: tk.bg,
        fontFamily: "'Inter', 'Geist', system-ui, sans-serif",
      }}
    >
      {/* Subtle background glow */}
      <div
        className="fixed pointer-events-none"
        style={{
          width: 500,
          height: 500,
          top: '20%',
          left: '50%',
          transform: 'translateX(-50%)',
          background: `radial-gradient(ellipse at center, ${tk.accent1}10, ${tk.accent2}08, transparent 70%)`,
          filter: 'blur(80px)',
        }}
      />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' as const }}
        className="relative z-10 w-full flex flex-col gap-8"
        style={{
          maxWidth: 400,
          padding: '0 24px',
        }}
      >
        {/* Branding */}
        <div className="flex flex-col items-center gap-4">
          <div
            className="flex items-center gap-2.5 cursor-pointer"
            onClick={() => onNavigate('landing')}
          >
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round">
              <path d="M4 4c4 4 6 12 8 16" stroke={tk.accent1} />
              <path d="M20 4c-4 4-6 12-8 16" stroke={tk.accent2} />
              <path d="M12 4v16" stroke={tk.textPrimary} />
            </svg>
            <span style={{ fontSize: 20, fontWeight: 500, color: tk.textPrimary, letterSpacing: '-0.02em' }}>
              Distill
            </span>
          </div>
          <div className="text-center">
            <h1 style={{ fontSize: 24, fontWeight: 500, color: tk.textPrimary, margin: '0 0 6px', letterSpacing: '-0.02em' }}>
              Welcome back
            </h1>
            <p style={{ fontSize: 14, color: tk.textSecondary, margin: 0 }}>
              Sign in to your document workspace
            </p>
          </div>
        </div>

        {/* Card */}
        <div
          style={{
            background: tk.surface,
            border: `1px solid ${tk.border}`,
            borderRadius: 12,
            padding: '28px 24px',
          }}
        >
          {/* Social buttons */}
          <div className="grid grid-cols-2 gap-3" style={{ marginBottom: 24 }}>
            <button
              type="button"
              onClick={() => handleSocialLogin('Google')}
              className="flex items-center justify-center gap-2 cursor-pointer transition-all duration-150"
              style={{
                ...inputStyle,
                padding: '10px 16px',
                fontSize: 13,
                fontWeight: 500,
                textAlign: 'center' as const,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = tk.border)}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" fill="#EA4335"/>
              </svg>
              Google
            </button>
            <button
              type="button"
              onClick={() => handleSocialLogin('GitHub')}
              className="flex items-center justify-center gap-2 cursor-pointer transition-all duration-150"
              style={{
                ...inputStyle,
                padding: '10px 16px',
                fontSize: 13,
                fontWeight: 500,
                textAlign: 'center' as const,
              }}
              onMouseEnter={(e) => (e.currentTarget.style.borderColor = 'rgba(255,255,255,0.15)')}
              onMouseLeave={(e) => (e.currentTarget.style.borderColor = tk.border)}
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill={tk.textPrimary}>
                <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.17 6.839 9.49.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.464-1.11-1.464-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.579.688.481C19.137 20.167 22 16.418 22 12c0-5.523-4.477-10-10-10z"/>
              </svg>
              GitHub
            </button>
          </div>

          {/* Divider */}
          <div className="flex items-center gap-3" style={{ marginBottom: 24 }}>
            <div className="flex-1" style={{ height: 1, background: tk.border }} />
            <span style={{ fontSize: 12, color: tk.textMuted, fontWeight: 400 }}>or</span>
            <div className="flex-1" style={{ height: 1, background: tk.border }} />
          </div>

          {/* Error */}
          {error && (
            <div
              style={{
                background: `${tk.error}12`,
                border: `1px solid ${tk.error}25`,
                color: tk.error,
                fontSize: 13,
                padding: '10px 14px',
                borderRadius: 8,
                marginBottom: 16,
              }}
            >
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {/* Username */}
            <div className="flex flex-col gap-1.5">
              <label style={{ fontSize: 13, fontWeight: 500, color: tk.textSecondary }}>
                Username
              </label>
              <input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                style={inputStyle}
                autoFocus
                onFocus={(e) => (e.currentTarget.style.borderColor = `${tk.accent1}50`)}
                onBlur={(e) => (e.currentTarget.style.borderColor = tk.border)}
              />
            </div>

            {/* Password */}
            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label style={{ fontSize: 13, fontWeight: 500, color: tk.textSecondary }}>
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => useStore.getState().addToast('Reset link sent to registered email.', 'success')}
                  className="bg-transparent border-0 cursor-pointer"
                  style={{ fontSize: 12, color: tk.accent2, fontWeight: 500 }}
                >
                  Forgot password?
                </button>
              </div>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter password"
                  style={{ ...inputStyle, paddingRight: 44 }}
                  onFocus={(e) => (e.currentTarget.style.borderColor = `${tk.accent1}50`)}
                  onBlur={(e) => (e.currentTarget.style.borderColor = tk.border)}
                />
                <button
                  type="button"
                  onClick={() => setShowPw(!showPw)}
                  className="absolute bg-transparent border-0 cursor-pointer"
                  style={{ right: 14, top: '50%', transform: 'translateY(-50%)', color: tk.textMuted }}
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <motion.button
              type="submit"
              disabled={loading || !username.trim() || !password.trim()}
              whileHover={{ scale: 1.02, boxShadow: `0 0 24px ${tk.accent1}30` }}
              whileTap={{ scale: 0.98 }}
              className="flex items-center justify-center gap-2 border-0 cursor-pointer disabled:opacity-50"
              style={{
                background: tk.gradient,
                color: '#fff',
                fontSize: 14,
                fontWeight: 500,
                padding: '12px 24px',
                borderRadius: 8,
                marginTop: 8,
                width: '100%',
                transition: 'box-shadow 150ms ease',
              }}
            >
              <LogIn size={16} />
              {loading ? 'Signing in…' : 'Sign in'}
            </motion.button>
          </form>
        </div>

        {/* Footer links */}
        <div className="flex flex-col items-center gap-3">
          <button
            onClick={() => onNavigate('register')}
            className="bg-transparent border-0 cursor-pointer"
            style={{ fontSize: 14, color: tk.textSecondary, fontWeight: 400 }}
            onMouseEnter={(e) => (e.currentTarget.style.color = tk.accent2)}
            onMouseLeave={(e) => (e.currentTarget.style.color = tk.textSecondary)}
          >
            Don&apos;t have an account? <span style={{ color: tk.accent2, fontWeight: 500 }}>Sign up</span>
          </button>
          <button
            onClick={() => onNavigate('landing')}
            className="flex items-center gap-1.5 bg-transparent border-0 cursor-pointer"
            style={{ fontSize: 13, color: tk.textMuted }}
            onMouseEnter={(e) => (e.currentTarget.style.color = tk.textSecondary)}
            onMouseLeave={(e) => (e.currentTarget.style.color = tk.textMuted)}
          >
            <ArrowLeft size={14} />
            Back to home
          </button>
        </div>
      </motion.div>
    </div>
  );
}
