import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Check,
  Edit2,
  Sparkles,
  X,
  Plus,
  Trash2,
  Loader2,
} from 'lucide-react';
import { ISORequirement } from '../types';

interface RequirementCardProps {
  requirement: ISORequirement;
  completeness_score: number;
  /**
   * Smell-based quality score (0.0-1.0). When present, this is the metric
   * displayed in the card meter — it reflects how many smells target this
   * requirement's text, making it actionable (cards that drag the cumulative
   * score down become visible). Falls back to completeness_score when absent
   * so older sessions still render.
   */
  quality_score?: number;
  is_highlighted?: boolean;
  is_focused?: boolean;
  onUpdate?: (req: ISORequirement) => void;
  onClarify?: (req: ISORequirement, context: string) => void | Promise<void>;
}

const spring = { type: 'spring' as const, damping: 24, stiffness: 220 };

type Variant = 'success' | 'warning' | 'danger' | 'primary' | 'neutral';

const variantBadgeClass: Record<Variant, string> = {
  success: 'badge badge-success',
  warning: 'badge badge-warning',
  danger: 'badge badge-danger',
  primary: 'badge badge-primary',
  neutral: 'badge badge-neutral',
};

function priorityVariant(p: string | undefined): Variant {
  const v = (p || 'medium').toLowerCase();
  if (v === 'high') return 'danger';
  if (v === 'low') return 'success';
  return 'warning';
}

function statusForScore(pct: number): { label: string; variant: Variant; colorVar: string } {
  if (pct >= 80)
    return {
      label: 'ISO verified',
      variant: 'success',
      colorVar: 'var(--color-success)',
    };
  if (pct >= 50)
    return {
      label: 'Draft',
      variant: 'warning',
      colorVar: 'var(--color-warning)',
    };
  return {
    label: 'Incomplete',
    variant: 'danger',
    colorVar: 'var(--color-danger)',
  };
}

// Normalize any case/format to the canonical 'High' | 'Medium' | 'Low' values
// used by the edit-mode <select>.
function normalizePriority(p: ISORequirement['priority']): 'High' | 'Medium' | 'Low' {
  const v = (p || 'medium').toString().toLowerCase();
  if (v === 'high') return 'High';
  if (v === 'low') return 'Low';
  return 'Medium';
}

export const RequirementCard: React.FC<RequirementCardProps> = ({
  requirement,
  completeness_score,
  quality_score,
  is_highlighted = false,
  is_focused = false,
  onUpdate,
  onClarify,
}) => {
  // Prefer the smell-based quality score when available — it is the same
  // metric the cumulative feed footer reports, so a low-scoring card clearly
  // points the user at what is dragging the overall score down. Fall back to
  // completeness_score for backwards compatibility with older backends.
  const displayScore = quality_score ?? completeness_score;
  const pct = Math.round(Math.min(Math.max(displayScore, 0), 1) * 100);
  const status = statusForScore(pct);
  const priority = priorityVariant(requirement.priority);

  // --- Edit mode state ---
  const [isEditing, setIsEditing] = useState(false);
  const [draft, setDraft] = useState<ISORequirement>(requirement);

  // --- Clarify panel state ---
  const [isClarifyOpen, setIsClarifyOpen] = useState(false);
  const [clarifyText, setClarifyText] = useState('');
  const [isClarifyPending, setIsClarifyPending] = useState(false);

  const enterEdit = () => {
    // Snapshot the current requirement so Cancel can revert cleanly even if
    // the parent mutated the prop in the meantime.
    setDraft({
      ...requirement,
      acceptance_criteria: [...(requirement.acceptance_criteria || [])],
    });
    setIsEditing(true);
  };

  const cancelEdit = () => {
    setDraft(requirement);
    setIsEditing(false);
  };

  const saveEdit = () => {
    onUpdate?.(draft);
    setIsEditing(false);
  };

  const updateCriterion = (idx: number, value: string) => {
    setDraft((d) => {
      const next = [...(d.acceptance_criteria || [])];
      next[idx] = value;
      return { ...d, acceptance_criteria: next };
    });
  };

  const addCriterion = () => {
    setDraft((d) => ({
      ...d,
      acceptance_criteria: [...(d.acceptance_criteria || []), ''],
    }));
  };

  const deleteCriterion = (idx: number) => {
    setDraft((d) => {
      const next = [...(d.acceptance_criteria || [])];
      next.splice(idx, 1);
      return { ...d, acceptance_criteria: next };
    });
  };

  const submitClarify = async () => {
    if (!clarifyText.trim() || !onClarify) return;
    setIsClarifyPending(true);
    try {
      await onClarify(requirement, clarifyText.trim());
      setClarifyText('');
      setIsClarifyOpen(false);
    } finally {
      setIsClarifyPending(false);
    }
  };

  const borderColor = is_focused
    ? 'var(--color-primary)'
    : is_highlighted
      ? 'var(--color-warning)'
      : 'var(--color-border)';

  const accentBg = is_focused
    ? 'var(--color-primary-subtle)'
    : is_highlighted
      ? 'var(--color-warning-subtle)'
      : 'var(--color-surface)';

  // Small shared style for icon-only header action buttons
  const iconBtnStyle: React.CSSProperties = {
    width: 28,
    height: 28,
    borderRadius: 'var(--radius-md)',
    border: '1px solid var(--color-border)',
    backgroundColor: 'var(--color-surface-raised)',
    color: 'var(--color-text-secondary)',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    transition: 'background-color 120ms ease, color 120ms ease',
  };

  return (
    <motion.article
      layout
      whileHover={{ y: isEditing ? 0 : -2 }}
      transition={spring}
      className="p-4 flex flex-col gap-3"
      style={{
        backgroundColor: accentBg,
        border: `1px solid ${borderColor}`,
        borderRadius: 'var(--radius-lg)',
        boxShadow: is_focused ? 'var(--shadow-md)' : 'var(--shadow-sm)',
      }}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2 flex-wrap min-w-0">
          <code
            className="text-xs font-mono font-semibold px-2 py-0.5"
            style={{
              backgroundColor: 'var(--color-primary-subtle)',
              color: 'var(--color-primary-text)',
              border: '1px solid var(--color-primary-subtle-border)',
              borderRadius: 'var(--radius-sm)',
              letterSpacing: '0.02em',
            }}
          >
            {requirement.requirement_id || requirement.id || 'REQ'}
          </code>
          <motion.span
            key={status.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className={variantBadgeClass[status.variant]}
          >
            {status.label}
          </motion.span>
        </div>

        {/* Completeness + actions */}
        <div className="flex-shrink-0 flex items-center gap-2">
          <div
            className="w-16 h-1.5 overflow-hidden"
            style={{
              backgroundColor: 'var(--color-border)',
              borderRadius: 'var(--radius-full)',
            }}
          >
            <motion.div
              className="h-full"
              style={{
                backgroundColor: status.colorVar,
                borderRadius: 'var(--radius-full)',
              }}
              initial={{ width: 0 }}
              animate={{ width: `${pct}%` }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            />
          </div>
          <span
            className="text-xs font-semibold font-mono tabular-nums"
            style={{ color: status.colorVar }}
          >
            {pct}%
          </span>

          {/* Action buttons */}
          {!isEditing ? (
            <div className="flex items-center gap-1 ml-1">
              {onUpdate && (
                <button
                  type="button"
                  onClick={enterEdit}
                  aria-label="Edit requirement"
                  title="Edit"
                  style={iconBtnStyle}
                >
                  <Edit2 className="w-3.5 h-3.5" />
                </button>
              )}
              {onClarify && (
                <button
                  type="button"
                  onClick={() => setIsClarifyOpen((v) => !v)}
                  aria-label="Clarify requirement"
                  aria-expanded={isClarifyOpen}
                  title="Clarify"
                  style={{
                    ...iconBtnStyle,
                    backgroundColor: isClarifyOpen
                      ? 'var(--color-primary-subtle)'
                      : iconBtnStyle.backgroundColor,
                    color: isClarifyOpen
                      ? 'var(--color-primary-text)'
                      : iconBtnStyle.color,
                    borderColor: isClarifyOpen
                      ? 'var(--color-primary-subtle-border)'
                      : 'var(--color-border)',
                  }}
                >
                  {isClarifyPending ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Sparkles className="w-3.5 h-3.5" />
                  )}
                </button>
              )}
            </div>
          ) : (
            <div className="flex items-center gap-1 ml-1">
              <button
                type="button"
                onClick={saveEdit}
                aria-label="Save changes"
                title="Save"
                style={{
                  ...iconBtnStyle,
                  backgroundColor: 'var(--color-primary)',
                  borderColor: 'var(--color-primary)',
                  color: 'var(--color-primary-contrast, #fff)',
                }}
              >
                <Check className="w-3.5 h-3.5" />
              </button>
              <button
                type="button"
                onClick={cancelEdit}
                aria-label="Cancel editing"
                title="Cancel"
                style={iconBtnStyle}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Body: view vs edit */}
      {!isEditing ? (
        <>
          {/* Title */}
          <h4
            className="text-sm font-semibold leading-snug"
            style={{ color: 'var(--color-text-primary)' }}
          >
            {requirement.title}
          </h4>

          {/* Shall statement */}
          <div
            className="px-3 py-2.5"
            style={{
              backgroundColor: 'var(--color-primary-subtle)',
              borderLeft: '3px solid var(--color-primary)',
              borderRadius: '0 var(--radius-md) var(--radius-md) 0',
            }}
          >
            <p
              className="text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Shall
            </p>
            <p
              className="text-sm leading-relaxed italic"
              style={{ color: 'var(--color-primary-text)' }}
            >
              “{requirement.shall_statement}”
            </p>
          </div>

          {/* Rationale */}
          {requirement.rationale && (
            <div>
              <p
                className="text-xs font-semibold uppercase tracking-wider mb-1"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                Rationale
              </p>
              <p
                className="text-sm leading-relaxed"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                {requirement.rationale}
              </p>
            </div>
          )}

          {/* Acceptance criteria */}
          {requirement.acceptance_criteria &&
            requirement.acceptance_criteria.length > 0 && (
              <div>
                <p
                  className="text-xs font-semibold uppercase tracking-wider mb-1.5"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Acceptance criteria
                </p>
                <ul className="space-y-1.5">
                  {requirement.acceptance_criteria.map((c, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-2 text-sm"
                      style={{ color: 'var(--color-text-secondary)' }}
                    >
                      <Check
                        className="w-3.5 h-3.5 mt-0.5 flex-shrink-0"
                        style={{ color: 'var(--color-success)' }}
                      />
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

          {/* Footer */}
          <div
            className="flex items-center gap-2 pt-2 flex-wrap"
            style={{ borderTop: '1px solid var(--color-border)' }}
          >
            <span className={variantBadgeClass[priority]}>
              {(requirement.priority || 'medium').toUpperCase()}
            </span>
            {requirement.category && (
              <span className="badge badge-primary">
                {requirement.category.replace(/-/g, ' ')}
              </span>
            )}
            {requirement.status && (
              <span className="badge badge-neutral">
                {requirement.status.replace(/_/g, ' ')}
              </span>
            )}
          </div>
        </>
      ) : (
        <div className="flex flex-col gap-3">
          {/* Title input */}
          <div>
            <label
              className="block text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Title
            </label>
            <input
              type="text"
              className="input-base w-full"
              value={draft.title}
              onChange={(e) =>
                setDraft((d) => ({ ...d, title: e.target.value }))
              }
              placeholder="Requirement title"
            />
          </div>

          {/* Shall statement */}
          <div>
            <label
              className="block text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Shall statement
            </label>
            <textarea
              className="input-base w-full"
              rows={3}
              value={draft.shall_statement}
              onChange={(e) =>
                setDraft((d) => ({ ...d, shall_statement: e.target.value }))
              }
              placeholder="The system shall…"
            />
          </div>

          {/* Rationale */}
          <div>
            <label
              className="block text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Rationale
            </label>
            <textarea
              className="input-base w-full"
              rows={2}
              value={draft.rationale || ''}
              onChange={(e) =>
                setDraft((d) => ({ ...d, rationale: e.target.value }))
              }
              placeholder="Why is this requirement necessary?"
            />
          </div>

          {/* Acceptance criteria editor */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label
                className="block text-xs font-semibold uppercase tracking-wider"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                Acceptance criteria
              </label>
              <button
                type="button"
                onClick={addCriterion}
                className="inline-flex items-center gap-1 text-xs font-medium px-2 py-1"
                style={{
                  backgroundColor: 'var(--color-primary-subtle)',
                  color: 'var(--color-primary-text)',
                  border: '1px solid var(--color-primary-subtle-border)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <Plus className="w-3 h-3" />
                Add criterion
              </button>
            </div>
            <div className="space-y-1.5">
              {(draft.acceptance_criteria || []).map((c, i) => (
                <div key={i} className="flex items-center gap-2">
                  <input
                    type="text"
                    className="input-base flex-1 min-w-0"
                    value={c}
                    onChange={(e) => updateCriterion(i, e.target.value)}
                    placeholder={`Criterion ${i + 1}`}
                  />
                  <button
                    type="button"
                    onClick={() => deleteCriterion(i)}
                    aria-label={`Delete criterion ${i + 1}`}
                    title="Delete criterion"
                    style={{
                      ...iconBtnStyle,
                      color: 'var(--color-danger)',
                    }}
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
              {(draft.acceptance_criteria || []).length === 0 && (
                <p
                  className="text-xs italic"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  No criteria yet. Click “Add criterion” to create one.
                </p>
              )}
            </div>
          </div>

          {/* Priority select */}
          <div>
            <label
              className="block text-xs font-semibold uppercase tracking-wider mb-1"
              style={{ color: 'var(--color-text-secondary)' }}
            >
              Priority
            </label>
            <select
              className="input-base w-full"
              value={normalizePriority(draft.priority)}
              onChange={(e) =>
                setDraft((d) => ({
                  ...d,
                  priority: e.target.value as 'High' | 'Medium' | 'Low',
                }))
              }
            >
              <option value="High">High</option>
              <option value="Medium">Medium</option>
              <option value="Low">Low</option>
            </select>
          </div>
        </div>
      )}

      {/* Clarify panel */}
      <AnimatePresence initial={false}>
        {isClarifyOpen && !isEditing && (
          <motion.div
            key="clarify-panel"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
            style={{ overflow: 'hidden' }}
          >
            <div
              className="mt-1 p-3 flex flex-col gap-2"
              style={{
                backgroundColor: 'var(--color-surface-sunken)',
                border: '1px solid var(--color-border)',
                borderRadius: 'var(--radius-md)',
              }}
            >
              <div className="flex items-center gap-1.5">
                <Sparkles
                  className="w-3.5 h-3.5"
                  style={{ color: 'var(--color-primary)' }}
                />
                <p
                  className="text-xs font-semibold uppercase tracking-wider"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Clarify
                </p>
              </div>
              <textarea
                className="input-base w-full"
                rows={3}
                value={clarifyText}
                onChange={(e) => setClarifyText(e.target.value)}
                placeholder="Add context to improve this requirement…"
                disabled={isClarifyPending}
              />
              <div className="flex items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => {
                    setClarifyText('');
                    setIsClarifyOpen(false);
                  }}
                  disabled={isClarifyPending}
                  className="text-xs font-medium px-3 py-1.5"
                  style={{
                    backgroundColor: 'transparent',
                    color: 'var(--color-text-secondary)',
                    border: '1px solid var(--color-border)',
                    borderRadius: 'var(--radius-md)',
                  }}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={submitClarify}
                  disabled={isClarifyPending || !clarifyText.trim()}
                  className="inline-flex items-center gap-1.5 text-xs font-semibold px-3 py-1.5"
                  style={{
                    backgroundColor: 'var(--color-primary)',
                    color: 'var(--color-primary-contrast, #fff)',
                    border: '1px solid var(--color-primary)',
                    borderRadius: 'var(--radius-md)',
                    opacity:
                      isClarifyPending || !clarifyText.trim() ? 0.6 : 1,
                  }}
                >
                  {isClarifyPending ? (
                    <>
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      Submitting…
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      Submit
                    </>
                  )}
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.article>
  );
};

export default RequirementCard;
