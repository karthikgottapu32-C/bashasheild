import React, { useEffect, useRef, useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, Sparkles, Cpu, Activity, Zap } from 'lucide-react';
import { useTheme } from '../theme/useTheme';

export type ViewRoute = 'landing' | 'textguard' | 'dashboard' | 'evaluation';

interface QuantumNeuralTransitionProps {
  isTransitioning: boolean;
  fromView: ViewRoute;
  toView: ViewRoute;
  onMidpoint?: () => void;
  onComplete?: () => void;
}

interface WarpStream {
  x: number;
  y: number;
  z: number;
  pz: number;
  speed: number;
  length: number;
  alpha: number;
}

export const QuantumNeuralTransition: React.FC<QuantumNeuralTransitionProps> = ({
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
  const { palette } = useTheme();

  // Route metadata for cinematic HUD readout
  const routeMeta = useMemo(() => {
    switch (toView) {
      case 'textguard':
        return {
          code: 'LAYER 01',
          title: 'TEXT GUARD INSTRUMENT',
          subtitle: 'MULTI-SCRIPT THREAT INTERCEPTION DECK',
          icon: Shield,
        };
      case 'dashboard':
        return {
          code: 'LAYER 02',
          title: 'INTELLIGENCE CONSOLE',
          subtitle: 'REAL-TIME INCIDENT TELEMETRY & ATTACK SURFACES',
          icon: Activity,
        };
      case 'evaluation':
        return {
          code: 'LAYER 03',
          title: 'SCIENTIFIC BENCHMARK',
          subtitle: 'HELD-OUT ADVERSARIAL VALIDATION PIPELINE',
          icon: Cpu,
        };
      case 'landing':
      default:
        return {
          code: 'CORE',
          title: 'BHASHASHIELD COMMAND',
          subtitle: 'MULTILINGUAL AI SECURITY PLATFORM',
          icon: Zap,
        };
    }
  }, [toView]);

  // Reactive motion preference
  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  useEffect(() => {
    const media = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleMotion = () => setPrefersReducedMotion(media.matches);
    media.addEventListener('change', handleMotion);
    return () => media.removeEventListener('change', handleMotion);
  }, []);

  // Main canvas animation effect
  useEffect(() => {
    if (!isTransitioning || prefersReducedMotion) return;

    midpointFiredRef.current = false;
    completeFiredRef.current = false;

    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    const startTime = performance.now();
    const duration = 650; // Total duration in ms
    const midpointTime = 300; // View switch moment

    // Generate 3D perspective warp stream vectors
    const numStreams = width < 768 ? 48 : 88;
    const streams: WarpStream[] = [];
    const centerX = width / 2;
    const centerY = height / 2;

    for (let i = 0; i < numStreams; i++) {
      streams.push({
        x: (Math.random() - 0.5) * width * 1.6,
        y: (Math.random() - 0.5) * height * 1.6,
        z: Math.random() * 1000 + 100,
        pz: 1000,
        speed: Math.random() * 22 + 18,
        length: Math.random() * 28 + 14,
        alpha: Math.random() * 0.7 + 0.3,
      });
    }

    const render = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);

      // Midpoint trigger
      if (elapsed >= midpointTime && !midpointFiredRef.current) {
        midpointFiredRef.current = true;
        if (onMidpoint) onMidpoint();
      }

      // Completion trigger
      if (elapsed >= duration && !completeFiredRef.current) {
        completeFiredRef.current = true;
        if (onComplete) onComplete();
        return;
      }

      ctx.clearRect(0, 0, width, height);

      // Envelope curves
      // Phase 1 (0 to 0.45): accelerate & compress
      // Phase 2 (0.45 to 1.0): decelerate & diffuse
      const intensity =
        progress < 0.45
          ? Math.sin((progress / 0.45) * (Math.PI / 2))
          : Math.cos(((progress - 0.45) / 0.55) * (Math.PI / 2));

      // 1. Dark frosted spatial vignette
      const darkAlpha = Math.min(0.85, intensity * 0.88);
      ctx.fillStyle = `rgba(9, 13, 22, ${darkAlpha})`;
      ctx.fillRect(0, 0, width, height);

      // 2. Central ambient energy bloom
      const grad = ctx.createRadialGradient(
        centerX,
        centerY,
        10,
        centerX,
        centerY,
        Math.max(width, height) * 0.65
      );
      grad.addColorStop(0, `rgba(var(--theme-accent-rgb), ${0.22 * intensity})`);
      grad.addColorStop(0.4, `rgba(var(--theme-accent-rgb), ${0.08 * intensity})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, width, height);

      // 3. Render 3D neural warp lines
      ctx.lineWidth = 1.5;
      for (let i = 0; i < streams.length; i++) {
        const s = streams[i];
        s.pz = s.z;
        s.z -= s.speed * (intensity * 2.2 + 0.3);

        if (s.z <= 10) {
          s.z = 1000;
          s.pz = 1000;
          s.x = (Math.random() - 0.5) * width * 1.6;
          s.y = (Math.random() - 0.5) * height * 1.6;
        }

        const k = 420 / s.z;
        const px = s.x * k + centerX;
        const py = s.y * k + centerY;

        const pk = 420 / s.pz;
        const prevX = s.x * pk + centerX;
        const prevY = s.y * pk + centerY;

        if (px >= 0 && px <= width && py >= 0 && py <= height) {
          const streamAlpha = s.alpha * intensity;
          ctx.strokeStyle = `rgba(var(--theme-accent-rgb), ${streamAlpha})`;
          ctx.beginPath();
          ctx.moveTo(prevX, prevY);
          ctx.lineTo(px, py);
          ctx.stroke();

          // Spark particle head
          ctx.fillStyle = `rgba(255, 255, 255, ${streamAlpha * 1.2})`;
          ctx.beginPath();
          ctx.arc(px, py, 1.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }

      // 4. Anamorphic horizontal specular sweep flare
      const sweepY = centerY + Math.sin(progress * Math.PI) * 20;
      const sweepWidth = width * 0.85;
      const sweepGrad = ctx.createLinearGradient(
        centerX - sweepWidth / 2,
        sweepY,
        centerX + sweepWidth / 2,
        sweepY
      );
      sweepGrad.addColorStop(0, 'rgba(var(--theme-accent-rgb), 0)');
      sweepGrad.addColorStop(0.5, `rgba(var(--theme-accent-rgb), ${0.45 * intensity})`);
      sweepGrad.addColorStop(1, 'rgba(var(--theme-accent-rgb), 0)');

      ctx.fillStyle = sweepGrad;
      ctx.fillRect(centerX - sweepWidth / 2, sweepY - 1, sweepWidth, 2);

      animFrameRef.current = requestAnimationFrame(render);
    };

    animFrameRef.current = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animFrameRef.current);
      window.removeEventListener('resize', handleResize);
    };
  }, [isTransitioning, prefersReducedMotion, onMidpoint, onComplete]);

  // Reduced motion immediate bypass
  useEffect(() => {
    if (isTransitioning && prefersReducedMotion) {
      if (onMidpoint) onMidpoint();
      const t = setTimeout(() => {
        if (onComplete) onComplete();
      }, 50);
      return () => clearTimeout(t);
    }
  }, [isTransitioning, prefersReducedMotion, onMidpoint, onComplete]);

  if (!isTransitioning || prefersReducedMotion) {
    return null;
  }

  const RouteIcon = routeMeta.icon;

  return (
    <div
      className="fixed inset-0 z-50 pointer-events-none flex items-center justify-center overflow-hidden"
      aria-hidden="true"
    >
      {/* Dynamic 3D Warp Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full" />

      {/* Cinematic HUD Layer Indicator */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9, y: 10 }}
        animate={{
          opacity: [0, 1, 1, 0],
          scale: [0.92, 1, 1.02, 1.06],
          y: [8, 0, 0, -6],
        }}
        transition={{
          duration: 0.65,
          times: [0, 0.25, 0.7, 1],
          ease: 'easeInOut',
        }}
        className="relative z-10 flex flex-col items-center text-center px-6 py-5 rounded-2xl bg-black/60 backdrop-blur-xl border border-[var(--theme-accent)]/30 shadow-[0_0_50px_rgba(var(--theme-accent-rgb),0.3)]"
      >
        {/* Glowing Beacon Core */}
        <div className="relative mb-3 flex items-center justify-center">
          <div className="w-12 h-12 rounded-xl bg-[var(--theme-accent)]/15 border border-[var(--theme-accent)]/40 flex items-center justify-center text-[var(--theme-accent)] shadow-[0_0_20px_rgba(var(--theme-accent-rgb),0.4)]">
            <RouteIcon className="w-6 h-6 animate-pulse" />
          </div>
          <span className="absolute -inset-1 rounded-xl bg-[var(--theme-accent)]/20 blur-md animate-ping pointer-events-none" />
        </div>

        {/* Code & Title */}
        <div className="flex items-center gap-2 mb-1">
          <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold tracking-widest bg-[var(--theme-accent)]/20 text-[var(--theme-accent)] border border-[var(--theme-accent)]/30">
            {routeMeta.code}
          </span>
          <span className="text-xs font-mono font-bold tracking-wider text-white/90">
            {routeMeta.title}
          </span>
        </div>

        {/* Subtitle */}
        <p className="text-[11px] font-mono text-white/60 tracking-wider uppercase">
          {routeMeta.subtitle}
        </p>

        {/* Progress Horizon Line */}
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: '100%' }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
          className="h-[2px] mt-3 bg-gradient-to-r from-transparent via-[var(--theme-accent)] to-transparent"
        />
      </motion.div>
    </div>
  );
};
