import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertTriangle, Info, X, AlertCircle } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'info' | 'warning';

export interface ToastMessage {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  durationMs?: number;
}

interface ToastProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastProps> = ({ toasts, onDismiss }) => {
  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full pointer-events-none px-4 sm:px-0"
    >
      <AnimatePresence>
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onDismiss={onDismiss} />
        ))}
      </AnimatePresence>
    </div>
  );
};

const ToastItem: React.FC<{ toast: ToastMessage; onDismiss: (id: string) => void }> = ({
  toast,
  onDismiss,
}) => {
  const { id, type, title, message, action, durationMs = 4500 } = toast;

  useEffect(() => {
    if (durationMs > 0) {
      const timer = setTimeout(() => {
        onDismiss(id);
      }, durationMs);
      return () => clearTimeout(timer);
    }
  }, [id, durationMs, onDismiss]);

  const borderColors: Record<ToastType, string> = {
    success: 'border-status-emerald/40 bg-[#09151F]/90 shadow-[0_0_20px_rgba(16,185,129,0.2)]',
    error: 'border-status-coral/40 bg-[#1D0C14]/90 shadow-[0_0_20px_rgba(244,63,94,0.2)]',
    warning: 'border-status-amber/40 bg-[#1A1208]/90 shadow-[0_0_20px_rgba(245,158,11,0.2)]',
    info: 'border-cyan/40 bg-[#081524]/90 shadow-[0_0_20px_rgba(54,228,255,0.2)]',
  };

  const icons: Record<ToastType, React.ReactNode> = {
    success: <CheckCircle2 className="w-5 h-5 text-status-emerald shrink-0" />,
    error: <AlertCircle className="w-5 h-5 text-status-coral shrink-0" />,
    warning: <AlertTriangle className="w-5 h-5 text-status-amber shrink-0" />,
    info: <Info className="w-5 h-5 text-cyan shrink-0" />,
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 10, scale: 0.9 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
      className={`pointer-events-auto p-4 rounded-xl border backdrop-blur-md text-white flex items-start gap-3 ${borderColors[type]}`}
      role="alert"
    >
      {icons[type]}
      <div className="flex-1 min-w-0">
        <div className="text-xs font-bold font-mono tracking-wide text-white">{title}</div>
        {message && <div className="text-xs text-white/70 mt-0.5 leading-relaxed font-sans">{message}</div>}
        {action && (
          <button
            onClick={action.onClick}
            className="mt-2 text-xs font-bold underline hover:text-white transition-colors"
          >
            {action.label}
          </button>
        )}
      </div>
      <button
        onClick={() => onDismiss(id)}
        className="text-white/40 hover:text-white p-1 rounded transition-colors -mr-1 -mt-1"
        aria-label="Dismiss notification"
      >
        <X className="w-4 h-4" />
      </button>
    </motion.div>
  );
};
