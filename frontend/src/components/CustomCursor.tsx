import React, { useEffect, useRef, useState } from 'react';
import { useTheme } from '../theme/ThemeContext';
import { hexToRgb } from '../theme/palettes';

interface Particle {
  x: number;
  y: number;
  alpha: number;
  size: number;
}

export const CustomCursor: React.FC = () => {
  const { palette } = useTheme();
  const [isTouchDevice] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
  });

  const dotRef = useRef<HTMLDivElement>(null);
  const innerRingRef = useRef<HTMLDivElement>(null);
  const outerRingRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const styleRef = useRef<HTMLStyleElement | null>(null);

  const mouse = useRef({ x: -100, y: -100 });
  const dotPos = useRef({ x: -100, y: -100 });
  const innerPos = useRef({ x: -100, y: -100 });
  const outerPos = useRef({ x: -100, y: -100 });

  const innerScale = useRef(1);
  const outerScale = useRef(1);
  const particles = useRef<Particle[]>([]);
  const lastParticleSpawn = useRef({ x: -100, y: -100 });

  const isVisible = useRef(false);
  const isPointer = useRef(false);
  const isCard = useRef(false);
  const isInput = useRef(false);
  const isPressed = useRef(false);
  const isInitialized = useRef(false);
  const prefersReducedMotion = useRef(false);

  const rafId = useRef<number>(0);
  const lastTime = useRef<number>(performance.now());
  const accentRgb = useRef<string>('183, 243, 74');

  // React to theme changes live without page reload
  useEffect(() => {
    if (!palette?.accent?.hex) return;
    const rgb = hexToRgb(palette.accent.hex);
    accentRgb.current = `${rgb.r}, ${rgb.g}, ${rgb.b}`;
  }, [palette?.accent?.hex]);

  useEffect(() => {
    if (isTouchDevice) return;

    // Prefers-reduced-motion check
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const applyReducedMotion = (reduced: boolean) => {
      prefersReducedMotion.current = reduced;
      if (innerRingRef.current) innerRingRef.current.style.display = reduced ? 'none' : 'block';
      if (outerRingRef.current) outerRingRef.current.style.display = reduced ? 'none' : 'block';
      if (canvasRef.current) canvasRef.current.style.display = reduced ? 'none' : 'block';
    };
    applyReducedMotion(motionQuery.matches);

    const handleMotionChange = (e: MediaQueryListEvent) => applyReducedMotion(e.matches);
    motionQuery.addEventListener('change', handleMotionChange);

    // Global cursor suppression style injection
    const style = document.createElement('style');
    style.id = 'bhashashield-custom-cursor-style';
    style.textContent = '* { cursor: none !important; }';
    document.head.appendChild(style);
    styleRef.current = style;

    // Theme color cache
    const updateThemeAccent = () => {
      const rgb = getComputedStyle(document.documentElement).getPropertyValue('--theme-accent-rgb').trim();
      if (rgb) accentRgb.current = rgb;
    };
    updateThemeAccent();

    // Canvas resize
    const handleResize = () => {
      if (!canvasRef.current) return;
      canvasRef.current.width = window.innerWidth;
      canvasRef.current.height = window.innerHeight;
    };
    handleResize();
    window.addEventListener('resize', handleResize);

    const lerp = (start: number, end: number, lambda: number, dt: number) =>
      end + (start - end) * Math.exp(-lambda * dt);

    const checkTargetType = (target: HTMLElement | null) => {
      if (!target) {
        isPointer.current = false;
        isCard.current = false;
        isInput.current = false;
        return;
      }
      const inputEl = target.closest('input, textarea, [contenteditable="true"]');
      if (inputEl) {
        if (inputEl instanceof HTMLInputElement) {
          const nonText = ['button', 'submit', 'reset', 'checkbox', 'radio', 'range', 'color', 'file', 'image'];
          isInput.current = !nonText.includes(inputEl.type.toLowerCase());
        } else {
          isInput.current = true;
        }
      } else {
        isInput.current = false;
      }
      const clickable =
        target.closest('button, a, [role="button"], input[type="submit"], input[type="button"]') !== null ||
        target.classList.contains('cursor-pointer') ||
        window.getComputedStyle(target).cursor === 'pointer';
      isPointer.current = clickable && !isInput.current;
      const cardEl = target.closest('.card, [data-cursor-card], .card-elevated');
      isCard.current = cardEl !== null && !clickable && !isInput.current;
    };

    const handleMouseMove = (e: MouseEvent) => {
      mouse.current.x = e.clientX;
      mouse.current.y = e.clientY;
      isVisible.current = true;

      if (!isInitialized.current) {
        dotPos.current = { x: e.clientX, y: e.clientY };
        innerPos.current = { x: e.clientX, y: e.clientY };
        outerPos.current = { x: e.clientX, y: e.clientY };
        lastParticleSpawn.current = { x: e.clientX, y: e.clientY };
        isInitialized.current = true;
      }

      checkTargetType(e.target as HTMLElement | null);

      if (prefersReducedMotion.current && dotRef.current) {
        dotRef.current.style.transform = `translate3d(${e.clientX}px, ${e.clientY}px, 0) translate(-50%, -50%)`;
        dotRef.current.style.opacity = '1';
      }
    };

    const handleMouseDown = () => { isPressed.current = true; };
    const handleMouseUp = () => { isPressed.current = false; };
    const handleMouseLeave = () => {
      isVisible.current = false;
      if (dotRef.current) dotRef.current.style.opacity = '0';
      if (innerRingRef.current) innerRingRef.current.style.opacity = '0';
      if (outerRingRef.current) outerRingRef.current.style.opacity = '0';
    };
    const handleMouseEnter = () => { isVisible.current = true; };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });
    window.addEventListener('mousedown', handleMouseDown, { passive: true });
    window.addEventListener('mouseup', handleMouseUp, { passive: true });
    document.addEventListener('mouseleave', handleMouseLeave);
    document.addEventListener('mouseenter', handleMouseEnter);

    const animate = (currentTime: number) => {
      rafId.current = requestAnimationFrame(animate);
      if (prefersReducedMotion.current) return;

      const dt = Math.min((currentTime - lastTime.current) / 1000, 0.1);
      lastTime.current = currentTime;

      // Position lerps: Dot ~15ms, Inner ~80ms, Outer ~150ms
      dotPos.current.x = lerp(dotPos.current.x, mouse.current.x, 50, dt);
      dotPos.current.y = lerp(dotPos.current.y, mouse.current.y, 50, dt);
      innerPos.current.x = lerp(innerPos.current.x, mouse.current.x, 12.5, dt);
      innerPos.current.y = lerp(innerPos.current.y, mouse.current.y, 12.5, dt);
      outerPos.current.x = lerp(outerPos.current.x, mouse.current.x, 6.67, dt);
      outerPos.current.y = lerp(outerPos.current.y, mouse.current.y, 6.67, dt);

      // Scale calculations: mousedown 0.85x, button hover 1.5x, card subtle pulse
      const clickFactor = isPressed.current ? 0.85 : 1.0;
      const hoverScale = isPointer.current ? 1.5 : 1.0;
      const pulse = isCard.current ? Math.sin(currentTime * 0.005) * 0.08 : 0;
      const targetInner = (hoverScale + pulse) * clickFactor;
      const targetOuter = (hoverScale + pulse * 0.75) * clickFactor;

      innerScale.current = lerp(innerScale.current, targetInner, 14, dt);
      outerScale.current = lerp(outerScale.current, targetOuter, 12, dt);

      // Central dot rendering & morphing
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${dotPos.current.x}px, ${dotPos.current.y}px, 0) translate(-50%, -50%)`;
        dotRef.current.style.opacity = isVisible.current ? '1' : '0';

        if (isInput.current) {
          dotRef.current.style.width = '2px';
          dotRef.current.style.height = '20px';
          dotRef.current.style.borderRadius = '1px';
          dotRef.current.style.backgroundColor = 'var(--theme-accent)';
          dotRef.current.style.boxShadow = '0 0 8px var(--theme-accent)';
        } else if (isPointer.current) {
          dotRef.current.style.width = '6px';
          dotRef.current.style.height = '6px';
          dotRef.current.style.borderRadius = '9999px';
          dotRef.current.style.backgroundColor = '#FFFFFF';
          dotRef.current.style.boxShadow = '0 0 12px #FFFFFF, 0 0 6px var(--theme-accent)';
        } else {
          dotRef.current.style.width = '6px';
          dotRef.current.style.height = '6px';
          dotRef.current.style.borderRadius = '9999px';
          dotRef.current.style.backgroundColor = 'var(--theme-accent)';
          dotRef.current.style.boxShadow = '0 0 10px var(--theme-accent), 0 0 4px #FFFFFF';
        }
      }

      // Inner ring rendering (28px)
      if (innerRingRef.current) {
        innerRingRef.current.style.transform = `translate3d(${innerPos.current.x}px, ${innerPos.current.y}px, 0) translate(-50%, -50%) scale(${innerScale.current})`;
        innerRingRef.current.style.opacity = isVisible.current && !isInput.current ? '1' : '0';
        innerRingRef.current.style.backgroundColor = isPointer.current ? `rgba(${accentRgb.current}, 0.15)` : 'transparent';
      }

      // Outer ring rendering (44px)
      if (outerRingRef.current) {
        outerRingRef.current.style.transform = `translate3d(${outerPos.current.x}px, ${outerPos.current.y}px, 0) translate(-50%, -50%) scale(${outerScale.current})`;
        outerRingRef.current.style.opacity = isVisible.current && !isInput.current ? '0.65' : '0';
      }

      // Particle trail canvas
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
          const dx = mouse.current.x - lastParticleSpawn.current.x;
          const dy = mouse.current.y - lastParticleSpawn.current.y;
          if (Math.hypot(dx, dy) > 7 && isVisible.current && !isInput.current && particles.current.length < 12) {
            particles.current.push({
              x: mouse.current.x,
              y: mouse.current.y,
              alpha: 0.75,
              size: Math.random() * 1.5 + 1.5,
            });
            lastParticleSpawn.current = { x: mouse.current.x, y: mouse.current.y };
          }
          for (let i = particles.current.length - 1; i >= 0; i--) {
            const p = particles.current[i];
            p.alpha -= dt * 2.2;
            p.size = Math.max(0, p.size - dt * 1.2);
            if (p.alpha <= 0.02 || p.size <= 0.1) {
              particles.current.splice(i, 1);
              continue;
            }
            ctx.fillStyle = `rgba(${accentRgb.current}, ${p.alpha})`;
            ctx.shadowColor = `rgba(${accentRgb.current}, ${p.alpha * 0.7})`;
            ctx.shadowBlur = 4;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
    };

    rafId.current = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(rafId.current);
      motionQuery.removeEventListener('change', handleMotionChange);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mouseleave', handleMouseLeave);
      document.removeEventListener('mouseenter', handleMouseEnter);
      if (styleRef.current && styleRef.current.parentNode) {
        styleRef.current.parentNode.removeChild(styleRef.current);
      }
    };
  }, [isTouchDevice]);

  if (isTouchDevice) return null;

  return (
    <>
      <canvas ref={canvasRef} className="fixed inset-0 pointer-events-none z-[99998]" />
      <div
        ref={outerRingRef}
        className="fixed top-0 left-0 pointer-events-none z-[99999] rounded-full will-change-transform"
        style={{
          width: '44px',
          height: '44px',
          border: '1px solid rgba(var(--theme-accent-rgb), 0.4)',
          boxShadow: '0 0 16px rgba(var(--theme-accent-rgb), 0.15)',
          opacity: 0,
          transition: 'border-color 0.2s ease, opacity 0.2s ease',
        }}
      />
      <div
        ref={innerRingRef}
        className="fixed top-0 left-0 pointer-events-none z-[99999] rounded-full will-change-transform"
        style={{
          width: '28px',
          height: '28px',
          border: '1.5px solid var(--theme-accent)',
          boxShadow: '0 0 14px rgba(var(--theme-accent-rgb), 0.35)',
          opacity: 0,
          transition: 'background-color 0.2s ease, border-color 0.2s ease, opacity 0.2s ease',
        }}
      />
      <div
        ref={dotRef}
        className="fixed top-0 left-0 pointer-events-none z-[99999] will-change-transform"
        style={{
          width: '6px',
          height: '6px',
          borderRadius: '9999px',
          backgroundColor: 'var(--theme-accent)',
          boxShadow: '0 0 10px var(--theme-accent), 0 0 4px #FFFFFF',
          opacity: 0,
          transition: 'width 0.18s cubic-bezier(0.16, 1, 0.3, 1), height 0.18s cubic-bezier(0.16, 1, 0.3, 1), border-radius 0.18s ease, background-color 0.2s ease, box-shadow 0.2s ease, opacity 0.15s ease',
        }}
      />
    </>
  );
};
