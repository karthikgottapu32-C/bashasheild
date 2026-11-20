import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './theme/ThemeContext';
import { Navbar } from './components/Navbar';
import { CustomCursor } from './components/CustomCursor';
import {
  QuantumNeuralTransition,
  ViewRoute,
} from './components/QuantumNeuralTransition';
import { LandingPageView } from './views/LandingPageView';
import { TextGuardView } from './views/TextGuardView';
import { DashboardView } from './views/DashboardView';
import { EvaluationView } from './views/EvaluationView';

// Fluid Quantum Neural Spatial Transition Variants
const pageTransition = {
  initial: {
    opacity: 0,
    y: 14,
    scale: 0.985,
    filter: 'blur(6px)',
  },
  animate: {
    opacity: 1,
    y: 0,
    scale: 1,
    filter: 'blur(0px)',
    transition: {
      duration: 0.44,
      ease: [0.16, 1, 0.3, 1],
      staggerChildren: 0.05,
      delayChildren: 0.04,
    },
  },
  exit: {
    opacity: 0,
    y: -10,
    scale: 0.975,
    filter: 'blur(8px)',
    transition: {
      duration: 0.28,
      ease: [0.32, 0, 0.67, 0],
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

  // Execute transition with breakup animation
  const triggerTransition = useCallback((target: ViewRoute) => {
    if (target === currentViewRef.current) return;
    if (isTransitioningRef.current) return; // Prevent duplicate transition triggers

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      setCurrentView(target);
      window.location.hash = target;
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
    window.location.hash = next;
    window.scrollTo({ top: 0, behavior: 'auto' });
  }, []);

  // Completion callback: reset transition state
  const handleTransitionComplete = useCallback(() => {
    setIsTransitioning(false);
  }, []);

  // Deep linking and browser back/forward history support
  useEffect(() => {
    const parseHash = (): ViewRoute => {
      const hash = window.location.hash.replace('#', '').toLowerCase();
      if (hash === 'textguard' || hash === 'text-guard') return 'textguard';
      if (hash === 'dashboard' || hash === 'intelligence') return 'dashboard';
      if (hash === 'evaluation') return 'evaluation';
      return 'landing';
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

      {/* Quantum Neural Spatial Transition Overlay */}
      <QuantumNeuralTransition
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
