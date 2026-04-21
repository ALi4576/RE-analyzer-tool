import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { HelpCircle, CheckCircle2, AlertCircle, Sparkles } from 'lucide-react';
import { ClarificationQuestion } from '@/types/index';

interface ClarificationPanelProps {
  questions: ClarificationQuestion[] | null;
  onSubmit: (clarifications: Record<string, string>) => Promise<void>;
  isLoading: boolean;
}

const spring = { type: 'spring' as const, damping: 24, stiffness: 220 };

export const ClarificationPanel: React.FC<ClarificationPanelProps> = ({
  questions,
  onSubmit,
  isLoading,
}) => {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!questions || questions.length === 0) return null;

  const isAnswered = (id: string) => Boolean(answers[id]?.trim());
  const allAnswered = questions.every((q) => isAnswered(q.question_id));
  const answeredCount = questions.filter((q) => isAnswered(q.question_id)).length;
  const progressPct = (answeredCount / questions.length) * 100;

  const handleChange = (id: string, val: string) => {
    setAnswers((p) => ({ ...p, [id]: val }));
    if (submitError) setSubmitError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    try {
      await onSubmit(answers);
      setAnswers({});
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit clarifications.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center gap-4 py-16 px-8">
        <div
          className="w-10 h-10 rounded-full border-2 animate-spin"
          style={{
            borderColor: 'var(--color-border)',
            borderTopColor: 'var(--color-primary)',
          }}
        />
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          Processing clarifications…
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col max-h-full">
      {/* Header */}
      <div
        className="px-6 py-5"
        style={{ borderBottom: '1px solid var(--color-border)' }}
      >
        <div className="flex items-start gap-3">
          <div
            className="flex items-center justify-center flex-shrink-0"
            style={{
              width: 40,
              height: 40,
              borderRadius: 'var(--radius-md)',
              backgroundColor: 'var(--color-warning-subtle)',
              color: 'var(--color-warning-text)',
              border: '1px solid var(--color-warning-subtle-border)',
            }}
          >
            <HelpCircle className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <h3
              id="clarification-title"
              className="text-base font-semibold"
              style={{ color: 'var(--color-text-primary)', letterSpacing: '-0.01em' }}
            >
              Clarification required
            </h3>
            <p
              className="text-sm mt-0.5"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Answer these questions to improve requirement quality.
            </p>
          </div>
          <div
            className="badge badge-warning flex-shrink-0"
            aria-live="polite"
          >
            {answeredCount}/{questions.length}
          </div>
        </div>

        {/* Progress bar */}
        <div
          className="h-1 mt-4 overflow-hidden"
          style={{
            backgroundColor: 'var(--color-border)',
            borderRadius: 'var(--radius-full)',
          }}
        >
          <motion.div
            className="h-full"
            style={{
              backgroundColor: 'var(--color-warning)',
              borderRadius: 'var(--radius-full)',
            }}
            animate={{ width: `${progressPct}%` }}
            transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
          />
        </div>
      </div>

      {/* Scrollable body */}
      <form
        onSubmit={handleSubmit}
        className="flex-1 overflow-y-auto px-6 py-5 space-y-3"
      >
        <AnimatePresence initial={false}>
          {questions.map((q, idx) => {
            const answered = isAnswered(q.question_id);
            return (
              <motion.div
                key={q.question_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ ...spring, delay: idx * 0.04 }}
                className="p-4"
                style={{
                  backgroundColor: answered
                    ? 'var(--color-success-subtle)'
                    : 'var(--color-surface-sunken)',
                  border: answered
                    ? '1px solid var(--color-success-subtle-border)'
                    : '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-lg)',
                  transition: 'background-color 150ms ease, border-color 150ms ease',
                }}
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <label
                    htmlFor={`cl-${q.question_id}`}
                    className="text-sm font-medium leading-snug flex-1"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    <span
                      className="mr-2 font-semibold"
                      style={{ color: 'var(--color-warning-text)' }}
                    >
                      {idx + 1}.
                    </span>
                    {q.question}
                  </label>
                  <AnimatePresence>
                    {answered && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.6 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.6 }}
                        transition={spring}
                      >
                        <CheckCircle2
                          className="w-4 h-4 flex-shrink-0"
                          style={{ color: 'var(--color-success)' }}
                        />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>

                {q.context && (
                  <p
                    className="text-xs mb-2"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    <span
                      className="font-semibold"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      Context:{' '}
                    </span>
                    {q.context}
                  </p>
                )}

                {q.required_clarity && q.required_clarity.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {q.required_clarity.map((hint, hi) => (
                      <span key={hi} className="badge badge-primary">
                        {hint}
                      </span>
                    ))}
                  </div>
                )}

                <textarea
                  id={`cl-${q.question_id}`}
                  value={answers[q.question_id] || ''}
                  onChange={(e) => handleChange(q.question_id, e.target.value)}
                  placeholder="Your clarification…"
                  rows={3}
                  className="input-base"
                  disabled={isLoading}
                  aria-invalid={!answered}
                  style={{ resize: 'vertical' }}
                />
              </motion.div>
            );
          })}
        </AnimatePresence>

        <AnimatePresence>
          {submitError && (
            <motion.div
              initial={{ opacity: 0, y: -4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              className="flex items-start gap-2 p-3 text-sm"
              style={{
                backgroundColor: 'var(--color-danger-subtle)',
                border: '1px solid var(--color-danger-subtle-border)',
                color: 'var(--color-danger-text)',
                borderRadius: 'var(--radius-md)',
              }}
              role="alert"
            >
              <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
              <span>{submitError}</span>
            </motion.div>
          )}
        </AnimatePresence>
      </form>

      {/* Footer */}
      <div
        className="px-6 py-4 flex items-center justify-between gap-3"
        style={{ borderTop: '1px solid var(--color-border)' }}
      >
        <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
          {allAnswered
            ? 'All answered — ready to submit.'
            : `${questions.length - answeredCount} remaining`}
        </p>
        <motion.button
          type="button"
          onClick={handleSubmit}
          disabled={!allAnswered || isLoading}
          whileHover={allAnswered ? { y: -1 } : undefined}
          whileTap={allAnswered ? { scale: 0.98 } : undefined}
          className="btn-primary"
        >
          <Sparkles className="w-4 h-4" />
          Submit clarifications
        </motion.button>
      </div>
    </div>
  );
};
