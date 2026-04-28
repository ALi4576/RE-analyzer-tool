/**
 * Requirement Analysis Types
 */

export interface ISORequirement {
  requirement_id?: string;
  id?: string;
  title: string;
  shall_statement: string;
  rationale: string;
  acceptance_criteria: string[];
  priority?: 'High' | 'Medium' | 'Low' | 'high' | 'medium' | 'low';
  category?: 'Functional' | 'Non-functional' | 'Interface';
  status?: 'draft' | 'approved' | 'implemented' | 'ready_for_export';
  traceability?: string[];
  /** Per-requirement completeness ratio across the 6 ISO fields (0.0-1.0). */
  completeness_score?: number;
  /**
   * Per-requirement smell-based quality score (0.0-1.0) where 1.0 means no
   * smells matched this requirement's text and 0.0 is worst.
   */
  quality_score?: number;
  /**
   * Combined score: average of completeness_score and quality_score (0.0-1.0).
   * Preferred display metric — use this over quality_score when present.
   */
  overall_score?: number;
}

export interface RequirementSmell {
  type: string;
  severity: number;
  location: string;
  recommendation: string;
}

export interface ClarificationQuestion {
  question_id: string;
  question: string;
  context: string;
  required_clarity: string[];
}

export interface AnalysisState {
  session_id: string;
  status: 'pending' | 'analyzing' | 'needs_clarification' | 'formal_draft' | 'export_ready';
  interrupt_needed: boolean;
  clarification_questions: ClarificationQuestion[] | null;
  analysis_summary?: {
    smell_score: number | null;
    logical_gap_score: number | null;
    issues_found: number;
  };
  // Inline requirements returned by /analyze and /clarify — no second /formalize call needed
  iso_requirements?: ISORequirement[];
  total_requirements?: number;
  completeness_score?: number;
  /** Document-level average of per-requirement smell quality scores (0.0-1.0). */
  quality_score?: number;
  /** Document-level combined score: avg of completeness + quality (0.0-1.0). Preferred display metric. */
  overall_score?: number;
  ready_for_export?: boolean;
}

export interface FormalizedRequirement {
  total_requirements: number;
  ready_for_export: boolean;
  completeness_score: number;
  /** Document-level average of per-requirement smell quality scores (0.0-1.0). */
  quality_score?: number;
  /** Document-level combined score: avg of completeness + quality (0.0-1.0). Preferred display metric. */
  overall_score?: number;
  iso_requirements?: ISORequirement[];
  requirements?: ISORequirement[];
  first_requirement?: ISORequirement | null;
}

export interface ExportRequest {
  session_id: string;
  /** UI-facing target name — mapped to export_target before sending to the API. */
  target: 'jira' | 'trello' | 'pdf';
  jira_project?: string;
  trello_board?: string;
}

export interface ExportResult {
  export_id: string;
  target: string;
  /** "success" or "failed" — backend uses "failed" not "error". */
  status: 'success' | 'failed';
  ticket_ids: string[];
  url?: string;
  timestamp?: string;
}

// API Request Types
export interface AnalyzeRequirementsRequest {
  text: string;
  session_id: string;
  context_file_path?: string | null;
}

export interface ClarificationResponseRequest {
  session_id: string;
  clarifications: Record<string, string>;
}

// UI State
export interface UINotification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  duration?: number;
}
