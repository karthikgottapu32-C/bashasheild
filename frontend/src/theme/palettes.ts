export interface ColorSwatch {
  name: string;
  hex: string;
  role: 'primary' | 'secondary' | 'accent';
  ratioDefault: number; // e.g. 60, 30, 10
}

export interface ThemePalette {
  id: string;
  name: string;
  number: string;
  personality: string;
  primary: ColorSwatch;
  secondary: ColorSwatch;
  accent: ColorSwatch;
  supporting?: {
    blue?: string;
    emerald?: string;
    amber?: string;
    coral?: string;
  };
  // Surface and text tokens customized for contrast
  isDarkTheme: boolean;
  surfaceBgAlpha: number;
}

export interface ColorRatio {
  primary: number;
  secondary: number;
  accent: number;
}

export const THEME_PALETTES: Record<string, ThemePalette> = {
  'midnight-lime': {
    id: 'midnight-lime',
    number: '01',
    name: 'MIDNIGHT LIME',
    personality: 'Modern, energetic, premium and futuristic.',
    primary: {
      name: 'Midnight Navy',
      hex: '#101C35',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Warm Cream',
      hex: '#F3F0E7',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Lime',
      hex: '#B7F34A',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#3874CB',
      emerald: '#2BBF76',
      amber: '#F5A623',
      coral: '#FF5A5F'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.88
  },

  'navy-coral': {
    id: 'navy-coral',
    number: '02',
    name: 'NAVY CORAL',
    personality: 'Bold, confident, modern and visually striking.',
    primary: {
      name: 'Deep Navy',
      hex: '#101C35',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Warm Cream',
      hex: '#F3F0E7',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Vibrant Coral',
      hex: '#FF665C',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#4D82F3',
      emerald: '#10B981',
      amber: '#F59E0B',
      coral: '#FF665C'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.88
  },

  'forest-green': {
    id: 'forest-green',
    number: '03',
    name: 'FOREST GREEN',
    personality: 'Trustworthy, sophisticated and natural.',
    primary: {
      name: 'Deep Forest Green',
      hex: '#123B32',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Soft Ivory',
      hex: '#F0EFE5',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Fresh Green',
      hex: '#A6D96A',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#3B82F6',
      emerald: '#A6D96A',
      amber: '#EAB308',
      coral: '#EF4444'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.90
  },

  'electric-purple': {
    id: 'electric-purple',
    number: '04',
    name: 'ELECTRIC PURPLE',
    personality: 'Experimental, futuristic and creative.',
    primary: {
      name: 'Deep Midnight',
      hex: '#17142B',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Soft Lavender Cream',
      hex: '#F0EAF6',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Purple',
      hex: '#925BFF',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#6366F1',
      emerald: '#10B981',
      amber: '#F59E0B',
      coral: '#EC4899'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.88
  },

  'original-cyber': {
    id: 'original-cyber',
    number: '05',
    name: 'ORIGINAL CYBERSECURITY',
    personality: 'Professional, powerful, cinematic cybersecurity.',
    primary: {
      name: 'Deep Cyber Navy',
      hex: '#070B14',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Dark Steel Blue',
      hex: '#0B1220',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Cyan',
      hex: '#00E5FF',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#397BFF',
      emerald: '#00D68F',
      amber: '#FFB547',
      coral: '#FF4566'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.82
  },

  'obsidian-lime': {
    id: 'obsidian-lime',
    number: '06',
    name: 'OBSIDIAN LIME',
    personality: 'Stark, monolithic, razor-sharp and commanding.',
    primary: {
      name: 'Obsidian Black',
      hex: '#090B09',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Soft White',
      hex: '#F2F4EF',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Lime',
      hex: '#B7F34A',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#5AC8FA',
      emerald: '#32D74B',
      amber: '#FFD60A',
      coral: '#FF453A'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.90
  },

  'indigo-ice': {
    id: 'indigo-ice',
    number: '07',
    name: 'AI LAB — INDIGO ICE',
    personality: 'Deep research intelligence, clinical precision, and electric neural focus.',
    primary: {
      name: 'Deep Indigo Obsidian',
      hex: '#090D1C',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Crisp Ice White',
      hex: '#EAF4FF',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Cyan Glow',
      hex: '#36E4FF',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#5AC8FA',
      emerald: '#32D74B',
      amber: '#FFD60A',
      coral: '#FF453A'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.92
  },

  'titanium-intelligence': {
    id: 'titanium-intelligence',
    number: '08',
    name: 'TITANIUM INTELLIGENCE',
    personality: 'Deep graphite, titanium silver, and luminous polaris ion cyan. Ultra-clean defense aesthetic.',
    primary: {
      name: 'Monolithic Graphite',
      hex: '#0B0E14',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Titanium Silver',
      hex: '#E6EBF2',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Polaris Ion Cyan',
      hex: '#38BDF8',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#3B82F6',
      emerald: '#10B981',
      amber: '#F59E0B',
      coral: '#F43F5E'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.94
  },

  'quantum-atmosphere': {
    id: 'quantum-atmosphere',
    number: '09',
    name: 'QUANTUM ATMOSPHERE',
    personality: 'Midnight quantum void, pearl white, and electric ultraviolet lighting.',
    primary: {
      name: 'Quantum Midnight',
      hex: '#090A1A',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Pearl White',
      hex: '#F2F2FA',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Electric Ultraviolet',
      hex: '#A855F7',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#6366F1',
      emerald: '#10B981',
      amber: '#F59E0B',
      coral: '#EC4899'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.92
  },

  'arctic-neural': {
    id: 'arctic-neural',
    number: '10',
    name: 'ARCTIC NEURAL',
    personality: 'Abyssal stygian blue, frost white, and plasma turquoise with luminous neural detail.',
    primary: {
      name: 'Abyssal Stygian',
      hex: '#060A12',
      role: 'primary',
      ratioDefault: 60
    },
    secondary: {
      name: 'Frost Glacial White',
      hex: '#EEF6FC',
      role: 'secondary',
      ratioDefault: 30
    },
    accent: {
      name: 'Plasma Turquoise',
      hex: '#00F5D4',
      role: 'accent',
      ratioDefault: 10
    },
    supporting: {
      blue: '#0EA5E9',
      emerald: '#10B981',
      amber: '#FBBF24',
      coral: '#FB7185'
    },
    isDarkTheme: true,
    surfaceBgAlpha: 0.92
  }
};

export const DEFAULT_THEME_ID = 'titanium-intelligence';
export const DEFAULT_RATIO: ColorRatio = { primary: 60, secondary: 30, accent: 10 };

export const RATIO_PRESETS: { name: string; label: string; ratio: ColorRatio }[] = [
  { name: 'Classic Golden', label: '60 / 30 / 10', ratio: { primary: 60, secondary: 30, accent: 10 } },
  { name: 'High Contrast', label: '50 / 35 / 15', ratio: { primary: 50, secondary: 35, accent: 15 } },
  { name: 'Deep Minimal', label: '70 / 20 / 10', ratio: { primary: 70, secondary: 20, accent: 10 } },
  { name: 'Vibrant Dynamic', label: '55 / 30 / 15', ratio: { primary: 55, secondary: 30, accent: 15 } },
];

/**
 * Utility: Convert HEX to RGB numbers
 */
export function hexToRgb(hex: string): { r: number; g: number; b: number } {
  let cleanHex = hex.replace('#', '');
  if (cleanHex.length === 3) {
    cleanHex = cleanHex.split('').map(c => c + c).join('');
  }
  const num = parseInt(cleanHex, 16);
  return {
    r: (num >> 16) & 255,
    g: (num >> 8) & 255,
    b: num & 255
  };
}

/**
 * Utility: Calculate Relative Luminance (WCAG 2.1)
 */
export function getLuminance(hex: string): number {
  const { r, g, b } = hexToRgb(hex);
  const a = [r, g, b].map(v => {
    v /= 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722;
}

/**
 * Utility: Get contrasting text color (pure dark or pure light)
 */
export function getContrastColor(hex: string): string {
  const lum = getLuminance(hex);
  return lum > 0.45 ? '#0A0F1D' : '#F5F7FA';
}
