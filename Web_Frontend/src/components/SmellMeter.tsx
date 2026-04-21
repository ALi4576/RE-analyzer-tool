import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, AlertTriangle, AlertOctagon } from 'lucide-react';

interface SmellMeterProps {
  smellScore: number;
  label?: string;
}

type Tier = {
  label: string;
  colorVar: string;
  subtleVar: string;
  textVar: string;
  borderVar: string;
  icon: React.ReactNode;
  description: string;
};

function resolveTier(score: number): Tier {
  if (score >= 0.7) {
    return {
      label: 'Good',
      colorVar: 'var(--color-success)',
      subtleVar: 'var(--color-success-subtle)',
      textVar: 'var(--color-success-text)',
      borderVar: 'var(--color-success-subtle-border)',
      icon: <CheckCircle2 className="w-3.5 h-3.5" />,
      description: 'Requirement is well-defined.',
    };
  }
  if (score >= 0.4) {
    return {
      label: 'Warning',
      colorVar: 'var(--color-warning)',
      subtleVar: 'var(--color-warning-subtle)',
      textVar: 'var(--color-warning-text)',
      borderVar: 'var(--color-warning-subtle-border)',
      icon: <AlertTriangle className="w-3.5 h-3.5" />,
      description: 'Ambiguities detected — review recommended.',
    };
  }
  return {
    label: 'Critical',
    colorVar: 'var(--color-danger)',
    subtleVar: 'var(--color-danger-subtle)',
    textVar: 'var(--color-danger-text)',
    borderVar: 'var(--color-danger-subtle-border)',
    icon: <AlertOctagon className="w-3.5 h-3.5" />,
    description: 'Multiple quality issues — clarification needed.',
  };
}

export const SmellMeter: React.FC<SmellMeterProps> = ({
  smellScore,
  label = 'Quality score',
}) => {
  const clamped = Math.min(Math.max(smellScore, 0), 1);
  const quality = 1 - clamped;
  const pct = quality * 100;
  const tier = resolveTier(quality);

  return (
    <div
      className="p-4"
      style={{
        backgroundColor: 'var(--color-surface-sunken)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-lg)',
      }}
    >
      {/* Header row */}
      <div className="flex items-center justify-between mb-3">
        <span
          className="text-xs font-semibold uppercase tracking-wider"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          {label}
        </span>
        <motion.span
          key={tier.label}
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ type: 'spring', damping: 22, stiffness: 220 }}
          className="inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-1 rounded-full"
          style={{
            backgroundColor: tier.subtleVar,
            color: tier.textVar,
            border: `1px solid ${tier.borderVar}`,
          }}
        >
          {tier.icon}
          {tier.label}
        </motion.span>
      </div>

      {/* Progress track */}
      <div
        className="relative h-2 w-full overflow-hidden"
        style={{
          backgroundColor: 'var(--color-border)',
          borderRadius: 'var(--radius-full)',
        }}
        role="progressbar"
        aria-valuenow={Math.round(pct)}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label}
      >
        <motion.div
          className="absolute inset-y-0 left-0"
          style={{
            backgroundColor: tier.colorVar,
            borderRadius: 'var(--radius-full)',
          }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
        />
      </div>

      {/* Footer row */}
      <div className="flex items-center justify-between mt-2.5">
        <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          {tier.description}
        </p>
        <motion.span
          key={pct.toFixed(0)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-xs font-semibold font-mono"
          style={{ color: tier.textVar }}
        >
          {pct.toFixed(0)}%
        </motion.span>
      </div>
    </div>
  );
};
