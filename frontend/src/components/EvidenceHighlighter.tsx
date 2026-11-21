import React, { useState } from 'react';
import { HighlightedSpan } from '../types';

interface EvidenceHighlighterProps {
  text: string;
  spans: HighlightedSpan[];
}

export const EvidenceHighlighter: React.FC<EvidenceHighlighterProps> = ({ text, spans }) => {
  const [activeTooltip, setActiveTooltip] = useState<HighlightedSpan | null>(null);

  if (!spans || spans.length === 0) {
    return (
      <div className="font-mono text-sm leading-relaxed text-txt-primary/90 whitespace-pre-wrap p-4 rounded-xl bg-bg-midnight/60 border border-white/5">
        {text}
      </div>
    );
  }

  // Sort spans by start offset, and filter out any invalid ranges
  const sortedSpans = [...spans]
    .filter(s => s.start >= 0 && s.end > s.start && s.start < text.length)
    .sort((a, b) => a.start - b.start || (b.end - b.start) - (a.end - a.start));

  const elements: React.ReactNode[] = [];
  let lastIndex = 0;

  sortedSpans.forEach((span, idx) => {
    // Clamp start to at least lastIndex to prevent re-rendering overlapping text
    const effectiveStart = Math.max(span.start, lastIndex);
    const effectiveEnd = Math.min(span.end, text.length);

    // If span is fully inside a previously rendered range, skip rendering text (avoid duplication)
    if (effectiveStart >= effectiveEnd) {
      return;
    }

    // Non-highlighted segment before the span
    if (effectiveStart > lastIndex) {
      elements.push(
        <span key={`text-${lastIndex}`}>
          {text.substring(lastIndex, effectiveStart)}
        </span>
      );
    }

    // Determine span highlight class
    const severityClass = {
      CRITICAL: 'threat-span-critical',
      HIGH: 'threat-span-high',
      MEDIUM: 'threat-span-medium',
      LOW: 'bg-status-emerald/20 border-b border-status-emerald text-status-emerald px-1 rounded'
    }[span.severity] || 'threat-span-high';

    const spanText = text.substring(effectiveStart, effectiveEnd);

    elements.push(
      <span
        key={`span-${idx}`}
        className={`relative inline cursor-pointer transition-all hover:brightness-125 ${severityClass}`}
        onMouseEnter={() => setActiveTooltip(span)}
        onMouseLeave={() => setActiveTooltip(null)}
        onClick={() => setActiveTooltip(activeTooltip === span ? null : span)}
      >
        {spanText}
      </span>
    );

    lastIndex = effectiveEnd;
  });

  // Trailing text
  if (lastIndex < text.length) {
    elements.push(
      <span key={`text-${lastIndex}`}>
        {text.substring(lastIndex)}
      </span>
    );
  }

  return (
    <div className="relative">
      <div className="font-mono text-sm leading-relaxed text-txt-primary/90 whitespace-pre-wrap p-4 rounded-xl bg-bg-midnight/70 border border-cyan/20 shadow-inner">
        {elements}
      </div>

      {/* Floating Span Tooltip */}
      {activeTooltip && (
        <div className="mt-3 p-3 rounded-xl bg-bg-card border border-cyan/40 shadow-[0_0_20px_rgba(0,229,255,0.2)] text-xs animate-fadeIn">
          <div className="flex items-center justify-between mb-1">
            <span className="font-bold font-mono text-cyan">
              [{activeTooltip.rule_id}]
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-status-coral/20 text-status-coral border border-status-coral/30">
              {activeTooltip.severity}
            </span>
          </div>
          <p className="text-txt-primary font-medium">{activeTooltip.description}</p>
          <div className="mt-1 text-[11px] text-txt-secondary font-mono">
            Category: <span className="text-txt-primary">{activeTooltip.category}</span> | Offsets: [{activeTooltip.start} : {activeTooltip.end}]
          </div>
        </div>
      )}
    </div>
  );
};
