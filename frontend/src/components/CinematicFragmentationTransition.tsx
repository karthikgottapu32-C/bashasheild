import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield } from 'lucide-react';

export type ViewRoute = 'landing' | 'textguard' | 'dashboard' | 'evaluation';

interface CinematicFragmentationTransitionProps {
  isTransitioning: boolean;
  fromView: ViewRoute;
  toView: ViewRoute;
  onMidpoint?: () => void;
  onComplete?: () => void;
}

interface ShardConfig {
  id: number;
  // Position percentage in viewport
  top: number;
  left: number;
  width: number;
  height: number;
  // Unique polygon clip-path
  clipPath: string;
  // Center coordinates for vector math
  cx: number;
  cy: number;
}

// 18 carefully calculated polygonal shards forming a shattered glass lattice
const SHARD_CONFIGS: ShardConfig[] = [
  // Top row
  { id: 1, top: 2, left: 3, width: 22, height: 18, clipPath: 'polygon(0% 0%, 100% 5%, 82% 100%, 0% 88%)', cx: 14, cy: 11 },
  { id: 2, top: 0, left: 26, width: 24, height: 20, clipPath: 'polygon(15% 0%, 100% 0%, 88% 95%, 0% 100%)', cx: 38, cy: 10 },
  { id: 3, top: 1, left: 51, width: 23, height: 19, clipPath: 'polygon(0% 12%, 92% 0%, 100% 88%, 12% 100%)', cx: 62, cy: 10 },
  { id: 4, top: 3, left: 75, width: 22, height: 18, clipPath: 'polygon(10% 0%, 100% 15%, 85% 100%, 0% 85%)', cx: 86, cy: 12 },

  // Upper middle row
  { id: 5, top: 21, left: 5, width: 20, height: 24, clipPath: 'polygon(0% 15%, 88% 0%, 100% 90%, 15% 100%)', cx: 15, cy: 33 },
  { id: 6, top: 19, left: 27, width: 22, height: 26, clipPath: 'polygon(0% 0%, 100% 18%, 78% 100%, 8% 85%)', cx: 38, cy: 32 },
  { id: 7, top: 20, left: 51, width: 23, height: 25, clipPath: 'polygon(20% 0%, 100% 8%, 90% 100%, 0% 92%)', cx: 62, cy: 32 },
  { id: 8, top: 22, left: 75, width: 21, height: 23, clipPath: 'polygon(0% 8%, 95% 0%, 100% 85%, 22% 100%)', cx: 85, cy: 33 },

  // Center core shards (shield focus)
  { id: 9, top: 40, left: 34, width: 15, height: 20, clipPath: 'polygon(50% 0%, 100% 40%, 75% 100%, 25% 100%, 0% 40%)', cx: 41, cy: 50 },
  { id: 10, top: 41, left: 51, width: 16, height: 20, clipPath: 'polygon(50% 0%, 100% 35%, 80% 100%, 20% 100%, 0% 35%)', cx: 59, cy: 51 },

  // Lower middle row
  { id: 11, top: 48, left: 4, width: 26, height: 24, clipPath: 'polygon(0% 0%, 100% 15%, 85% 100%, 0% 85%)', cx: 17, cy: 60 },
  { id: 12, top: 62, left: 25, width: 24, height: 22, clipPath: 'polygon(12% 0%, 95% 5%, 85% 100%, 0% 90%)', cx: 37, cy: 73 },
  { id: 13, top: 63, left: 52, width: 24, height: 22, clipPath: 'polygon(0% 8%, 88% 0%, 100% 90%, 15% 100%)', cx: 64, cy: 74 },
  { id: 14, top: 47, left: 72, width: 24, height: 25, clipPath: 'polygon(15% 0%, 100% 10%, 82% 100%, 0% 95%)', cx: 84, cy: 59 },

  // Bottom row
  { id: 15, top: 76, left: 3, width: 22, height: 20, clipPath: 'polygon(0% 10%, 90% 0%, 100% 85%, 15% 100%)', cx: 14, cy: 86 },
  { id: 16, top: 82, left: 28, width: 22, height: 16, clipPath: 'polygon(10% 0%, 100% 15%, 88% 100%, 0% 88%)', cx: 39, cy: 90 },
  { id: 17, top: 83, left: 52, width: 22, height: 15, clipPath: 'polygon(0% 0%, 100% 10%, 80% 100%, 10% 90%)', cx: 63, cy: 90 },
  { id: 18, top: 75, left: 75, width: 22, height: 21, clipPath: 'polygon(12% 0%, 100% 0%, 85% 92%, 0% 100%)', cx: 86, cy: 85 },
];

export const CinematicFragmentationTransition: React.FC<CinematicFragmentationTransitionProps> = ({
  isTransitioning,
  fromView,
  toView,
  onMidpoint,
  onComplete,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animFrameRef = useRef<number>(0);
  const midpointFiredRef = useRef<boolean>(false);
  const completeFiredRef = useRef<boolean>(false);

  // Reactive mobile detection
  const [isMobile, setIsMobile] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.innerWidth < 768;
  });

  // Reactive reduced motion detection
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    const handleResize = () => setIsMobile(window.innerWidth < 768);
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleMotion = () => setPrefersReducedMotion(media.matches);

    window.addEventListener('resize', handleResize);
    media.addEventListener('change', handleMotion);

    return () => {
      window.removeEventListener('resize', handleResize);
      media.removeEventListener('change', handleMotion);
    };
  }, []);

  // Determine transition variation
  const transitionType = useMemo(() => {
    if (fromView === 'landing' && toView === 'textguard') return 'radial_pulse';
    if (fromView === 'textguard' && toView === 'dashboard') return 'scanner_shear';
    if (fromView === 'dashboard' && toView === 'evaluation') return 'telemetry_lift';
    if (fromView === 'evaluation' && toView === 'landing') return 'shield_convergence';
    return 'omnidirectional';
  }, [fromView, toView]);

  // Handle midpoint (when views swap) and completion lifecycle
  useEffect(() => {
    if (!isTransitioning) {
      midpointFiredRef.current = false;
      completeFiredRef.current = false;
      return;
    }

    // Midpoint trigger: outgoing page finishes fragmenting, incoming page mounts underneath
    const midTimer = setTimeout(() => {
      if (!midpointFiredRef.current) {
        midpointFiredRef.current = true;
        onMidpoint?.();
      }
    }, prefersReducedMotion ? 80 : 280);

    // Completion trigger: fragments fully dissolve and clear
    const compTimer = setTimeout(() => {
      if (!completeFiredRef.current) {
        completeFiredRef.current = true;
        onComplete?.();
      }
    }, prefersReducedMotion ? 160 : 620);

    return () => {
      clearTimeout(midTimer);
      clearTimeout(compTimer);
    };
  }, [isTransitioning, prefersReducedMotion, onMidpoint, onComplete]);

  // Canvas particle trail simulation for high-speed sparks
  useEffect(() => {
    if (!isTransitioning || prefersReducedMotion || isMobile) return;

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Read active theme accent RGB
    const computedStyle = getComputedStyle(document.documentElement);
    const accentRgbStr = computedStyle.getPropertyValue('--theme-accent-rgb').trim() || '183, 243, 74';
    const accentRgb = accentRgbStr.split(',').map(s => parseInt(s.trim(), 10)) as [number, number, number];

    interface Particle {
      x: number;
      y: number;
      vx: number;
      vy: number;
      size: number;
      alpha: number;
      decay: number;
      color: string;
    }

    const particleCount = 36;
    const particles: Particle[] = [];

    const centerX = canvas.width / 2;
    const centerY = canvas.height * 0.45;

    for (let i = 0; i < particleCount; i++) {
      let x = centerX;
      let y = centerY;
      let vx = (Math.random() - 0.5) * 12;
      let vy = (Math.random() - 0.5) * 12;

      if (transitionType === 'radial_pulse') {
        const angle = (Math.PI * 2 * i) / particleCount + (Math.random() - 0.5) * 0.4;
        const speed = 6 + Math.random() * 12;
        vx = Math.cos(angle) * speed;
        vy = Math.sin(angle) * speed;
      } else if (transitionType === 'scanner_shear') {
        x = Math.random() * canvas.width * 0.4;
        y = Math.random() * canvas.height;
        vx = 9 + Math.random() * 14;
        vy = (Math.random() - 0.5) * 4;
      } else if (transitionType === 'telemetry_lift') {
        x = Math.random() * canvas.width;
        y = canvas.height * 0.7 + Math.random() * canvas.height * 0.3;
        vx = (Math.random() - 0.5) * 5;
        vy = -(7 + Math.random() * 11);
      } else if (transitionType === 'shield_convergence') {
        const angle = Math.random() * Math.PI * 2;
        const dist = 300 + Math.random() * 400;
        x = centerX + Math.cos(angle) * dist;
        y = centerY + Math.sin(angle) * dist;
        vx = -Math.cos(angle) * (10 + Math.random() * 8);
        vy = -Math.sin(angle) * (10 + Math.random() * 8);
      }

      particles.push({
        x,
        y,
        vx,
        vy,
        size: 1.5 + Math.random() * 3,
        alpha: 0.9,
        decay: 0.016 + Math.random() * 0.02,
        color: Math.random() > 0.35 ? `rgba(${accentRgb[0]}, ${accentRgb[1]}, ${accentRgb[2]}` : 'rgba(242, 244, 239',
      });
    }

    const startTime = performance.now();
    const duration = 800;

    const render = (time: number) => {
      const elapsed = time - startTime;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < particles.length; i++) {
        const p = particles[i];
        p.x += p.vx;
        p.y += p.vy;
        p.vx *= 0.96;
        p.vy *= 0.96;
        p.alpha -= p.decay;

        if (p.alpha <= 0) continue;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = `${p.color}, ${Math.max(0, p.alpha)})`;
        ctx.shadowBlur = 10;
        ctx.shadowColor = `rgba(${accentRgb[0]}, ${accentRgb[1]}, ${accentRgb[2]}, 0.8)`;
        ctx.fill();
      }

      if (elapsed < duration) {
        animFrameRef.current = requestAnimationFrame(render);
      }
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
    };
  }, [isTransitioning, transitionType, prefersReducedMotion, isMobile]);

  // Reduced motion fallback
  if (prefersReducedMotion) {
    return (
      <AnimatePresence>
        {isTransitioning && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: [0, 0.4, 0] }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="fixed inset-0 pointer-events-none z-50 bg-[var(--theme-primary)]"
          />
        )}
      </AnimatePresence>
    );
  }

  // Calculate 3D motion vectors for each shard based on transition variation
  const getShardAnimation = (shard: ShardConfig) => {
    const dx = (shard.cx - 50) * 12;
    const dy = (shard.cy - 45) * 9;

    switch (transitionType) {
      case 'radial_pulse':
        // Overview -> Text Guard: radial burst outward from shield center
        return {
          initial: {
            x: 0,
            y: 0,
            z: 0,
            rotateX: 0,
            rotateY: 0,
            rotateZ: 0,
            scale: 1,
            opacity: 0.95,
          },
          animate: {
            x: dx * 1.6,
            y: dy * 1.6,
            z: 220,
            rotateX: (Math.random() - 0.5) * 70,
            rotateY: (Math.random() - 0.5) * 80,
            rotateZ: (Math.random() - 0.5) * 45,
            scale: 0.85,
            opacity: [0.95, 0.85, 0],
            transition: {
              duration: 0.72,
              ease: [0.22, 1, 0.36, 1],
              delay: (Math.abs(shard.cx - 50) + Math.abs(shard.cy - 45)) * 0.0025,
            },
          },
        };

      case 'scanner_shear':
        // Text Guard -> Dashboard: horizontal laser shear
        return {
          initial: {
            x: 0,
            y: 0,
            z: 0,
            rotateX: 0,
            rotateY: 0,
            rotateZ: 0,
            scale: 1,
            opacity: 0.95,
          },
          animate: {
            x: 180 + Math.random() * 220,
            y: (Math.random() - 0.5) * 80,
            z: 140,
            rotateX: 15,
            rotateY: -25,
            rotateZ: -18,
            scale: 0.8,
            opacity: [0.95, 0.9, 0],
            transition: {
              duration: 0.75,
              ease: [0.16, 1, 0.3, 1],
              delay: (shard.cx / 100) * 0.18,
            },
          },
        };

      case 'telemetry_lift':
        // Dashboard -> Evaluation: vertical matrix telemetry lift
        return {
          initial: {
            x: 0,
            y: 0,
            z: 0,
            rotateX: 0,
            rotateY: 0,
            rotateZ: 0,
            scale: 1,
            opacity: 0.95,
          },
          animate: {
            x: (Math.random() - 0.5) * 120,
            y: -180 - Math.random() * 200,
            z: 180,
            rotateX: -45,
            rotateY: (Math.random() - 0.5) * 40,
            rotateZ: 10,
            scale: 0.75,
            opacity: [0.95, 0.8, 0],
            transition: {
              duration: 0.76,
              ease: [0.2, 0.8, 0.2, 1],
              delay: ((100 - shard.cy) / 100) * 0.16,
            },
          },
        };

      case 'shield_convergence':
        // Evaluation -> Overview: converge from perimeter inward toward center
        return {
          initial: {
            x: dx * 2.2,
            y: dy * 2.2,
            z: 280,
            rotateX: 55,
            rotateY: -45,
            rotateZ: 30,
            scale: 1.4,
            opacity: 0,
          },
          animate: {
            x: [dx * 2.2, dx * 0.2, 0],
            y: [dy * 2.2, dy * 0.2, 0],
            z: [280, 50, 0],
            rotateX: [55, 10, 0],
            rotateY: [-45, -5, 0],
            rotateZ: [30, 5, 0],
            scale: [1.4, 0.9, 0.1],
            opacity: [0, 0.95, 0],
            transition: {
              duration: 0.78,
              times: [0, 0.55, 1],
              ease: [0.25, 1, 0.5, 1],
            },
          },
        };

      default:
        // Omnidirectional dissolve
        return {
          initial: {
            x: 0,
            y: 0,
            z: 0,
            rotateX: 0,
            rotateY: 0,
            rotateZ: 0,
            scale: 1,
            opacity: 0.95,
          },
          animate: {
            x: dx * 1.3,
            y: dy * 1.3,
            z: 160,
            rotateX: (Math.random() - 0.5) * 50,
            rotateY: (Math.random() - 0.5) * 60,
            rotateZ: (Math.random() - 0.5) * 35,
            scale: 0.85,
            opacity: [0.95, 0.85, 0],
            transition: {
              duration: 0.7,
              ease: [0.16, 1, 0.3, 1],
              delay: Math.random() * 0.1,
            },
          },
        };
    }
  };

  const activeShards = isMobile ? SHARD_CONFIGS.slice(0, 8) : SHARD_CONFIGS;

  if (!isTransitioning) return null;

  return (
    <div
      key="fragmentation-root-overlay"
      data-fragmentation-overlay="true"
      className="fixed inset-0 pointer-events-none z-50 overflow-hidden"
      style={{ perspective: '1200px' }}
    >
          {/* 1. Luminous Accent Light Sweep Beam */}
          <motion.div
            className="absolute top-0 bottom-0 w-[55%] pointer-events-none"
            initial={{ x: '-120%', skewX: -22, opacity: 0 }}
            animate={{
              x: '240%',
              skewX: -22,
              opacity: [0, 0.85, 0.85, 0],
            }}
            transition={{ duration: 0.75, ease: [0.16, 1, 0.3, 1] }}
            style={{
              background: `linear-gradient(90deg, transparent 0%, rgba(var(--theme-accent-rgb), 0.06) 20%, rgba(var(--theme-accent-rgb), 0.38) 48%, rgba(242, 244, 239, 0.65) 50%, rgba(var(--theme-accent-rgb), 0.38) 52%, transparent 80%)`,
              filter: 'blur(12px)',
            }}
          />

          {/* 2. Variation-Specific Pulse / Shockwave Effects */}
          {transitionType === 'radial_pulse' && (
            <motion.div
              className="absolute rounded-full pointer-events-none -translate-x-1/2 -translate-y-1/2"
              style={{
                top: '45%',
                left: '50%',
                border: '2px solid rgba(var(--theme-accent-rgb), 0.9)',
                boxShadow: '0 0 60px rgba(var(--theme-accent-rgb), 0.8), inset 0 0 40px rgba(var(--theme-accent-rgb), 0.4)',
              }}
              initial={{ width: 40, height: 40, scale: 0.2, opacity: 1 }}
              animate={{ width: 1400, height: 1400, scale: 1.8, opacity: [1, 0.8, 0] }}
              transition={{ duration: 0.72, ease: [0.16, 1, 0.3, 1] }}
            />
          )}

          {transitionType === 'scanner_shear' && (
            <motion.div
              className="absolute top-0 bottom-0 w-1 pointer-events-none"
              style={{
                background: 'var(--theme-accent)',
                boxShadow: '0 0 35px 8px var(--theme-accent), 0 0 80px 16px rgba(var(--theme-accent-rgb), 0.6)',
              }}
              initial={{ left: '-5%', opacity: 1 }}
              animate={{ left: '105%', opacity: [1, 1, 0] }}
              transition={{ duration: 0.68, ease: 'easeInOut' }}
            />
          )}

          {transitionType === 'shield_convergence' && (
            <motion.div
              className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 flex items-center justify-center pointer-events-none"
              initial={{ scale: 0.6, opacity: 0 }}
              animate={{
                scale: [0.6, 1.35, 1.6],
                opacity: [0, 0.95, 0],
              }}
              transition={{ duration: 0.78, times: [0, 0.55, 1], ease: [0.16, 1, 0.3, 1] }}
            >
              <div className="relative">
                <Shield className="w-32 h-32 text-[var(--theme-accent)] drop-shadow-[0_0_40px_var(--theme-accent)]" />
                <div
                  className="absolute inset-0 rounded-full"
                  style={{
                    background: 'radial-gradient(circle, rgba(var(--theme-accent-rgb), 0.5) 0%, transparent 70%)',
                    filter: 'blur(20px)',
                  }}
                />
              </div>
            </motion.div>
          )}

          {/* 3. High-Speed Luminous Spark Trail Canvas */}
          <canvas
            ref={canvasRef}
            data-transition-canvas="true"
            className="absolute inset-0 pointer-events-none z-20"
          />

          {/* 4. Geometric Obsidian Glass Shards */}
          <div className="absolute inset-0 pointer-events-none z-10">
            {activeShards.map((shard) => {
              const anim = getShardAnimation(shard);

              return (
                <motion.div
                  key={shard.id}
                  data-fragment-shard="true"
                  className="absolute pointer-events-none"
                  style={{
                    top: `${shard.top}%`,
                    left: `${shard.left}%`,
                    width: `${shard.width}vw`,
                    height: `${shard.height}vh`,
                    clipPath: shard.clipPath,
                    transformStyle: 'preserve-3d',
                    willChange: 'transform, opacity',
                  }}
                  initial={anim.initial}
                  animate={anim.animate}
                >
                  {/* Glass Shard Body: Obsidian surface with specular reflection */}
                  <div
                    className="w-full h-full relative"
                    style={{
                      background: `linear-gradient(135deg, rgba(9, 11, 9, 0.92) 0%, rgba(20, 25, 20, 0.84) 100%)`,
                      backdropFilter: 'blur(10px)',
                      WebkitBackdropFilter: 'blur(10px)',
                      boxShadow: 'inset 0 1px 2px 0 rgba(242, 244, 239, 0.5), inset 0 0 18px 0 rgba(var(--theme-accent-rgb), 0.25)',
                    }}
                  >
                    {/* White reflective edge highlights */}
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{
                        border: '1.2px solid rgba(242, 244, 239, 0.45)',
                        mixBlendMode: 'screen',
                      }}
                    />

                    {/* Luminous lime edge glint on corner */}
                    <div
                      className="absolute top-0 left-0 right-0 h-[2px]"
                      style={{
                        background: 'linear-gradient(90deg, transparent 0%, var(--theme-accent) 50%, transparent 100%)',
                        boxShadow: '0 0 8px var(--theme-accent)',
                      }}
                    />

                    {/* Obsidian gloss gradient overlay */}
                    <div
                      className="absolute inset-0 pointer-events-none"
                      style={{
                        background: 'linear-gradient(115deg, rgba(255, 255, 255, 0.18) 0%, transparent 45%, rgba(var(--theme-accent-rgb), 0.12) 85%)',
                      }}
                    />
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>
      );
    };
