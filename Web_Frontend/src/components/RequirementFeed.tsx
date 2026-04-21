import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Layers } from 'lucide-react';
import { FormalizedRequirement, ISORequirement } from '@/types/index';
import RequirementCard from './RequirementCard';
import { useRequirementStore } from '@/store/requirementStore';

interface RequirementFeedProps {
  requirements: FormalizedRequirement | null;
  isLoading: boolean;
}

const spring = { type: 'spring' as const, damping: 24, stiffness: 220 };

const SkeletonCard: React.FC<{ delay: number }> = ({ delay }) => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    transition={{ delay, duration: 0.25 }}
    className="p-4 space-y-3"
    style={{
      backgroundColor: 'var(--color-surface)',
      border: '1px solid var(--color-border)',
      borderRadius: 'var(--radius-lg)',
    }}
  >
    <div className="flex items-center gap-2">
      <div className="skeleton h-5 w-20" />
      <div className="skeleton h-4 w-16" style={{ borderRadius: 'var(--radius-full)' }} />
    </div>
    <div className="skeleton h-4 w-4/5" />
    <div className="skeleton h-12 w-full" />
    <div className="skeleton h-3 w-full" />
    <div className="skeleton h-3 w-3/4" />
  </motion.div>
);

export const RequirementFeed: React.FC<RequirementFeedProps> = ({
  requirements,
  isLoading,
}) => {
  const feedRef = useRef<HTMLDivElement>(null);
  const updateRequirement = useRequirementStore((s) => s.updateRequirement);
  const clarifyOneRequirement = useRequirementStore((s) => s.clarifyOneRequirement);

  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [requirements]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {[0, 1, 2].map((i) => (
          <SkeletonCard key={i} delay={i * 0.08} />
        ))}
      </div>
    );
  }

  if (!requirements || requirements.total_requirements === 0) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex flex-col items-center justify-center text-center p-10"
        style={{
          backgroundColor: 'var(--color-surface-sunken)',
          border: '1px dashed var(--color-border-strong)',
          borderRadius: 'var(--radius-lg)',
        }}
      >
        <div
          className="flex items-center justify-center mb-3"
          style={{
            width: 48,
            height: 48,
            borderRadius: 'var(--radius-md)',
            backgroundColor: 'var(--color-surface-raised)',
            color: 'var(--color-text-muted)',
          }}
        >
          <Layers className="w-5 h-5" />
        </div>
        <p
          className="text-sm font-medium"
          style={{ color: 'var(--color-text-primary)' }}
        >
          No requirements yet
        </p>
        <p
          className="text-xs mt-1"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          Speak, upload, or type your requirement to generate ISO 29148 specs.
        </p>
      </motion.div>
    );
  }

  const reqs: ISORequirement[] =
    requirements.iso_requirements || requirements.requirements || [];
  // Document-level average — used for the summary footer and as a fallback
  // for any requirement whose per-item score was not produced by the backend.
  const completeness = requirements.completeness_score || 0;
  // Smell-based quality is the metric both the footer and the per-card meter
  // display. Fall back to `completeness` when the backend has not yet
  // populated it so older sessions still render a meaningful value.
  const cumulativeQuality =
    typeof requirements.quality_score === 'number'
      ? requirements.quality_score
      : completeness;

  return (
    <div ref={feedRef} className="space-y-3" style={{ scrollBehavior: 'smooth' }}>
      <AnimatePresence initial={false}>
        {reqs.map((req, idx) => (
          <motion.div
            key={req.requirement_id || req.id || idx}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -6 }}
            transition={{ ...spring, delay: Math.min(idx * 0.04, 0.4) }}
          >
            <RequirementCard
              requirement={req}
              completeness_score={
                typeof req.completeness_score === 'number'
                  ? req.completeness_score
                  : completeness
              }
              quality_score={
                typeof req.quality_score === 'number'
                  ? req.quality_score
                  : typeof req.completeness_score === 'number'
                    ? req.completeness_score
                    : cumulativeQuality
              }
              is_highlighted={false}
              onUpdate={(updated) =>
                updateRequirement(
                  updated.requirement_id || updated.id || '',
                  updated
                )
              }
              onClarify={(r, context) =>
                clarifyOneRequirement(r.requirement_id ?? '', context)
              }
            />
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Completeness summary */}
      {reqs.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: Math.min(reqs.length * 0.04 + 0.1, 0.5) }}
          className="px-4 py-3 flex items-center justify-between"
          style={{
            backgroundColor: 'var(--color-primary-subtle)',
            border: '1px solid var(--color-primary-subtle-border)',
            borderRadius: 'var(--radius-lg)',
          }}
        >
          <p
            className="text-xs font-medium"
            style={{ color: 'var(--color-primary-text)' }}
          >
            {reqs.length} requirement{reqs.length !== 1 ? 's' : ''} generated
          </p>
          <div className="flex items-center gap-2">
            <div
              className="w-24 h-1.5 overflow-hidden"
              style={{
                backgroundColor: 'var(--color-border)',
                borderRadius: 'var(--radius-full)',
              }}
            >
              <motion.div
                className="h-full"
                style={{
                  backgroundColor: 'var(--color-primary)',
                  borderRadius: 'var(--radius-full)',
                }}
                animate={{ width: `${Math.round(cumulativeQuality * 100)}%` }}
                transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              />
            </div>
            <span
              className="text-xs font-semibold font-mono tabular-nums"
              style={{ color: 'var(--color-primary-text)' }}
            >
              {Math.round(cumulativeQuality * 100)}%
            </span>
          </div>
        </motion.div>
      )}
    </div>
  );
};
