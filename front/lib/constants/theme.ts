export const NEO_BRUTALISM_THEME = {
  colors: {
    bg: '#FFFEF0',
    fg: '#1a1a1a',
    primary: '#FF6B35',
    secondary: '#4ECDC4',
    accent: '#FFE66D',
    danger: '#FF4444',
  },
  
  borders: {
    default: '3px solid #1a1a1a',
    thick: '4px solid #1a1a1a',
    radius: {
      none: '0px',
      sm: '2px',
      md: '4px',
    }
  },
  
  shadows: {
    default: '4px 4px 0px #1a1a1a',
    hover: '6px 6px 0px #1a1a1a',
    active: '2px 2px 0px #1a1a1a',
    none: '0px 0px 0px transparent',
  },
  
  typography: {
    fontFamily: {
      sans: 'Inter, sans-serif',
    },
    fontWeight: {
      normal: 400,
      bold: 700,
      black: 900,
    },
    scale: {
      h1: 'text-4xl font-black uppercase tracking-tight',
      h2: 'text-3xl font-black uppercase tracking-tight',
      h3: 'text-2xl font-bold uppercase',
      body: 'text-base font-normal',
      caption: 'text-sm font-bold uppercase',
    }
  }
} as const;

export type NeoBrutalismTheme = typeof NEO_BRUTALISM_THEME;
