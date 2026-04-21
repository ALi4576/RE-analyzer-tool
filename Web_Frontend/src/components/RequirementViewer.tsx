import React, { useState } from 'react';
import { Download } from 'lucide-react';
import { FormalizedRequirement, ExportRequest } from '@/types/index';

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api';

type ExportTarget = 'jira' | 'trello' | 'pdf';

interface RequirementViewerProps {
  requirements: FormalizedRequirement | null;
  sessionId: string | null;
  isLoading: boolean;
  onExport?: (request: ExportRequest) => Promise<void>;
}

/**
 * Renders export controls once requirements are ready.
 * The actual requirement list rendering lives in <RequirementFeed />.
 */
export const RequirementViewer: React.FC<RequirementViewerProps> = ({
  requirements,
  sessionId,
  isLoading,
  onExport,
}) => {
  const [exportTarget, setExportTarget] = useState<ExportTarget>('jira');
  const [isExporting, setIsExporting] = useState(false);

  if (!requirements || requirements.total_requirements === 0) return null;

  const handleExport = async () => {
    if (!sessionId) return;
    setIsExporting(true);
    try {
      if (exportTarget === 'pdf') {
        // PDF is a file download — open directly so the browser saves it.
        const url = `${API_BASE}/export/pdf/${encodeURIComponent(sessionId)}`;
        const a = document.createElement('a');
        a.href = url;
        a.download = `requirements_${sessionId.slice(0, 12)}.pdf`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
      } else {
        if (!onExport) return;
        await onExport({ session_id: sessionId, target: exportTarget });
      }
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p
            className="text-sm font-semibold"
            style={{ color: 'var(--color-text-primary)' }}
          >
            Export
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-secondary)' }}>
            {requirements.total_requirements} requirement
            {requirements.total_requirements !== 1 ? 's' : ''} ready
          </p>
        </div>
        {requirements.ready_for_export && (
          <span className="badge badge-success">Ready</span>
        )}
      </div>

      <div className="flex items-center gap-2">
        <select
          value={exportTarget}
          onChange={(e) => setExportTarget(e.target.value as ExportTarget)}
          className="input-base"
          style={{ flex: 1, maxWidth: 220 }}
          disabled={isExporting || isLoading}
          aria-label="Export target"
        >
          <option value="jira">Export to Jira</option>
          <option value="trello">Export to Trello</option>
          <option value="pdf">Download as PDF</option>
        </select>
        <button
          type="button"
          onClick={handleExport}
          disabled={isExporting || isLoading || !requirements.ready_for_export}
          className="btn-primary"
        >
          <Download className="w-4 h-4" />
          {isExporting ? 'Exporting…' : 'Export'}
        </button>
      </div>
    </div>
  );
};
