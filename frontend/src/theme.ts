export type Theme = 'dark' | 'light';

export const darkTheme = {
  bg: '#0B0E14',
  surface: '#12161F',
  elevated: '#1A1F2C',
  accentSignal: '#4FF2C4', // signal accent
  accentAgent: '#7C7FFF',  // agent accent
  textPrimary: '#E8EAF0',  // text
  textMuted: '#8B93A7',    // muted text
  border: '#232838',       // border
  error: '#FF6B6B',
  warning: '#FBBF24',
  success: '#4FF2C4',
};

export const lightTheme = {
  bg: '#F7F8FA',
  surface: '#FFFFFF',
  elevated: '#EEF0F4',
  accentSignal: '#0FAE86', // signal accent
  accentAgent: '#5B5FEF',  // agent accent
  textPrimary: '#14171F',  // text
  textMuted: '#5B6472',    // muted text
  border: '#E1E4EA',       // border
  error: '#E11D48',
  warning: '#D97706',
  success: '#0FAE86',
};

export const themes = { dark: darkTheme, light: lightTheme };
