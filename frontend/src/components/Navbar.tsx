import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Menu,
  X,
  ArrowRight,
  Terminal,
  LayoutDashboard,
  Award,
  Home,
  User,
  LogOut,
  Lock,
  Loader2
} from 'lucide-react';
import { ColorPaletteSelector } from '../theme/ColorPaletteSelector';
import { ViewRoute } from './CinematicFragmentationTransition';
import {
  getStoredUser,
  setStoredUser,
  getCurrentUser,
  loginUser,
  registerUser,
  logoutUser
} from '../services/api';
import { UserProfile } from '../types';

interface NavbarProps {
  currentView: ViewRoute;
  onNavigate: (view: ViewRoute) => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onNavigate }) => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Authentication State
  const [user, setUser] = useState<UserProfile | null>(() => getStoredUser());
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [authModalOpen, setAuthModalOpen] = useState(false);
  const [authMode, setAuthMode] = useState<'login' | 'register'>('login');
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authLoading, setAuthLoading] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  // Sync current user on mount if token exists
  useEffect(() => {
    getCurrentUser()
      .then((profile) => {
        setUser(profile);
        setStoredUser(profile);
      })
      .catch(() => {
        // If token expired or invalid, keep stored or reset
      });
  }, []);

  // Close menus/modals on Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (authModalOpen) setAuthModalOpen(false);
        if (userMenuOpen) setUserMenuOpen(false);
        if (mobileMenuOpen) setMobileMenuOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [authModalOpen, userMenuOpen, mobileMenuOpen]);

  const handleNav = (view: ViewRoute) => {
    onNavigate(view);
    setMobileMenuOpen(false);
  };

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);

    try {
      if (authMode === 'login') {
        const res = await loginUser(authUsername, authPassword);
        setUser(res.user);
      } else {
        const res = await registerUser(authUsername, authPassword);
        setUser(res.user);
      }
      setAuthModalOpen(false);
      setAuthUsername('');
      setAuthPassword('');
      // Dispatch custom event so dashboard/scans reload
      window.dispatchEvent(new CustomEvent('bhashashield:auth-change'));
    } catch (err: any) {
      setAuthError(err.message || 'Authentication failed. Please verify credentials.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    logoutUser();
    setUser(null);
    setUserMenuOpen(false);
    window.dispatchEvent(new CustomEvent('bhashashield:auth-change'));
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-40 glass-panel border-b border-white/10 transition-all duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between">
        {/* Brand Logo - Fully accessible and keyboard navigatable */}
        <button
          onClick={() => handleNav('landing')}
          className="flex items-center gap-3 cursor-pointer group select-none text-left focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] rounded-xl p-1 -ml-1 transition-all"
          aria-label="BhashaShield Home — Return to platform overview"
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
        </button>

        {/* Desktop Nav Items */}
        <nav className="hidden md:flex items-center gap-7 text-sm font-semibold text-white/70" aria-label="Desktop Navigation">
          <button
            data-nav-desktop="landing"
            onClick={() => handleNav('landing')}
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] relative py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] rounded ${
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
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] rounded ${
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
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] rounded ${
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
            className={`transition-all duration-200 hover:text-[var(--theme-accent)] flex items-center gap-1.5 relative py-1 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] rounded ${
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

        {/* Right Section: Auth Pill + Color Grading Studio Trigger + CTA Button */}
        <div className="hidden md:flex items-center gap-3">
          {/* User Auth Pill / Menu */}
          {user ? (
            <div className="relative">
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 hover:border-[var(--theme-accent)]/50 text-xs font-mono font-medium text-white transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)]"
                aria-expanded={userMenuOpen}
                aria-haspopup="true"
                aria-label={`User menu for ${user.username}`}
              >
                <div className="w-2 h-2 rounded-full bg-[var(--theme-accent)] animate-pulse" />
                <span className="font-bold text-[var(--theme-accent)]">{user.username}</span>
                <span className="text-[10px] text-white/50 uppercase">({user.role})</span>
              </button>

              {userMenuOpen && (
                <div className="absolute right-0 mt-2 w-52 glass-panel border border-white/15 rounded-xl p-3 shadow-2xl z-50 animate-fadeIn space-y-2">
                  <div className="text-[11px] font-mono text-white/60 pb-2 border-b border-white/10">
                    <div className="text-white font-bold truncate">{user.username}</div>
                    <div className="text-[9px] text-[var(--theme-accent)] uppercase">Role: {user.role}</div>
                    <div className="text-[9px] text-white/40 truncate">ID: {user.id.slice(0, 8)}...</div>
                  </div>
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-all text-left"
                  >
                    <LogOut className="w-3.5 h-3.5" />
                    <span>Sign Out</span>
                  </button>
                </div>
              )}
            </div>
          ) : (
            <button
              onClick={() => {
                setAuthModalOpen(true);
                setAuthMode('login');
                setAuthError(null);
              }}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white/5 border border-white/10 hover:border-[var(--theme-accent)]/50 text-xs font-semibold text-white/80 hover:text-white transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)]"
              aria-label="Sign In or Register"
            >
              <User className="w-3.5 h-3.5 text-[var(--theme-accent)]" />
              <span>Sign In</span>
            </button>
          )}

          {/* Interactive 60/30/10 Theme Selector */}
          <ColorPaletteSelector />

          {/* Direct Launch CTA */}
          <button
            onClick={() => handleNav('textguard')}
            className="theme-button-primary px-4 py-2 rounded-xl text-xs font-black tracking-wider uppercase flex items-center gap-1.5 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)]"
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
            className="text-white/70 hover:text-white p-2.5 rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)] min-w-[44px] min-h-[44px] flex items-center justify-center"
            aria-expanded={mobileMenuOpen}
            aria-controls="mobile-nav-menu"
            aria-label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
          >
            {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile Drawer */}
      {mobileMenuOpen && (
        <nav
          id="mobile-nav-menu"
          aria-label="Mobile Navigation"
          className="md:hidden glass-panel border-b border-white/10 p-5 space-y-2 animate-fadeIn"
        >
          <button
            data-nav-mobile="landing"
            onClick={() => handleNav('landing')}
            className={`w-full text-left py-3 px-3.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-3 min-h-[44px] ${
              currentView === 'landing'
                ? 'bg-[var(--theme-accent)]/15 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 font-bold'
                : 'text-white/80 hover:bg-white/5 hover:text-white'
            }`}
          >
            <Home className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Platform Overview</span>
          </button>

          <button
            data-nav-mobile="textguard"
            onClick={() => handleNav('textguard')}
            className={`w-full text-left py-3 px-3.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-3 min-h-[44px] ${
              currentView === 'textguard'
                ? 'bg-[var(--theme-accent)]/15 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 font-bold'
                : 'text-white/80 hover:bg-white/5 hover:text-white'
            }`}
          >
            <Terminal className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Text Guard Workstation</span>
          </button>

          <button
            data-nav-mobile="dashboard"
            onClick={() => handleNav('dashboard')}
            className={`w-full text-left py-3 px-3.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-3 min-h-[44px] ${
              currentView === 'dashboard'
                ? 'bg-[var(--theme-accent)]/15 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 font-bold'
                : 'text-white/80 hover:bg-white/5 hover:text-white'
            }`}
          >
            <LayoutDashboard className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Intelligence Console</span>
          </button>

          <button
            data-nav-mobile="evaluation"
            onClick={() => handleNav('evaluation')}
            className={`w-full text-left py-3 px-3.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-3 min-h-[44px] ${
              currentView === 'evaluation'
                ? 'bg-[var(--theme-accent)]/15 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30 font-bold'
                : 'text-white/80 hover:bg-white/5 hover:text-white'
            }`}
          >
            <Award className="w-4 h-4 text-[var(--theme-accent)]" />
            <span>Evaluation & Benchmark Metrics</span>
          </button>

          {/* Mobile Auth Button */}
          <div className="pt-2 border-t border-white/10">
            {user ? (
              <div className="p-3 rounded-xl bg-white/5 border border-white/10 space-y-2">
                <div className="flex items-center justify-between text-xs font-mono">
                  <span className="text-white font-bold">{user.username}</span>
                  <span className="text-[10px] text-[var(--theme-accent)] uppercase">{user.role}</span>
                </div>
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center justify-center gap-2 py-2 rounded-lg text-xs font-semibold text-red-400 bg-red-500/10 hover:bg-red-500/20 transition-all"
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign Out</span>
                </button>
              </div>
            ) : (
              <button
                onClick={() => {
                  setMobileMenuOpen(false);
                  setAuthModalOpen(true);
                  setAuthMode('login');
                  setAuthError(null);
                }}
                className="w-full py-2.5 rounded-xl bg-white/5 border border-white/10 hover:border-[var(--theme-accent)]/50 text-xs font-semibold text-white flex items-center justify-center gap-2"
              >
                <User className="w-3.5 h-3.5 text-[var(--theme-accent)]" />
                <span>Sign In / Register</span>
              </button>
            )}
          </div>

          <div className="pt-3 border-t border-white/10 mt-2">
            <button
              onClick={() => handleNav('textguard')}
              className="w-full theme-button-primary py-3 rounded-xl text-xs uppercase tracking-wider text-center min-h-[44px] flex items-center justify-center gap-2"
            >
              <span>Launch Text Guard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </nav>
      )}

      {/* Auth Modal */}
      {authModalOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="auth-modal-title"
          className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={(e) => {
            if (e.target === e.currentTarget) setAuthModalOpen(false);
          }}
        >
          <div className="glass-panel border border-white/20 rounded-2xl max-w-md w-full p-6 shadow-2xl relative animate-fadeIn text-white">
            <button
              onClick={() => setAuthModalOpen(false)}
              className="absolute top-4 right-4 p-1.5 text-white/50 hover:text-white rounded-lg hover:bg-white/10 transition-all focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--theme-accent)]"
              aria-label="Close authentication modal"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-5">
              <div className="w-9 h-9 rounded-xl bg-[var(--theme-accent)]/20 border border-[var(--theme-accent)]/40 flex items-center justify-center text-[var(--theme-accent)]">
                <Lock className="w-5 h-5" />
              </div>
              <div>
                <h3 id="auth-modal-title" className="text-base font-bold text-white">
                  {authMode === 'login' ? 'Sign In to BhashaShield' : 'Create BhashaShield Account'}
                </h3>
                <p className="text-xs text-white/50 font-mono">
                  {authMode === 'login'
                    ? 'Access your private scan history & isolated intelligence'
                    : 'Isolated scans, threat telemetry & persistent audit logs'}
                </p>
              </div>
            </div>

            {/* Mode Switcher Tabs */}
            <div className="grid grid-cols-2 p-1 bg-white/5 rounded-xl border border-white/10 mb-4 text-xs font-semibold">
              <button
                type="button"
                onClick={() => { setAuthMode('login'); setAuthError(null); }}
                className={`py-2 rounded-lg transition-all ${
                  authMode === 'login'
                    ? 'bg-[var(--theme-accent)] text-[#0A0F1D] font-bold shadow-md'
                    : 'text-white/70 hover:text-white'
                }`}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setAuthMode('register'); setAuthError(null); }}
                className={`py-2 rounded-lg transition-all ${
                  authMode === 'register'
                    ? 'bg-[var(--theme-accent)] text-[#0A0F1D] font-bold shadow-md'
                    : 'text-white/70 hover:text-white'
                }`}
              >
                Register
              </button>
            </div>

            {authError && (
              <div
                role="alert"
                className="mb-4 p-3 rounded-xl bg-red-500/15 border border-red-500/30 text-red-300 text-xs flex items-start gap-2"
              >
                <div className="w-1.5 h-1.5 rounded-full bg-red-400 mt-1.5 shrink-0" />
                <span>{authError}</span>
              </div>
            )}

            <form onSubmit={handleAuthSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-mono font-medium text-white/70 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  required
                  autoFocus
                  value={authUsername}
                  onChange={(e) => setAuthUsername(e.target.value)}
                  placeholder="e.g. security_lead"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/15 focus:border-[var(--theme-accent)] text-sm text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-[var(--theme-accent)] font-mono transition-all"
                />
                <span className="text-[10px] text-white/40 font-mono mt-0.5 block">
                  Alphanumeric, underscore or dash (min 3 chars)
                </span>
              </div>

              <div>
                <label className="block text-xs font-mono font-medium text-white/70 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full px-3.5 py-2.5 rounded-xl bg-white/5 border border-white/15 focus:border-[var(--theme-accent)] text-sm text-white placeholder-white/30 focus:outline-none focus:ring-1 focus:ring-[var(--theme-accent)] font-mono transition-all"
                />
                <span className="text-[10px] text-white/40 font-mono mt-0.5 block">
                  Minimum 8 characters
                </span>
              </div>

              <button
                type="submit"
                disabled={authLoading}
                className="w-full theme-button-primary py-2.5 rounded-xl text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 mt-2 disabled:opacity-50"
              >
                {authLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span>Processing...</span>
                  </>
                ) : (
                  <span>{authMode === 'login' ? 'Sign In' : 'Create Account'}</span>
                )}
              </button>
            </form>
          </div>
        </div>
      )}
    </header>
  );
};
