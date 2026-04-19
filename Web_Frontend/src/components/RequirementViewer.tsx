import React, { useState } from 'react';
import { Download, Copy, CheckCircle } from 'lucide-react';
import { FormalizedRequirement, ExportRequest } from '@/types/index';
import { LoadingSpinner } from './Loading';

interface RequirementViewerProps {
  requirements: FormalizedRequirement | null;
  sessionId: string | null;
  isLoading: boolean;
  onExport?: (request: ExportRequest) => Promise<void>;
}

export const RequirementViewer: React.FC<RequirementViewerProps> = ({
  requirements,
  sessionId,
  isLoading,
  onExport,
}) => {
  const [exportTarget, setExportTarget] = useState<'jira' | 'trello' | 'pdf'>(
    'jira'
  );
  const [isExporting, setIsExporting] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  if (isLoading) {
    return <LoadingSpinner message="Loading requirements..." />;
  }

  if (!requirements || requirements.total_requirements === 0) {
    return (
      <div className="card p-8 text-center">
        <CheckCircle className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
        <h3 className="font-semibold text-neutral-600 mb-2">
          No Requirements Yet
        </h3>
        <p className="text-sm text-neutral-500">
          Run an analysis to generate ISO 29148 formatted requirements.
        </p>
      </div>
    );
  }

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleExport = async () => {
    if (!sessionId || !onExport) return;

    setIsExporting(true);
    try {
      await onExport({
        session_id: sessionId,
        target: exportTarget,
      });
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="space-y-4 animate-slide-in">
      {/* Header */}
      <div className="card p-6 flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-neutral-900">
            Formalized Requirements
          </h3>
          <p className="text-sm text-neutral-500 mt-1">
            {requirements.total_requirements} requirement{
              requirements.total_requirements !== 1 ? 's' : ''
            } ready for export
          </p>
        </div>
        {requirements.ready_for_export && (
          <span className="px-3 py-1 bg-success/10 text-success text-xs font-medium rounded-full">
            Ready to Export
          </span>
        )}
      </div>

      {/* Export Controls */}
      <div className="card p-4 flex flex-col md:flex-row gap-3 items-stretch md:items-center">
        <select
          value={exportTarget}
          onChange={(e) => setExportTarget(e.target.value as any)}
          className="input-base text-sm"
          disabled={isExporting}
        >
          <option value="jira">Export to Jira</option>
          <option value="trello">Export to Trello</option>
          <option value="pdf">Download as PDF</option>
        </select>
        <button
          onClick={handleExport}
          disabled={isExporting || !requirements.ready_for_export}
          className="btn-primary flex items-center gap-2"
        >
          <Download className="w-4 h-4" />
          {isExporting ? 'Exporting...' : 'Export'}
        </button>
      </div>

      {/* Requirements List */}
      <div className="space-y-3">
        {(requirements.requirements ?? requirements.iso_requirements ?? []).map((req) => {
          const reqId = req.id || req.requirement_id || 'REQ-' + Math.random().toString(36).substr(2, 9);
          return (
          <div key={reqId} className="card p-4 space-y-3 hover:shadow-md transition-shadow">
            {/* ID & Title */}
            <div className="flex items-start justify-between gap-3">
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-neutral-100 text-neutral-900 px-2 py-1 rounded font-mono font-semibold">
                    {reqId}
                  </code>
                  <h4 className="font-semibold text-neutral-900">{req.title}</h4>
                </div>
              </div>
              <button
                onClick={() =>
                  handleCopy(reqId, `${reqId}: ${req.shall_statement}`)
                }
                className="btn-ghost"
                title="Copy"
              >
                {copiedId === reqId ? (
                  <CheckCircle className="w-4 h-4 text-success" />
                ) : (
                  <Copy className="w-4 h-4 text-neutral-500" />
                )}
              </button>
            </div>

            {/* Shall Statement */}
            <div>
              <p className="text-xs font-medium text-neutral-600 mb-1">
                Requirement
              </p>
              <p className="text-sm text-neutral-900 italic">
                "{req.shall_statement}"
              </p>
            </div>

            {/* Rationale */}
            <div>
              <p className="text-xs font-medium text-neutral-600 mb-1">
                Rationale
              </p>
              <p className="text-sm text-neutral-700">{req.rationale}</p>
            </div>

            {/* Acceptance Criteria */}
            {req.acceptance_criteria.length > 0 && (
              <div>
                <p className="text-xs font-medium text-neutral-600 mb-2">
                  Acceptance Criteria
                </p>
                <ul className="space-y-1">
                  {req.acceptance_criteria.map((criterion, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-neutral-700 flex gap-2"
                    >
                      <span className="text-primary-600 flex-shrink-0">✓</span>
                      {criterion}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Footer */}
            <div className="flex items-center gap-4 pt-2 border-t border-neutral-200">
              <span className="text-xs text-neutral-500">
                Priority:{' '}
                <span className="font-medium uppercase text-neutral-700">
                  {req.priority}
                </span>
              </span>
              <span className="text-xs text-neutral-500">
                Status:{' '}
                <span className="font-medium uppercase text-neutral-700">
                  {req.status}
                </span>
              </span>
            </div>
          </div>
        );
        })}
      </div>
    </div>
  );
};
