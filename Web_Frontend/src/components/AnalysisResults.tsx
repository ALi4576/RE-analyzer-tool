import React from 'react';
import { AlertCircle, CheckCircle, TrendingUp } from 'lucide-react';
import { AnalysisState, FormalizedRequirement } from '@/types/index';
import { LoadingSpinner } from './Loading';
import { useEffect } from 'react';

interface AnalysisResultsProps {
  state: AnalysisState | null;
  isLoading: boolean;
  formalizedRequirement?: FormalizedRequirement | null;
}

export const AnalysisResults: React.FC<AnalysisResultsProps> = ({
  state,
  isLoading,
  formalizedRequirement,
}) => {
  useEffect(() => {
    if (!state) return;

    const ws = new WebSocket(`/api/ws/stream/${state.session_id}`);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'status_update') {
        // Update analysis state with real-time data
        console.log('Real-time update:', data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [state]);

  if (isLoading) {
    return <LoadingSpinner message="Analyzing requirement..." />;
  }

  if (!state) {
    return null;
  }

  const smellScore = state.analysis_summary?.smell_score ?? 0;
  const logicalGapScore = state.analysis_summary?.logical_gap_score ?? 0;
  const issuesFound = state.analysis_summary?.issues_found ?? 0;

  const getStatusBadge = () => {
    const statuses = {
      analyzing: { bg: 'bg-blue-50', text: 'text-blue-700', label: 'Analyzing' },
      needs_clarification: { bg: 'bg-yellow-50', text: 'text-yellow-700', label: 'Needs Clarification' },
      formal_draft: { bg: 'bg-green-50', text: 'text-green-700', label: 'Formal Draft' },
      export_ready: { bg: 'bg-green-50', text: 'text-green-700', label: 'Ready for Export' },
    };
    
    const status = statuses[state.status as keyof typeof statuses];
    return (
      <span className={`px-3 py-1 rounded-full text-xs font-medium ${status.bg} ${status.text}`}>
        {status.label}
      </span>
    );
  };

  return (
    <div className="space-y-4 animate-slide-in">
      {/* Status Row */}
      <div className="card p-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {state.interrupt_needed ? (
            <AlertCircle className="w-6 h-6 text-warning" />
          ) : (
            <CheckCircle className="w-6 h-6 text-success" />
          )}
          <div>
            <h3 className="font-semibold text-neutral-900">Analysis Complete</h3>
            <p className="text-sm text-neutral-500">Session: {state.session_id}</p>
          </div>
        </div>
        {getStatusBadge()}
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Smell Score */}
        <div className="card p-4">
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-neutral-600">Quality Score</label>
            <TrendingUp className="w-4 h-4 text-neutral-400" />
          </div>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-primary-600">
              {(smellScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="mt-2 w-full bg-neutral-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full"
              style={{ width: `${Math.min(smellScore * 100, 100)}%` }}
            ></div>
          </div>
          <p className="text-xs text-neutral-500 mt-2">
            {smellScore > 0.7
              ? 'Quality issues detected'
              : 'Good quality requirement'}
          </p>
        </div>

        {/* Logical Gap */}
        <div className="card p-4">
          <label className="text-sm font-medium text-neutral-600 block mb-2">
            Logical Consistency
          </label>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-primary-600">
              {(logicalGapScore * 100).toFixed(0)}%
            </span>
          </div>
          <div className="mt-2 w-full bg-neutral-200 rounded-full h-2">
            <div
              className="bg-primary-600 h-2 rounded-full"
              style={{ width: `${(1 - logicalGapScore) * 100}%` }}
            ></div>
          </div>
          <p className="text-xs text-neutral-500 mt-2">
            {logicalGapScore > 0.3 ? 'Some gaps found' : 'Well structured'}
          </p>
        </div>

        {/* Issues Found */}
        <div className="card p-4">
          <label className="text-sm font-medium text-neutral-600 block mb-2">
            Issues Found
          </label>
          <div className="flex items-end gap-2">
            <span className="text-3xl font-bold text-error">{issuesFound}</span>
          </div>
          <p className="text-xs text-neutral-500 mt-3">
            {issuesFound === 0
              ? 'No issues detected'
              : `${issuesFound} issue${issuesFound !== 1 ? 's' : ''} to address`}
          </p>
        </div>
      </div>

      {/* ISO 29148 Formatted Requirement */}
      {formalizedRequirement?.first_requirement && (
        <div className="card p-4 bg-blue-50 border-blue-200">
          <h4 className="font-semibold text-blue-900 text-sm mb-3 flex items-center gap-2">
            <CheckCircle className="w-4 h-4" />
            ISO 29148 Formatted Requirement
          </h4>
          <div className="bg-white p-3 rounded border border-blue-100 text-sm text-neutral-700 space-y-2">
            <div>
              <span className="font-semibold text-neutral-900">ID:</span>
              <span className="ml-2 text-neutral-600">{formalizedRequirement.first_requirement.id}</span>
            </div>
            <div>
              <span className="font-semibold text-neutral-900">Title:</span>
              <p className="text-neutral-700 mt-1">{formalizedRequirement.first_requirement.title}</p>
            </div>
            <div>
              <span className="font-semibold text-neutral-900">Statement:</span>
              <p className="text-neutral-700 mt-1 italic">{formalizedRequirement.first_requirement.shall_statement}</p>
            </div>
            {formalizedRequirement.first_requirement.rationale && (
              <div>
                <span className="font-semibold text-neutral-900">Rationale:</span>
                <p className="text-neutral-700 mt-1">{formalizedRequirement.first_requirement.rationale}</p>
              </div>
            )}
            {formalizedRequirement.first_requirement.acceptance_criteria && formalizedRequirement.first_requirement.acceptance_criteria.length > 0 && (
              <div>
                <span className="font-semibold text-neutral-900">Acceptance Criteria:</span>
                <ul className="list-disc list-inside mt-1 text-neutral-600">
                  {formalizedRequirement.first_requirement.acceptance_criteria.map((criterion, idx) => (
                    <li key={idx}>{criterion}</li>
                  ))}
                </ul>
              </div>
            )}
            <div className="flex gap-4 pt-2">
              <span className="text-xs bg-neutral-100 px-2 py-1 rounded">Priority: <span className="font-semibold">{formalizedRequirement.first_requirement.priority}</span></span>
              <span className="text-xs bg-neutral-100 px-2 py-1 rounded">Status: <span className="font-semibold">{formalizedRequirement.first_requirement.status}</span></span>
            </div>
          </div>
        </div>
      )}

      {/* Interrupt Notice */}
      {state.interrupt_needed && state.clarification_questions && (
        <div className="card p-4 bg-yellow-50 border-yellow-200">
          <div className="flex gap-3">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="font-semibold text-yellow-900 text-sm mb-2">
                Clarification Needed
              </h4>
              <p className="text-sm text-yellow-800">
                The analysis detected quality issues. Please answer the clarification questions before proceeding.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
