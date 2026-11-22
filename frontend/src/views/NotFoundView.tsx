import React from 'react';
import { motion } from 'framer-motion';
import { ShieldAlert, ArrowLeft, Terminal, LayoutDashboard, Home, AlertOctagon } from 'lucide-react';

interface NotFoundViewProps {
  onNavigateToLanding: () => void;
  onNavigateToTextGuard: () => void;
  onNavigateToDashboard: () => void;
}

export const NotFoundView: React.FC<NotFoundViewProps> = ({
  onNavigateToLanding,
  onNavigateToTextGuard,
  onNavigateToDashboard,
}) => {
  return (
    <div className="min-h-screen pt-28 pb-20 px-4 sm:px-6 lg:px-8 max-w-4xl mx-auto flex flex-col items-center justify-center text-center">
      {/* 404 Shield Beacon */}
      <motion.div
        initial={{ scale: 0.8, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
        className="w-24 h-24 rounded-3xl bg-[var(--theme-accent)]/15 border border-[var(--theme-accent)]/40 flex items-center justify-center shadow-[var(--theme-glow-shadow)] mb-6"
      >
        <AlertOctagon className="w-12 h-12 text-[var(--theme-accent)]" />
      </motion.div>

      {/* Code Badge */}
      <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-mono font-bold tracking-wider uppercase bg-[var(--theme-accent)]/10 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 mb-4">
        <span>HTTP 404 • UNRESOLVED TELEMETRY NODE</span>
      </div>

      <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white mb-4">
        Security Vector Not Found
      </h1>

      <p className="text-white/60 text-base sm:text-lg max-w-xl mx-auto mb-8 font-sans">
        The route, diagnostic endpoint, or telemetry node you navigated to does not exist within BhashaShield's active defense network.
      </p>

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-center gap-4">
        <button
          onClick={onNavigateToLanding}
          className="theme-button-primary px-6 py-3 rounded-xl text-sm font-bold tracking-wide flex items-center gap-2"
          aria-label="Return to platform overview"
        >
          <Home className="w-4 h-4" />
          <span>Return to Overview</span>
        </button>

        <button
          onClick={onNavigateToTextGuard}
          className="theme-button-secondary px-6 py-3 rounded-xl text-sm font-bold tracking-wide flex items-center gap-2"
          aria-label="Launch text guard scanner"
        >
          <Terminal className="w-4 h-4" />
          <span>Launch Text Guard</span>
        </button>

        <button
          onClick={onNavigateToDashboard}
          className="px-6 py-3 rounded-xl border border-white/20 text-white/80 hover:text-white hover:bg-white/10 text-sm font-bold tracking-wide transition-all flex items-center gap-2"
          aria-label="Open intelligence console"
        >
          <LayoutDashboard className="w-4 h-4" />
          <span>Intelligence Console</span>
        </button>
      </div>

      {/* Diagnostic Details */}
      <div className="mt-12 p-4 rounded-xl glass-panel border border-white/10 max-w-md w-full text-left font-mono text-xs text-white/50">
        <div className="flex items-center justify-between mb-2 pb-2 border-b border-white/10">
          <span className="text-white/70 font-bold">Vector Status</span>
          <span className="text-[var(--theme-accent)] font-bold">ROUTE_MISMATCH</span>
        </div>
        <div>Active Routes: #overview, #textguard, #dashboard, #evaluation</div>
        <div className="text-[10px] text-white/30 mt-1">BhashaShield Production Client Router</div>
      </div>
    </div>
  );
};
