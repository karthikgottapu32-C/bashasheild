import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './theme/ThemeContext';
import { Navbar } from './components/Navbar';
import { CustomCursor } from './components/CustomCursor';
import {
  CinematicFragmentationTransition,
  ViewRoute,
} from './components/CinematicFragmentationTransition';
import { LandingPageView } from './views/LandingPageView';
import { TextGuardView } from './views/TextGuardView';
import { DashboardView } from './views/DashboardView';
import { EvaluationView } from './views/EvaluationView';
import { NotFoundView } from './views/NotFoundView';

// Cinematic incoming/outgoing page variants synchronized with fragmentation
const pageTransition = {
  initial: {
    opacity: 0,
    y: 20,
    scale: 0.98,
    filter: 'blur(8px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      duration: 0.52,
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.08,
      delayChildren: 0.06,
    },
  },
  exit: {
    opacity: 0,
    scale: 0.96,
    filter: 'blur(10px)',
    transition: {
      duration: 0.32,
      ease: [0.4, 0, 0.2, 1],
    },
  },
};

// Stagger container variant for view children
export const staggerItem = {
  initial: { opacity: 0, y: 16 },
  animate: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.44, ease: [0.16, 1, 0.3, 1] },
  },
};

export function AppContent() {
  const [currentView, setCurrentView] = useState<ViewRoute>('landing');
  const [fromView, setFromView] = useState<ViewRoute>('landing');
  const [toView, setToView] = useState<ViewRoute>('landing');
  const [isTransitioning, setIsTransitioning] = useState<boolean>(false);

  const currentViewRef = useRef<ViewRoute>(currentView);
  const isTransitioningRef = useRef<boolean>(false);
  const targetViewRef = useRef<ViewRoute>('landing');

  // Keep refs synchronized
  useEffect(() => {
    currentViewRef.current = currentView;
  }, [currentView]);

  useEffect(() => {
    isTransitioningRef.current = isTransitioning;
  }, [isTransitioning]);

  // Dynamic document title and meta description synchronization per view (Check 5 & 6)
  useEffect(() => {
    const titles: Record<ViewRoute, string> = {
      landing: 'BhashaShield — Multilingual AI Security Intelligence Platform',
      textguard: 'BhashaShield — Text Guard Security Scanner',
      dashboard: 'BhashaShield — Intelligence Console & Security Telemetry',
      evaluation: 'BhashaShield — Held-Out Model Evaluation & Benchmarks',
      notfound: 'BhashaShield — 404 Security Vector Not Found',
    };

    const descriptions: Record<ViewRoute, string> = {
      landing: 'Next-generation multilingual prompt-injection defense platform safeguarding AI systems across Telugu, Hindi, Romanized dialects, and mixed scripts.',
      textguard: 'Scan and analyze prompts, user messages, and documents for prompt injection, jailbreaks, and financial fraud across Indian languages.',
      dashboard: 'Real-time telemetry, threat distribution, risk level analytics, and audit history of multilingual security scans.',
      evaluation: 'Independent held-out evaluation benchmarks, calibration metrics, precision, recall, and per-language verification.',
      notfound: 'The requested telemetry endpoint or route could not be found within the BhashaShield security grid.',
    };

    document.title = titles[currentView] || titles.landing;
    const metaDesc = document.querySelector('meta[name="description"]');
    if (metaDesc) {
      metaDesc.setAttribute('content', descriptions[currentView] || descriptions.landing);
    }
  }, [currentView]);

  // Execute transition with breakup animation
  const triggerTransition = useCallback((target: ViewRoute) => {
    if (target === currentViewRef.current) return;
    if (isTransitioningRef.current) return; // Prevent duplicate transition triggers

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      setCurrentView(target);
      window.location.hash = target === 'landing' ? '' : target;
      window.scrollTo({ top: 0, behavior: 'auto' });
      return;
    }

    setFromView(currentViewRef.current);
    setToView(target);
    targetViewRef.current = target;
    setIsTransitioning(true);
  }, []);

  // Midpoint callback from CinematicFragmentationTransition: switch views underneath shards
  const handleTransitionMidpoint = useCallback(() => {
    const next = targetViewRef.current;
    currentViewRef.current = next;
    setCurrentView(next);
    window.location.hash = next === 'landing' ? '' : next;
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  // Completion callback: reset transition state
  const handleTransitionComplete = useCallback(() => {
    setIsTransitioning(false);
  }, []);

  // Deep linking and browser back/forward history support
  useEffect(() => {
    const parseHash = (): ViewRoute => {
      const rawHash = window.location.hash.replace('#', '').trim().toLowerCase();
      if (!rawHash || rawHash === 'landing' || rawHash === 'overview') return 'landing';
      if (rawHash === 'textguard' || rawHash === 'text-guard') return 'textguard';
      if (rawHash === 'dashboard' || rawHash === 'intelligence') return 'dashboard';
      if (rawHash === 'evaluation') return 'evaluation';
      return 'notfound';
    };

    // Initial mount sync
    const initialView = parseHash();
    if (initialView !== currentViewRef.current) {
      setCurrentView(initialView);
      currentViewRef.current = initialView;
      targetViewRef.current = initialView;
    }

    const handleHashChange = () => {
      const target = parseHash();
      // Only trigger if hash changed to a different view than currentViewRef and targetViewRef
      if (
        target !== currentViewRef.current &&
        target !== targetViewRef.current &&
        !isTransitioningRef.current
      ) {
        triggerTransition(target);
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [triggerTransition]);

  const navigateTo = (view: ViewRoute) => {
    triggerTransition(view);
  };

  return (
    <div className="min-h-screen bg-[var(--theme-primary)] text-white relative selection:bg-[var(--theme-accent)] selection:text-black transition-colors duration-700 overflow-x-hidden">
      {/* Desktop Cinematic Multi-Ring & Particle Cursor */}
      <CustomCursor />

      {/* Cinematic Breakup / Fragmentation Overlay */}
      <CinematicFragmentationTransition
        isTransitioning={isTransitioning}
        fromView={fromView}
        toView={toView}
        onMidpoint={handleTransitionMidpoint}
        onComplete={handleTransitionComplete}
      />

      {/* Persistent Navigation */}
      <Navbar currentView={currentView} onNavigate={navigateTo} />

      {/* Main View Router with Fluid Transitions */}
      <main className="relative">
        <AnimatePresence mode="wait">
          {currentView === 'landing' && (
            <motion.div
              key="landing"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <LandingPageView
                onNavigateToTextGuard={() => navigateTo('textguard')}
                onNavigateToDashboard={() => navigateTo('dashboard')}
                onNavigateToEvaluation={() => navigateTo('evaluation')}
              />
            </motion.div>
          )}

          {currentView === 'textguard' && (
            <motion.div
              key="textguard"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <TextGuardView />
            </motion.div>
          )}

          {currentView === 'dashboard' && (
            <motion.div
              key="dashboard"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <DashboardView
                onNavigateToTextGuard={() => navigateTo('textguard')}
                onNavigateToEvaluation={() => navigateTo('evaluation')}
              />
            </motion.div>
          )}

          {currentView === 'evaluation' && (
            <motion.div
              key="evaluation"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <EvaluationView />
            </motion.div>
          )}

          {currentView === 'notfound' && (
            <motion.div
              key="notfound"
              variants={pageTransition}
              initial="initial"
              animate="animate"
              exit="exit"
            >
              <NotFoundView
                onNavigateToLanding={() => navigateTo('landing')}
                onNavigateToTextGuard={() => navigateTo('textguard')}
                onNavigateToDashboard={() => navigateTo('dashboard')}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}

export function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
