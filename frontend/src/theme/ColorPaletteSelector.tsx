import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTheme } from './useTheme';
import { THEME_PALETTES } from './palettes';
import { ColorRatioControl } from './ColorRatioControl';
import { Palette, X, Sparkles, Check, SlidersHorizontal, Layers } from 'lucide-react';

export const ColorPaletteSelector: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'palettes' | 'proportions'>('palettes');
  const { themeId, setTheme, palette, colorRatio } = useTheme();

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  return (
    <>
      {/* Floating / Embedded Palette Selector Trigger */}
      <button
        onClick={() => setIsOpen(true)}
        className="group relative flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-black/40 hover:bg-black/60 border border-white/15 hover:border-[var(--theme-accent)] transition-all duration-300 shadow-[0_4px_20px_rgba(0,0,0,0.3)] hover:shadow-[0_0_20px_rgba(var(--theme-accent-rgb),0.35)]"
        aria-label="Open 60/30/10 Color Grading Studio"
        title="Open 60/30/10 Color Grading Studio"
      >
        {/* Animated Palette Icon */}
        <Palette className="w-3.5 h-3.5 text-[var(--theme-accent)] group-hover:rotate-12 transition-transform duration-300" />

        {/* 3 Active Theme Swatches */}
        <div className="flex items-center -space-x-1">
          <span
            className="w-3.5 h-3.5 rounded-full border border-black/40 shadow-sm"
            style={{ backgroundColor: palette.primary.hex }}
            title={`Primary (60%): ${palette.primary.name}`}
          />
          <span
            className="w-3.5 h-3.5 rounded-full border border-black/40 shadow-sm"
            style={{ backgroundColor: palette.secondary.hex }}
            title={`Secondary (30%): ${palette.secondary.name}`}
          />
          <span
            className="w-3.5 h-3.5 rounded-full border border-black/40 shadow-sm animate-pulse"
            style={{ backgroundColor: palette.accent.hex }}
            title={`Accent (10%): ${palette.accent.name}`}
          />
        </div>

        {/* Proportions Pill */}
        <span className="text-[11px] font-mono font-bold text-white/80 group-hover:text-white transition-colors">
          {colorRatio.primary}/{colorRatio.secondary}/{colorRatio.accent}
        </span>

        {/* Subtle Live Badge */}
        <span className="w-1.5 h-1.5 rounded-full bg-[var(--theme-accent)] shadow-[0_0_6px_var(--theme-accent)]" />
      </button>

      {/* Luxury Color Grading Studio Modal / Drawer */}
      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 md:p-8">
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/80 backdrop-blur-md"
            />

            {/* Modal Card */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
              className="relative w-full max-w-2xl max-h-[90vh] overflow-hidden rounded-2xl border border-white/20 bg-[var(--theme-primary)]/95 shadow-[0_20px_70px_rgba(0,0,0,0.8),0_0_40px_rgba(var(--theme-accent-rgb),0.15)] backdrop-blur-2xl flex flex-col z-10"
            >
              {/* Studio Header */}
              <div className="p-6 border-b border-white/10 flex items-center justify-between shrink-0 bg-black/20">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[var(--theme-accent)]/15 border border-[var(--theme-accent)]/40 flex items-center justify-center shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.3)]">
                    <Sparkles className="w-5 h-5 text-[var(--theme-accent)]" />
                  </div>
                  <div>
                    <h2 className="text-base sm:text-lg font-black tracking-wide text-white flex items-center gap-2">
                      <span>COLOR GRADING STUDIO</span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-[var(--theme-accent)]/20 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 uppercase">
                        60 / 30 / 10 Live
                      </span>
                    </h2>
                    <p className="text-xs text-white/60 font-mono">
                      Dynamic three-color harmony & proportional UI distribution
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setIsOpen(false)}
                  className="w-8 h-8 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 flex items-center justify-center text-white/70 hover:text-white transition-all"
                  aria-label="Close theme studio"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Navigation Tabs: Palettes vs Distribution */}
              <div className="px-6 pt-4 pb-2 border-b border-white/10 flex gap-4 shrink-0 bg-black/10">
                <button
                  onClick={() => setActiveTab('palettes')}
                  className={`pb-2.5 text-xs font-mono font-bold tracking-wider uppercase transition-all relative flex items-center gap-2 ${
                    activeTab === 'palettes' ? 'text-[var(--theme-accent)]' : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  <Layers className="w-3.5 h-3.5" />
                  <span>Curated Palettes (5)</span>
                  {activeTab === 'palettes' && (
                    <motion.div
                      layoutId="activeTabUnderline"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] shadow-[0_0_8px_var(--theme-accent)]"
                    />
                  )}
                </button>

                <button
                  onClick={() => setActiveTab('proportions')}
                  className={`pb-2.5 text-xs font-mono font-bold tracking-wider uppercase transition-all relative flex items-center gap-2 ${
                    activeTab === 'proportions' ? 'text-[var(--theme-accent)]' : 'text-white/50 hover:text-white/80'
                  }`}
                >
                  <SlidersHorizontal className="w-3.5 h-3.5" />
                  <span>60/30/10 Proportions Control</span>
                  {activeTab === 'proportions' && (
                    <motion.div
                      layoutId="activeTabUnderline"
                      className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] shadow-[0_0_8px_var(--theme-accent)]"
                    />
                  )}
                </button>
              </div>

              {/* Scrollable Content Area */}
              <div className="p-6 overflow-y-auto space-y-4 flex-1 custom-scrollbar">
                {activeTab === 'palettes' ? (
                  <div className="space-y-3.5">
                    {Object.values(THEME_PALETTES).map((p) => {
                      const isSelected = p.id === themeId;
                      return (
                        <div
                          key={p.id}
                          onClick={() => setTheme(p.id)}
                          className={`p-4 rounded-xl border transition-all duration-300 cursor-pointer relative overflow-hidden group ${
                            isSelected
                              ? 'bg-white/10 border-[var(--theme-accent)] shadow-[0_0_25px_rgba(var(--theme-accent-rgb),0.25)]'
                              : 'bg-black/30 border-white/10 hover:border-white/25 hover:bg-white/5'
                          }`}
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-3">
                            <div className="flex items-center gap-2.5">
                              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-white/10 text-white/60">
                                THEME {p.number}
                              </span>
                              <h3 className="text-sm font-bold tracking-wide text-white flex items-center gap-2">
                                {p.name}
                                {isSelected && (
                                  <span className="flex items-center gap-1 text-[10px] font-mono text-[var(--theme-accent)] font-bold">
                                    <Check className="w-3 h-3" /> ACTIVE
                                  </span>
                                )}
                              </h3>
                            </div>
                            <span className="text-[11px] text-white/50 italic font-mono sm:text-right">
                              {p.personality}
                            </span>
                          </div>

                          {/* 3 Adjacent Swatches with 60/30/10 Labels */}
                          <div className="grid grid-cols-3 gap-2 pt-1">
                            {/* Primary Swatch */}
                            <div className="rounded-lg p-2.5 border border-white/10 flex flex-col justify-between h-20 relative overflow-hidden"
                              style={{ backgroundColor: p.primary.hex }}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-[9px] font-mono uppercase px-1 rounded bg-black/60 text-white/90">
                                  Primary 60%
                                </span>
                              </div>
                              <div>
                                <div className="text-[11px] font-bold text-white truncate drop-shadow-sm">
                                  {p.primary.name}
                                </div>
                                <div className="text-[10px] font-mono text-white/80">
                                  {p.primary.hex}
                                </div>
                              </div>
                            </div>

                            {/* Secondary Swatch */}
                            <div className="rounded-lg p-2.5 border border-white/10 flex flex-col justify-between h-20 relative overflow-hidden"
                              style={{ backgroundColor: p.secondary.hex }}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-[9px] font-mono uppercase px-1 rounded bg-black/60 text-white/90">
                                  Secondary 30%
                                </span>
                              </div>
                              <div>
                                <div className="text-[11px] font-bold text-black truncate drop-shadow-sm">
                                  {p.secondary.name}
                                </div>
                                <div className="text-[10px] font-mono text-black/70">
                                  {p.secondary.hex}
                                </div>
                              </div>
                            </div>

                            {/* Accent Swatch */}
                            <div className="rounded-lg p-2.5 border border-white/10 flex flex-col justify-between h-20 relative overflow-hidden shadow-[0_0_15px_rgba(0,0,0,0.3)]"
                              style={{ backgroundColor: p.accent.hex }}
                            >
                              <div className="flex items-center justify-between">
                                <span className="text-[9px] font-mono uppercase px-1 rounded bg-black/70 text-white font-bold">
                                  Accent 10%
                                </span>
                              </div>
                              <div>
                                <div className="text-[11px] font-bold text-black truncate drop-shadow-sm">
                                  {p.accent.name}
                                </div>
                                <div className="text-[10px] font-mono text-black/80 font-bold">
                                  {p.accent.hex}
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <ColorRatioControl />
                )}
              </div>

              {/* Studio Footer */}
              <div className="p-4 border-t border-white/10 bg-black/30 flex items-center justify-between text-xs text-white/60 font-mono shrink-0">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-[var(--theme-accent)] animate-ping" />
                  <span>Real-time CSS variables active across entire application</span>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="px-4 py-1.5 rounded-lg bg-[var(--theme-accent)] text-black font-bold hover:brightness-110 active:scale-95 transition-all text-xs"
                >
                  Done
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
};
