import React from 'react';
import { motion } from 'framer-motion';
import { RiskLevel } from '../types';

interface RiskGaugeProps {
  score: number;
  level: RiskLevel;
  size?: number;
}

export const RiskGauge: React.FC<RiskGaugeProps> = ({ score, level, size = 180 }) => {
  const strokeWidth = 14;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  // Arc spans 260 degrees (leaving an open gap at bottom)
  const arcLength = circumference * 0.75;
  const normalizedScore = Math.min(100, Math.max(0, score));
  const strokeDashoffset = arcLength - (normalizedScore / 100) * arcLength;

  // Determine styling based on risk level
  const config = {
    LOW: {
      color: '#00D68F',
      glow: 'rgba(0, 214, 143, 0.4)',
      label: 'LOW RISK',
      bgClass: 'bg-status-emerald/10 text-status-emerald border-status-emerald/30'
    },
    MEDIUM: {
      color: '#397BFF',
      glow: 'rgba(57, 123, 255, 0.4)',
      label: 'MEDIUM RISK',
      bgClass: 'bg-neon-blue/10 text-neon-blue border-neon-blue/30'
    },
    HIGH: {
      color: '#FFB547',
      glow: 'rgba(255, 181, 71, 0.4)',
      label: 'HIGH RISK',
      bgClass: 'bg-status-amber/10 text-status-amber border-status-amber/30'
    },
    CRITICAL: {
      color: '#FF4566',
      glow: 'rgba(255, 69, 102, 0.5)',
      label: 'CRITICAL THREAT',
      bgClass: 'bg-status-coral/10 text-status-coral border-status-coral/30'
    }
  }[level] || {
    color: '#00E5FF',
    glow: 'rgba(0, 229, 255, 0.4)',
    label: 'ANALYZING',
    bgClass: 'bg-cyan/10 text-cyan border-cyan/30'
  };

  return (
    <div className="flex flex-col items-center justify-center relative">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          className="transform rotate-[135deg]"
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
        >
          {/* Background Track */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            strokeLinecap="round"
          />

          {/* Animated Value Arc */}
          <motion.circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={config.color}
            strokeWidth={strokeWidth}
            strokeDasharray={`${arcLength} ${circumference}`}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset }}
            transition={{ duration: 1.4, ease: "easeOut" }}
            strokeLinecap="round"
            style={{
              filter: `drop-shadow(0px 0px 8px ${config.glow})`
            }}
          />
        </svg>

        {/* Center Content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
          <motion.span
            className="text-4xl font-extrabold tracking-tight text-txt-primary font-mono"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
          >
            {Math.round(score)}
          </motion.span>
          <span className="text-[11px] uppercase tracking-wider text-txt-secondary font-mono">
            / 100 RISK
          </span>
        </div>
      </div>

      {/* Risk Badge */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`mt-1 px-3 py-1 rounded-full text-xs font-bold tracking-wider border ${config.bgClass}`}
        style={{ boxShadow: `0 0 15px ${config.glow}` }}
      >
        {config.label}
      </motion.div>
    </div>
  );
};
