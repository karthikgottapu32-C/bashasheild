import React from 'react';
import { useTheme } from './useTheme';
import { RATIO_PRESETS, DEFAULT_RATIO, ColorRatio } from './palettes';
import { RotateCcw, Sliders, Info, Check } from 'lucide-react';

export const ColorRatioControl: React.FC = () => {
  const { palette, colorRatio, setColorRatio, resetToDefault, isCustomRatio } = useTheme();

  // Handler to adjust one slider while re-balancing the others to strictly maintain 100%
  const handlePrimaryChange = (val: number) => {
    val = Math.max(40, Math.min(80, val)); // primary between 40 and 80
    const remainder = 100 - val;
    // Keep secondary/accent proportion
    const currentSecProp = colorRatio.secondary / (colorRatio.secondary + colorRatio.accent || 1);
    let newSec = Math.round(remainder * currentSecProp);
    let newAcc = remainder - newSec;
    if (newAcc < 5) {
      newAcc = 5;
      newSec = remainder - 5;
    }
    if (newSec < 10) {
      newSec = 10;
      newAcc = remainder - 10;
    }
    setColorRatio({ primary: val, secondary: newSec, accent: newAcc });
  };

  const handleSecondaryChange = (val: number) => {
    val = Math.max(10, Math.min(50, val));
    const remainder = 100 - val;
    let newPri = Math.round(remainder * 0.85);
    let newAcc = remainder - newPri;
    if (newAcc < 5) {
      newAcc = 5;
      newPri = remainder - 5;
    }
    if (newPri < 40) {
      newPri = 40;
      newAcc = remainder - 40;
    }
    setColorRatio({ primary: newPri, secondary: val, accent: newAcc });
  };

  const handleAccentChange = (val: number) => {
    val = Math.max(5, Math.min(25, val));
    const remainder = 100 - val;
    const currentPriProp = colorRatio.primary / (colorRatio.primary + colorRatio.secondary || 1);
    let newPri = Math.round(remainder * currentPriProp);
    let newSec = remainder - newPri;
    if (newSec < 10) {
      newSec = 10;
      newPri = remainder - 10;
    }
    if (newPri < 40) {
      newPri = 40;
      newSec = remainder - 40;
    }
    setColorRatio({ primary: newPri, secondary: newSec, accent: val });
  };

  return (
    <div className="space-y-5">
      {/* Header and Reset */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-[var(--theme-accent)]" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-white/90">
            60 / 30 / 10 DISTRIBUTION SYSTEM
          </span>
        </div>
        {isCustomRatio && (
          <button
            onClick={resetToDefault}
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-mono text-[var(--theme-accent)] hover:bg-[var(--theme-accent)]/10 border border-[var(--theme-accent)]/30 transition-all"
            title="Reset to 60/30/10 standard"
          >
            <RotateCcw className="w-3 h-3" />
            <span>Reset 60/30/10</span>
          </button>
        )}
      </div>

      {/* Visual Dynamic Ratio Bar */}
      <div className="space-y-1.5">
        <div className="h-4 rounded-full overflow-hidden flex shadow-inner border border-white/10 p-0.5 bg-black/40">
          {/* Primary Segment */}
          <div
            style={{
              width: `${colorRatio.primary}%`,
              backgroundColor: palette.primary.hex
            }}
            className="h-full rounded-l-full transition-all duration-300 relative group cursor-pointer"
            title={`Primary: ${colorRatio.primary}%`}
          />
          {/* Secondary Segment */}
          <div
            style={{
              width: `${colorRatio.secondary}%`,
              backgroundColor: palette.secondary.hex
            }}
            className="h-full transition-all duration-300 relative group cursor-pointer"
            title={`Secondary: ${colorRatio.secondary}%`}
          />
          {/* Accent Segment */}
          <div
            style={{
              width: `${colorRatio.accent}%`,
              backgroundColor: palette.accent.hex
            }}
            className="h-full rounded-r-full transition-all duration-300 relative group cursor-pointer shadow-[0_0_12px_rgba(var(--theme-accent-rgb),0.8)]"
            title={`Accent: ${colorRatio.accent}%`}
          />
        </div>

        {/* Proportions Indicator */}
        <div className="flex justify-between items-center text-[11px] font-mono pt-1 text-white/70">
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block border border-white/20"
              style={{ backgroundColor: palette.primary.hex }}
            />
            <span>Primary Foundation: <strong className="text-white">{colorRatio.primary}%</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block border border-white/20"
              style={{ backgroundColor: palette.secondary.hex }}
            />
            <span>Surfaces: <strong className="text-white">{colorRatio.secondary}%</strong></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block border border-white/20 shadow-[0_0_6px_var(--theme-accent)]"
              style={{ backgroundColor: palette.accent.hex }}
            />
            <span>Accent Energy: <strong className="text-[var(--theme-accent)]">{colorRatio.accent}%</strong></span>
          </div>
        </div>
      </div>

      {/* Preset Buttons */}
      <div className="space-y-2">
        <label className="text-[11px] font-mono text-white/50 uppercase tracking-wider block">
          Curated Proportions:
        </label>
        <div className="grid grid-cols-2 gap-2">
          {RATIO_PRESETS.map((preset) => {
            const isSelected =
              colorRatio.primary === preset.ratio.primary &&
              colorRatio.secondary === preset.ratio.secondary &&
              colorRatio.accent === preset.ratio.accent;
            return (
              <button
                key={preset.label}
                onClick={() => setColorRatio(preset.ratio)}
                className={`px-3 py-2 rounded-lg text-left transition-all border ${
                  isSelected
                    ? 'bg-white/10 border-[var(--theme-accent)] shadow-[0_0_15px_rgba(var(--theme-accent-rgb),0.2)]'
                    : 'bg-white/5 border-white/10 hover:border-white/20 hover:bg-white/8 text-white/70'
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white flex items-center gap-1.5">
                    {preset.label}
                    {isSelected && <Check className="w-3.5 h-3.5 text-[var(--theme-accent)]" />}
                  </span>
                  <span className="text-[10px] font-mono text-white/50">{preset.name}</span>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Detailed Fine-Tuning Sliders */}
      <div className="space-y-3 pt-2 border-t border-white/10">
        <div className="flex items-center justify-between text-xs font-mono">
          <span className="text-white/70 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: palette.primary.hex }} />
            Primary (Foundation)
          </span>
          <span className="font-bold text-white">{colorRatio.primary}%</span>
        </div>
        <input
          type="range"
          min="40"
          max="80"
          value={colorRatio.primary}
          onChange={(e) => handlePrimaryChange(Number(e.target.value))}
          className="w-full accent-[var(--theme-accent)] h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
        />

        <div className="flex items-center justify-between text-xs font-mono pt-1">
          <span className="text-white/70 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full" style={{ backgroundColor: palette.secondary.hex }} />
            Secondary (Cards & Panels)
          </span>
          <span className="font-bold text-white">{colorRatio.secondary}%</span>
        </div>
        <input
          type="range"
          min="10"
          max="50"
          value={colorRatio.secondary}
          onChange={(e) => handleSecondaryChange(Number(e.target.value))}
          className="w-full accent-[var(--theme-accent)] h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
        />

        <div className="flex items-center justify-between text-xs font-mono pt-1">
          <span className="text-white/70 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full shadow-[0_0_5px_var(--theme-accent)]" style={{ backgroundColor: palette.accent.hex }} />
            Accent (Focal Highlights)
          </span>
          <span className="font-bold text-[var(--theme-accent)]">{colorRatio.accent}%</span>
        </div>
        <input
          type="range"
          min="5"
          max="25"
          value={colorRatio.accent}
          onChange={(e) => handleAccentChange(Number(e.target.value))}
          className="w-full accent-[var(--theme-accent)] h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer"
        />
      </div>

      {/* Design Rule Explanation */}
      <div className="p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5 text-xs text-white/60">
        <Info className="w-4 h-4 text-[var(--theme-accent)] shrink-0 mt-0.5" />
        <p className="leading-relaxed">
          The <strong>60-30-10 Rule</strong> balances human visual perception: <strong>60%</strong> primary deep background, <strong>30%</strong> secondary structural cards, and <strong>10%</strong> high-energy accent for CTAs, 3D shield lighting, and critical indicators.
        </p>
      </div>
    </div>
  );
};
