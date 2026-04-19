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
  ready_for_export?: boolean;
}

export interface FormalizedRequirement {
  total_requirements: number;
  ready_for_export: boolean;
  completeness_score: number;
  iso_requirements?: ISORequirement[];
  requirements?: ISORequirement[];
  first_requirement?: ISORequirement | null;
}

export interface ExportRequest {
  session_id: string;
  target: 'jira' | 'trello' | 'pdf';
  jira_project?: string;
  trello_board?: string;
}

export interface ExportResult {
  session_id: string;
  target: string;
  status: 'success' | 'error';
  items_exported: number;
  export_url?: string;
  error?: string;
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
