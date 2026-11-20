import React, { createContext, useContext, useEffect, useState } from 'react';
import {
  THEME_PALETTES,
  DEFAULT_THEME_ID,
  DEFAULT_RATIO,
  ThemePalette,
  ColorRatio,
  hexToRgb,
  getContrastColor,
  getLuminance
} from './palettes';

interface ThemeContextType {
  palette: ThemePalette;
  themeId: string;
  colorRatio: ColorRatio;
  setTheme: (id: string) => void;
  setColorRatio: (ratio: ColorRatio) => void;
  resetToDefault: () => void;
  isCustomRatio: boolean;
  contrastText: {
    onPrimary: string;
    onSecondary: string;
    onAccent: string;
  };
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const STORAGE_THEME_KEY = 'bhashashield_theme_id';
const STORAGE_RATIO_KEY = 'bhashashield_color_ratio';

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [themeId, setThemeId] = useState<string>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_THEME_KEY);
      if (saved && THEME_PALETTES[saved]) return saved;
    } catch {
      // Fallback if localStorage is inaccessible
    }
    return DEFAULT_THEME_ID;
  });

  const [colorRatio, setColorRatioState] = useState<ColorRatio>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_RATIO_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (
          typeof parsed.primary === 'number' &&
          typeof parsed.secondary === 'number' &&
          typeof parsed.accent === 'number' &&
          parsed.primary + parsed.secondary + parsed.accent === 100
        ) {
          return parsed;
        }
      }
    } catch {
      // Fallback
    }
    return DEFAULT_RATIO;
  });

  const palette = THEME_PALETTES[themeId] || THEME_PALETTES[DEFAULT_THEME_ID];

  const setTheme = (id: string) => {
    if (THEME_PALETTES[id]) {
      setThemeId(id);
      try {
        localStorage.setItem(STORAGE_THEME_KEY, id);
      } catch {
        // Ignored
      }
    }
  };

  const setColorRatio = (ratio: ColorRatio) => {
    // Ensure total is 100
    const sum = ratio.primary + ratio.secondary + ratio.accent;
    if (sum === 100) {
      setColorRatioState(ratio);
      try {
        localStorage.setItem(STORAGE_RATIO_KEY, JSON.stringify(ratio));
      } catch {
        // Ignored
      }
    }
  };

  const resetToDefault = () => {
    setColorRatioState(DEFAULT_RATIO);
    try {
      localStorage.setItem(STORAGE_RATIO_KEY, JSON.stringify(DEFAULT_RATIO));
    } catch {
      // Ignored
    }
  };

  const isCustomRatio =
    colorRatio.primary !== DEFAULT_RATIO.primary ||
    colorRatio.secondary !== DEFAULT_RATIO.secondary ||
    colorRatio.accent !== DEFAULT_RATIO.accent;

  const contrastText = {
    onPrimary: getContrastColor(palette.primary.hex),
    onSecondary: getContrastColor(palette.secondary.hex),
    onAccent: getContrastColor(palette.accent.hex)
  };

  // Sync to root CSS variables with smooth transitions
  useEffect(() => {
    const root = document.documentElement;
    const pRgb = hexToRgb(palette.primary.hex);
    const sRgb = hexToRgb(palette.secondary.hex);
    const aRgb = hexToRgb(palette.accent.hex);

    // Apply color values
    root.style.setProperty('--theme-primary', palette.primary.hex);
    root.style.setProperty('--theme-primary-rgb', `${pRgb.r}, ${pRgb.g}, ${pRgb.b}`);

    root.style.setProperty('--theme-secondary', palette.secondary.hex);
    root.style.setProperty('--theme-secondary-rgb', `${sRgb.r}, ${sRgb.g}, ${sRgb.b}`);

    root.style.setProperty('--theme-accent', palette.accent.hex);
    root.style.setProperty('--theme-accent-rgb', `${aRgb.r}, ${aRgb.g}, ${aRgb.b}`);

    // Proportions
    root.style.setProperty('--theme-ratio-primary', `${colorRatio.primary}`);
    root.style.setProperty('--theme-ratio-secondary', `${colorRatio.secondary}`);
    root.style.setProperty('--theme-ratio-accent', `${colorRatio.accent}`);

    // Contrast text
    root.style.setProperty('--theme-text-on-primary', contrastText.onPrimary);
    root.style.setProperty('--theme-text-on-secondary', contrastText.onSecondary);
    root.style.setProperty('--theme-text-on-accent', contrastText.onAccent);

    // Dynamic surfaces according to 60/30/10 ratio
    const secLum = getLuminance(palette.secondary.hex);
    const isSecondaryLight = secLum > 0.5;

    // Surface alpha scales subtly with primary weight
    const surfaceAlpha = Math.min(0.92, Math.max(0.70, colorRatio.primary / 100 * 1.15));
    root.style.setProperty('--theme-surface-alpha', `${surfaceAlpha}`);

    // Derived surface & card styles
    if (isSecondaryLight) {
      // If secondary is warm cream/ivory (Themes 01, 02, 03, 04)
      root.style.setProperty('--theme-surface-glass', `rgba(${pRgb.r}, ${pRgb.g}, ${pRgb.b}, ${surfaceAlpha})`);
      root.style.setProperty('--theme-card-bg', `rgba(${pRgb.r + 8}, ${pRgb.g + 10}, ${pRgb.b + 16}, 0.82)`);
      root.style.setProperty('--theme-border-subtle', `rgba(${sRgb.r}, ${sRgb.g}, ${sRgb.b}, 0.14)`);
      root.style.setProperty('--theme-border-accent', `rgba(${aRgb.r}, ${aRgb.g}, ${aRgb.b}, 0.38)`);
      root.style.setProperty('--theme-text-muted', `rgba(${sRgb.r}, ${sRgb.g}, ${sRgb.b}, 0.65)`);
      root.style.setProperty('--theme-text-heading', `rgba(255, 255, 255, 0.98)`);
    } else {
      // Dark steel / original cyber
      root.style.setProperty('--theme-surface-glass', `rgba(${sRgb.r}, ${sRgb.g}, ${sRgb.b}, 0.80)`);
      root.style.setProperty('--theme-card-bg', `rgba(${sRgb.r + 6}, ${sRgb.g + 8}, ${sRgb.b + 12}, 0.75)`);
      root.style.setProperty('--theme-border-subtle', `rgba(${aRgb.r}, ${aRgb.g}, ${aRgb.b}, 0.15)`);
      root.style.setProperty('--theme-border-accent', `rgba(${aRgb.r}, ${aRgb.g}, ${aRgb.b}, 0.40)`);
      root.style.setProperty('--theme-text-muted', '#8B9BB4');
      root.style.setProperty('--theme-text-heading', '#FFFFFF');
    }

    // Dynamic glow influenced by accent ratio (10% standard, scales up with higher ratio)
    const glowIntensity = (colorRatio.accent / 10) * 0.35;
    root.style.setProperty('--theme-glow-shadow', `0 0 35px rgba(${aRgb.r}, ${aRgb.g}, ${aRgb.b}, ${glowIntensity})`);
    root.style.setProperty('--theme-glow-intense', `0 0 50px rgba(${aRgb.r}, ${aRgb.g}, ${aRgb.b}, ${glowIntensity * 1.5})`);

    // Document body background
    document.body.style.backgroundColor = palette.primary.hex;
  }, [palette, colorRatio]);

  return (
    <ThemeContext.Provider
      value={{
        palette,
        themeId,
        colorRatio,
        setTheme,
        setColorRatio,
        resetToDefault,
        isCustomRatio,
        contrastText
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextType => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
