import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  RequirementInput,
  ClarificationPanel,
  RequirementViewer,
  VoiceRecorder,
  SmellMeter,
  RequirementFeed,
  WaveformVisualizer,
  DocumentUpload,
} from '@/components/index';
import { useRequirementStore, setupWebSocketListeners } from '@/store/requirementStore';
import { generateSessionId } from '@/utils/helpers';
import { apiClient } from '@/services/api';
import { ExportRequest } from '@/types/index';
import {
  Cpu,
  Sparkles,
  Activity,
  Moon,
  Sun,
  FileSearch,
  Mic,
  FileUp,
  X,
} from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

// ── Motion presets ─────────────────────────────────────────────
const spring = { type: 'spring' as const, damping: 24, stiffness: 220 };
const easeOut = { duration: 0.35, ease: [0.16, 1, 0.3, 1] as [number, number, number, number] };

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: easeOut },
};

const stagger = {
  show: { transition: { staggerChildren: 0.08 } },
};

// ── Status pill for analysis state ──────────────────────────────
const StatusPill: React.FC<{ status: string | undefined }> = ({ status }) => {
  if (!status || status === 'pending') return null;
  const map: Record<string, { label: string; variant: string }> = {
    analyzing: { label: 'Analyzing', variant: 'badge-primary' },
    needs_clarification: { label: 'Needs Input', variant: 'badge-warning' },
    formal_draft: { label: 'Draft Ready', variant: 'badge-primary' },
    clarified: { label: 'Clarified', variant: 'badge-success' },
    export_ready: { label: 'Export Ready', variant: 'badge-success' },
  };
  const entry = map[status];
  if (!entry) return null;
  return (
    <motion.span
      key={status}
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={spring}
      className={`badge ${entry.variant}`}
    >
      {entry.label}
    </motion.span>
  );
};

// ── Theme toggle ────────────────────────────────────────────────
const ThemeToggle: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  return (
    <button
      type="button"
      onClick={toggleTheme}
      className="btn-icon"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <AnimatePresence mode="wait" initial={false}>
        {isDark ? (
          <motion.span
            key="sun"
            initial={{ rotate: -45, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: 45, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ display: 'inline-flex' }}
          >
            <Sun className="w-4 h-4" />
          </motion.span>
        ) : (
          <motion.span
            key="moon"
            initial={{ rotate: 45, opacity: 0 }}
            animate={{ rotate: 0, opacity: 1 }}
            exit={{ rotate: -45, opacity: 0 }}
            transition={{ duration: 0.2 }}
            style={{ display: 'inline-flex' }}
          >
            <Moon className="w-4 h-4" />
          </motion.span>
        )}
      </AnimatePresence>
    </button>
  );
};

// ── Zone heading ────────────────────────────────────────────────
const ZoneHeading: React.FC<{
  icon: React.ReactNode;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
}> = ({ icon, title, subtitle, action }) => (
  <div className="flex items-start justify-between gap-3">
    <div className="flex items-start gap-3 min-w-0">
      <div
        className="flex items-center justify-center flex-shrink-0"
        style={{
          width: 36,
          height: 36,
          borderRadius: 'var(--radius-md)',
          backgroundColor: 'var(--color-primary-subtle)',
          color: 'var(--color-primary-text)',
          border: '1px solid var(--color-primary-subtle-border)',
        }}
      >
        {icon}
      </div>
      <div className="min-w-0">
        <h2
          className="text-base font-semibold"
          style={{ color: 'var(--color-text-primary)', letterSpacing: '-0.01em' }}
        >
          {title}
        </h2>
        {subtitle && (
          <p className="text-xs mt-0.5" style={{ color: 'var(--color-text-secondary)' }}>
            {subtitle}
          </p>
        )}
      </div>
    </div>
    {action && <div className="flex-shrink-0">{action}</div>}
  </div>
);

// ═══════════════════════════════════════════════════════════════
export const Dashboard: React.FC = () => {
  const {
    currentSession,
    analysisState,
    formalizedRequirements,
    loading,
    incrementalLoading,
    setSession,
    analyzeRequirements,
    analyzeRequirementsIncremental,
    clarifyRequirements,
    addNotification,
  } = useRequirementStore();

  useEffect(() => {
    if (!currentSession) setSession(generateSessionId());
    setupWebSocketListeners();
  }, [currentSession, setSession]);

  const handleClarify = async (clarifications: Record<string, string>) => {
    await clarifyRequirements(clarifications);
  };

  const handleExport = async (request: ExportRequest) => {
    try {
      const result = await apiClient.exportRequirements(request);
      addNotification({
        type: result.status === 'success' ? 'success' : 'error',
        message:
          result.status === 'success'
            ? `Exported ${result.ticket_ids?.length ?? 0} requirements to ${request.target}.`
            : `Export to ${request.target} failed.`,
      });
    } catch (error: unknown) {
      addNotification({ type: 'error', message: apiClient.getErrorMessage(error) });
    }
  };

  const hasRequirements = (formalizedRequirements?.total_requirements ?? 0) > 0;
  const interruptNeeded =
    analysisState?.interrupt_needed && analysisState.clarification_questions;

  return (
    <div
      className="min-h-screen flex flex-col"
      style={{ backgroundColor: 'var(--color-bg)' }}
    >
      {/* ── Header ──────────────────────────────────────────── */}
      <motion.header
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={easeOut}
        className="sticky top-0 z-40"
        style={{
          backgroundColor: 'color-mix(in srgb, var(--color-surface) 85%, transparent)',
          backdropFilter: 'saturate(180%) blur(12px)',
          WebkitBackdropFilter: 'saturate(180%) blur(12px)',
          borderBottom: '1px solid var(--color-border)',
        }}
      >
        <div className="px-6 py-3 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-3 min-w-0">
            <div
              className="flex items-center justify-center flex-shrink-0"
              style={{
                width: 36,
                height: 36,
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--color-primary)',
                color: '#FFFFFF',
                boxShadow: 'var(--shadow-sm)',
              }}
            >
              <Cpu className="w-4 h-4" />
            </div>
            <div className="min-w-0">
              <div
                className="text-sm font-semibold leading-tight"
                style={{ color: 'var(--color-text-primary)', letterSpacing: '-0.01em' }}
              >
                RE Tool
              </div>
              <div
                className="text-xs leading-tight"
                style={{ color: 'var(--color-text-muted)' }}
              >
                ISO 29148 Multi-Agent
              </div>
            </div>
          </div>

          {/* Status area */}
          <div className="flex items-center gap-2 flex-1 justify-center">
            {incrementalLoading && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                className="badge badge-primary"
              >
                <motion.span
                  className="inline-block w-1.5 h-1.5 rounded-full"
                  style={{ backgroundColor: 'var(--color-primary)' }}
                  animate={{ opacity: [0.4, 1, 0.4] }}
                  transition={{ duration: 1.4, repeat: Infinity }}
                />
                Analyzing
              </motion.div>
            )}
            <StatusPill status={analysisState?.status} />
          </div>

          {/* Session + toggle */}
          <div className="flex items-center gap-2">
            {currentSession && (
              <div
                className="hidden md:flex items-center gap-1.5 px-2.5 py-1 rounded-md"
                style={{
                  backgroundColor: 'var(--color-surface-raised)',
                  border: '1px solid var(--color-border)',
                }}
              >
                <Activity className="w-3 h-3" style={{ color: 'var(--color-text-muted)' }} />
                <span
                  className="text-xs font-mono"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  {currentSession.substring(0, 8)}
                </span>
              </div>
            )}
            <ThemeToggle />
          </div>
        </div>
      </motion.header>

      {/* ── Main grid ──────────────────────────────────────── */}
      <motion.main
        variants={stagger}
        initial="hidden"
        animate="show"
        className="flex-1 p-5 grid gap-5"
        style={{
          gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1.15fr)',
          gridTemplateRows: 'auto 1fr',
          minHeight: 0,
        }}
      >
        {/* ─ LEFT: Input zone (full height) ─ */}
        <motion.section
          variants={fadeUp}
          className="card flex flex-col gap-5 p-5 overflow-y-auto"
          style={{ gridRow: '1 / 3' }}
        >
          <ZoneHeading
            icon={<Sparkles className="w-4 h-4" />}
            title="Input"
            subtitle="Paste, speak, or upload a requirement."
          />

          <div>
            <RequirementInput
              onAnalyze={analyzeRequirements}
              onIncrementalAnalyze={analyzeRequirementsIncremental}
              isLoading={loading}
            />
          </div>

          {/* Voice block */}
          <div
            className="p-4 flex flex-col gap-3"
            style={{
              backgroundColor: 'var(--color-surface-sunken)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div className="flex items-center gap-2">
              <Mic className="w-3.5 h-3.5" style={{ color: 'var(--color-text-secondary)' }} />
              <span
                className="text-xs font-semibold uppercase tracking-wide"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                Voice capture
              </span>
            </div>
            <WaveformVisualizer isRecording={false} />
            <VoiceRecorder sessionId={currentSession} isLoading={loading} />
          </div>

          {/* Document block */}
          <div
            className="p-4 flex flex-col gap-3"
            style={{
              backgroundColor: 'var(--color-surface-sunken)',
              border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-lg)',
            }}
          >
            <div className="flex items-center gap-2">
              <FileUp className="w-3.5 h-3.5" style={{ color: 'var(--color-text-secondary)' }} />
              <span
                className="text-xs font-semibold uppercase tracking-wide"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                Document upload
              </span>
            </div>
            <DocumentUpload isLoading={loading} />
          </div>
        </motion.section>

        {/* ─ RIGHT TOP: Quality meter ─ */}
        <motion.section variants={fadeUp} className="card p-5 flex flex-col gap-4">
          <ZoneHeading
            icon={<FileSearch className="w-4 h-4" />}
            title="Intelligence"
            subtitle="Live quality analysis and ISO 29148 specs."
            action={
              formalizedRequirements && formalizedRequirements.total_requirements > 0 ? (
                <motion.span
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="badge badge-primary"
                >
                  {formalizedRequirements.total_requirements} spec
                  {formalizedRequirements.total_requirements !== 1 ? 's' : ''}
                </motion.span>
              ) : null
            }
          />

          {analysisState ? (
            <SmellMeter
              smellScore={analysisState.analysis_summary?.smell_score ?? 0}
              label="Requirement Quality"
            />
          ) : (
            <div
              className="p-4 text-center"
              style={{
                backgroundColor: 'var(--color-surface-sunken)',
                border: '1px dashed var(--color-border)',
                borderRadius: 'var(--radius-lg)',
                color: 'var(--color-text-secondary)',
                fontSize: 13,
              }}
            >
              Submit a requirement to see quality metrics.
            </div>
          )}
        </motion.section>

        {/* ─ RIGHT BOTTOM: Requirements feed + export ─ */}
        <motion.section
          variants={fadeUp}
          className="card p-5 flex flex-col gap-4 overflow-hidden min-h-0"
        >
          <div className="flex-1 min-h-0 overflow-y-auto pr-1">
            <RequirementFeed
              requirements={formalizedRequirements}
              isLoading={loading && !formalizedRequirements}
            />
          </div>

          <AnimatePresence>
            {hasRequirements && (
              <motion.div
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 8 }}
                transition={spring}
                style={{ borderTop: '1px solid var(--color-border)', paddingTop: 16 }}
              >
                <RequirementViewer
                  requirements={formalizedRequirements}
                  sessionId={currentSession}
                  isLoading={loading}
                  onExport={handleExport}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.section>
      </motion.main>

      {/* ── Clarification modal ─────────────────────────────── */}
      <AnimatePresence>
        {interruptNeeded && (
          <>
            <motion.div
              key="backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="fixed inset-0 z-50"
              style={{
                backgroundColor: 'var(--color-overlay)',
                backdropFilter: 'blur(4px)',
                WebkitBackdropFilter: 'blur(4px)',
              }}
            />
            <motion.div
              key="panel"
              initial={{ opacity: 0, scale: 0.95, y: 16 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.97, y: 10 }}
              transition={spring}
              className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
              role="dialog"
              aria-modal="true"
              aria-labelledby="clarification-title"
            >
              <div
                className="w-full max-w-2xl max-h-[88vh] overflow-hidden flex flex-col"
                style={{
                  backgroundColor: 'var(--color-surface)',
                  border: '1px solid var(--color-border)',
                  borderRadius: 'var(--radius-xl)',
                  boxShadow: 'var(--shadow-xl)',
                }}
              >
                <ClarificationPanel
                  questions={analysisState!.clarification_questions}
                  onSubmit={handleClarify}
                  isLoading={loading}
                />
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

// Used so eslint doesn't complain about the unused X import in some lint configs;
// X is reserved for future modal close actions.
void X;
