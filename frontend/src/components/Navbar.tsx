import React, { useState } from 'react';
import { ShieldAlert, Menu, X, ArrowRight, Activity, Terminal, LayoutDashboard, Award, Sparkles } from 'lucide-react';
import { ColorPaletteSelector } from '../theme/ColorPaletteSelector';

interface NavbarProps {
  currentView: 'landing' | 'textguard' | 'dashboard' | 'evaluation';
  onNavigate: (view: 'landing' | 'textguard' | 'dashboard' | 'evaluation') => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNav = (view: 'landing' | 'textguard' | 'dashboard' | 'evaluation') => {
    onNavigate(view);
    setMobileMenuOpen(false);
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-40 glass-panel border-b border-white/10 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo */}
        <div
          onClick={() => handleNav('landing')}
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[var(--theme-accent)] to-[var(--theme-secondary)] flex items-center justify-center shadow-[var(--theme-glow-shadow)] group-hover:scale-105 transition-all duration-300">
            <ShieldAlert className="w-6 h-6 text-[#0A0F1D]" />
          </div>
          <div>
            <div className="text-lg font-black tracking-wider text-white flex items-center gap-1.5">
              <span>BHASHASHIELD</span>
              <span className="text-[9px] font-mono font-bold uppercase px-1.5 py-0.5 rounded bg-[var(--theme-accent)]/20 text-[var(--theme-accent)] border border-[var(--theme-accent)]/40 shadow-[0_0_8px_rgba(var(--theme-accent-rgb),0.3)]">
                AI GUARD
              </span>
            </div>
            <div className="text-[10px] text-white/50 font-mono tracking-tight">
              Multilingual Security Intelligence
            </div>
          </div>
        </div>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-white/70">
          <button
            data-nav-desktop="landing"
            onClick={() => handleNav('landing')}
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] relative py-1 ${
              currentView === 'landing' ? 'text-[var(--theme-accent)] font-bold' : ''
            }`}
          >
            <span>Overview</span>
            {currentView === 'landing' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] rounded-full shadow-[0_0_8px_var(--theme-accent)]" />
            )}
          </button>

          <button
            data-nav-desktop="textguard"
            onClick={() => handleNav('textguard')}
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 ${
              currentView === 'textguard' ? 'text-[var(--theme-accent)] font-bold' : ''
            }`}
          >
            <Terminal className="w-4 h-4" />
            <span>Text Guard</span>
            {currentView === 'textguard' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] rounded-full shadow-[0_0_8px_var(--theme-accent)]" />
            )}
          </button>

          <button
            data-nav-desktop="dashboard"
            onClick={() => handleNav('dashboard')}
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 ${
              currentView === 'dashboard' ? 'text-[var(--theme-accent)] font-bold' : ''
            }`}
          >
            <LayoutDashboard className="w-4 h-4" />
            <span>Intelligence Console</span>
            {currentView === 'dashboard' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] rounded-full shadow-[0_0_8px_var(--theme-accent)]" />
            )}
          </button>

          <button
            data-nav-desktop="evaluation"
            onClick={() => handleNav('evaluation')}
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 ${
              currentView === 'evaluation' ? 'text-[var(--theme-accent)] font-bold' : ''
            }`}
          >
            <Award className="w-4 h-4" />
            <span>Evaluation</span>
            {currentView === 'evaluation' && (
              <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-[var(--theme-accent)] rounded-full shadow-[0_0_8px_var(--theme-accent)]" />
            )}
          </button>
        </nav>

        {/* Right Section: Color Grading Studio Trigger + CTA Button */}
        <div className="hidden md:flex items-center gap-3.5">
          {/* Interactive 60/30/10 Theme Selector */}
          <ColorPaletteSelector />

          {/* Direct Launch CTA */}
          <button
            onClick={() => handleNav('textguard')}
            className="theme-button-primary px-4 py-2 rounded-xl text-xs font-black tracking-wider uppercase flex items-center gap-1.5"
          >
            <span>Scan Text</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Mobile menu hamburger */}
        <div className="flex md:hidden items-center gap-2">
          <ColorPaletteSelector />
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="text-white/70 hover:text-white p-2"
            aria-label="Toggle Navigation Menu"
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <div className="md:hidden glass-panel border-b border-white/10 p-5 space-y-3 animate-fadeIn">
          <button
            data-nav-mobile="landing"
            onClick={() => handleNav('landing')}
            className="w-full text-left py-2.5 px-3 rounded-lg text-sm font-semibold text-white/90 hover:bg-white/5 hover:text-[var(--theme-accent)] flex items-center justify-between"
          >
            <span>Platform Overview</span>
          </button>
          <button
            data-nav-mobile="textguard"
            onClick={() => handleNav('textguard')}
            className="w-full text-left py-2.5 px-3 rounded-lg text-sm font-semibold text-white/90 hover:bg-white/5 hover:text-[var(--theme-accent)] flex items-center gap-2"
          >
            <Terminal className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Text Guard Workstation</span>
          </button>
          <button
            data-nav-mobile="dashboard"
            onClick={() => handleNav('dashboard')}
            className="w-full text-left py-2.5 px-3 rounded-lg text-sm font-semibold text-white/90 hover:bg-white/5 hover:text-[var(--theme-accent)] flex items-center gap-2"
          >
            <LayoutDashboard className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Intelligence Console</span>
          </button>
          <button
            data-nav-mobile="evaluation"
            onClick={() => handleNav('evaluation')}
            className="w-full text-left py-2.5 px-3 rounded-lg text-sm font-semibold text-white/90 hover:bg-white/5 hover:text-[var(--theme-accent)] flex items-center gap-2"
          >
            <Award className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Evaluation & Held-Out Metrics</span>
          </button>
          <div className="pt-2">
            <button
              onClick={() => handleNav('textguard')}
              className="w-full theme-button-primary py-3 rounded-xl text-xs uppercase tracking-wider text-center"
            >
              Launch Text Guard
            </button>
          </div>
        </div>
      )}
    </header>
  );
};
