import { create } from 'zustand';
import {
  AnalysisState,
  FormalizedRequirement,
  ISORequirement,
  UINotification,
} from '@/types/index';
import { apiClient } from '@/services/api';

interface RequirementStore {
  // State
  currentSession: string | null;
  analysisState: AnalysisState | null;
  formalizedRequirements: FormalizedRequirement | null;
  documentContextPath: string | null;
  loading: boolean;
  // Lightweight flag for background/incremental updates — does NOT block typing.
  incrementalLoading: boolean;
  error: string | null;
  notifications: UINotification[];
  uploadProgress: number;

  // Actions
  setSession: (sessionId: string) => void;
  setAnalysisState: (state: AnalysisState) => void;
  setFormalizedRequirements: (requirements: FormalizedRequirement) => void;
  analyzeRequirements: (text: string) => Promise<void>;
  // Incremental, non-blocking variant used while the user is still typing.
  // Fires /analyze then /formalize in the background, updates state, and
  // cancels any in-flight prior request to avoid out-of-order races.
  analyzeRequirementsIncremental: (text: string) => void;
  clarifyRequirements: (
    clarifications: Record<string, string>
  ) => Promise<void>;
  updateRequirement: (id: string, changes: Partial<ISORequirement>) => void;
  clarifyOneRequirement: (reqId: string, context: string) => Promise<void>;
  fetchFormalizedRequirements: () => Promise<void>;
  uploadAudio: (file: File) => Promise<void>;
  uploadDocument: (file: File) => Promise<void>;
  addNotification: (notification: Omit<UINotification, 'id'>) => void;
  removeNotification: (id: string) => void;
  reset: () => void;
}

// Module-scope controller so successive incremental calls can cancel the
// previous in-flight request without storing an AbortController in React state.
let incrementalAbortController: AbortController | null = null;
// Monotonic sequence guard: a late-arriving older response must not overwrite
// a newer one even if the abort didn't reach the server in time.
let incrementalSeq = 0;

export const useRequirementStore = create<RequirementStore>((set, get) => ({
  currentSession: null,
  analysisState: null,
  formalizedRequirements: null,
  documentContextPath: null,
  loading: false,
  incrementalLoading: false,
  error: null,
  notifications: [],
  uploadProgress: 0,

  setSession: (sessionId: string) => {
    set({ currentSession: sessionId });
  },

  setAnalysisState: (state: AnalysisState) => {
    set({ analysisState: state });
  },

  setFormalizedRequirements: (requirements: FormalizedRequirement) => {
    set({ formalizedRequirements: requirements });
  },

  analyzeRequirements: async (text: string, overrideSessionId?: string) => {
    const { currentSession, addNotification } = get();
    const sessionId = overrideSessionId || currentSession;

    if (!sessionId) {
      addNotification({
        type: 'error',
        message: 'No session ID. Please refresh the page.',
      });
      return;
    }

    // Cancel any in-flight incremental so a stale background response can't
    // overwrite interrupt_needed:true with false after the modal appears.
    if (incrementalAbortController) {
      incrementalAbortController.abort();
      incrementalAbortController = null;
    }
    ++incrementalSeq;

    set({ loading: true, error: null });
    try {
      const result = await apiClient.analyzeRequirements({
        text,
        session_id: sessionId,
        context_file_path: get().documentContextPath,
      });
      set({ analysisState: result });

      // /analyze now returns iso_requirements inline — hydrate formalizedRequirements
      // directly so RequirementFeed populates without a second /formalize call.
      if (result.iso_requirements && result.iso_requirements.length > 0) {
        set({
          formalizedRequirements: {
            iso_requirements: result.iso_requirements,
            total_requirements: result.total_requirements ?? result.iso_requirements.length,
            completeness_score: result.completeness_score ?? 0,
            // Smell-based quality score — primary metric for card/footer
            // meters. Fall back to completeness for backends that have
            // not yet been upgraded.
            quality_score: result.quality_score ?? result.completeness_score ?? 0,
            ready_for_export: result.ready_for_export ?? false,
          },
        });
      }

      addNotification({
        type: 'success',
        message: 'Requirement analysis completed successfully!',
      });
    } catch (error: any) {
      const message = apiClient.getErrorMessage(error);
      set({ error: message });
      addNotification({ type: 'error', message });
    } finally {
      set({ loading: false });
    }
  },

  /**
   * Non-blocking incremental analysis.
   *
   * Triggered while the user is still typing (every 30 new characters).
   * Fires /analyze (score) and /formalize (ISO specs) concurrently in the
   * background, then patches the store. Returns immediately so the caller
   * (textarea onChange) never awaits network I/O.
   *
   * Safety properties:
   *  - Cancels any prior in-flight request via AbortController.
   *  - A monotonically increasing sequence number guards against stale
   *    responses clobbering newer state if the server didn't honor abort.
   *  - Does NOT set `loading: true` (which disables the submit button);
   *    uses `incrementalLoading` instead for optional subtle UI hints.
   *  - Does NOT surface error/success toasts — the user is still typing.
   */
  analyzeRequirementsIncremental: (text: string) => {
    const { currentSession } = get();
    if (!currentSession || !text.trim()) return;

    // Abort the previous in-flight incremental request, if any.
    if (incrementalAbortController) {
      incrementalAbortController.abort();
    }
    const controller = new AbortController();
    incrementalAbortController = controller;

    const mySeq = ++incrementalSeq;
    set({ incrementalLoading: true });

    // Fire and forget — we do NOT await.
    (async () => {
      try {
        // Single call to /analyze — response now includes iso_requirements inline
        // so there is no second /formalize round-trip to race or abort.
        const analysis = await apiClient.analyzeRequirements(
          { text, session_id: currentSession, context_file_path: get().documentContextPath },
          { signal: controller.signal }
        );

        // Guard against stale responses from superseded requests.
        if (mySeq !== incrementalSeq) return;

        set({ analysisState: analysis });

        // Hydrate the requirements panel directly from the analyze response.
        if (analysis.iso_requirements && analysis.iso_requirements.length > 0) {
          set({
            formalizedRequirements: {
              iso_requirements: analysis.iso_requirements,
              total_requirements: analysis.total_requirements ?? analysis.iso_requirements.length,
              completeness_score: analysis.completeness_score ?? 0,
              quality_score: analysis.quality_score ?? analysis.completeness_score ?? 0,
              ready_for_export: analysis.ready_for_export ?? false,
            },
          });
        }
      } catch (err: any) {
        // Cancellation is expected whenever a newer keystroke supersedes us.
        if (err?.name === 'CanceledError' || err?.code === 'ERR_CANCELED') {
          return;
        }
        // Silent failure for background calls; surface via console only.
        console.warn('[incremental analysis] failed:', err);
      } finally {
        if (mySeq === incrementalSeq) {
          set({ incrementalLoading: false });
        }
      }
    })();
  },

  clarifyRequirements: async (clarifications: Record<string, string>) => {
    const { currentSession, addNotification } = get();
    if (!currentSession) return;

    set({ loading: true, error: null });
    try {
      const result = await apiClient.clarifyRequirements({
        session_id: currentSession,
        clarifications,
      });
      set({ analysisState: result });

      // /clarify also returns iso_requirements inline after re-running the pipeline
      if (result.iso_requirements && result.iso_requirements.length > 0) {
        set({
          formalizedRequirements: {
            iso_requirements: result.iso_requirements,
            total_requirements: result.total_requirements ?? result.iso_requirements.length,
            completeness_score: result.completeness_score ?? 0,
            quality_score: result.quality_score ?? result.completeness_score ?? 0,
            ready_for_export: result.ready_for_export ?? false,
          },
        });
      }

      addNotification({
        type: 'success',
        message: 'Clarifications processed!',
      });
    } catch (error: any) {
      const message = apiClient.getErrorMessage(error);
      set({ error: message });
      addNotification({ type: 'error', message });
    } finally {
      set({ loading: false });
    }
  },

  updateRequirement: (id: string, changes: Partial<ISORequirement>) => {
    if (!id) return;
    // Fire-and-forget PATCH to persist edit server-side for the session lifetime.
    const { currentSession } = get();
    if (currentSession) {
      apiClient.patchRequirement(currentSession, id, changes as any).catch((err) => {
        console.warn('[updateRequirement] backend patch failed:', err);
      });
    }
    set((state) => {
      const current = state.formalizedRequirements;
      if (!current || !current.iso_requirements) return {} as any;

      let matched = false;
      const nextIsoRequirements = current.iso_requirements.map((req) => {
        if (req.requirement_id === id || req.id === id) {
          matched = true;
          return { ...req, ...changes };
        }
        return req;
      });

      if (!matched) return {} as any;

      // Keep the parallel `requirements` array in sync if the backend
      // happened to populate it (some WS payloads mirror both fields).
      const nextRequirements = current.requirements
        ? current.requirements.map((req: any) => {
            if (req?.requirement_id === id || req?.id === id) {
              return { ...req, ...changes };
            }
            return req;
          })
        : current.requirements;

      return {
        formalizedRequirements: {
          ...current,
          iso_requirements: nextIsoRequirements,
          requirements: nextRequirements,
        },
      };
    });
  },

  clarifyOneRequirement: async (reqId: string, context: string) => {
    const { currentSession, addNotification } = get();
    if (!currentSession || !reqId) return;
    try {
      const result = await apiClient.clarifyOneRequirement(currentSession, reqId, context);
      const improved: ISORequirement = result?.iso_requirements?.[0];
      if (!improved) return;
      set((state) => {
        const current = state.formalizedRequirements;
        if (!current?.iso_requirements) return {} as any;
        return {
          formalizedRequirements: {
            ...current,
            iso_requirements: current.iso_requirements.map((r) =>
              r.requirement_id === reqId ? { ...r, ...improved } : r
            ),
          },
        };
      });
      addNotification({ type: 'success', message: 'Requirement improved.' });
    } catch (err: any) {
      addNotification({ type: 'error', message: apiClient.getErrorMessage(err) });
    }
  },

  fetchFormalizedRequirements: async () => {
    const { currentSession } = get();
    if (!currentSession) return;

    set({ loading: true, error: null });
    try {
      const result = await apiClient.getFormalizedRequirements(currentSession);
      set({ formalizedRequirements: result });
    } catch (error: any) {
      const message = apiClient.getErrorMessage(error);
      set({ error: message });
    } finally {
      set({ loading: false });
    }
  },

  addNotification: (notification: Omit<UINotification, 'id'>) => {
    const id = Math.random().toString(36).substr(2, 9);
    const newNotification: UINotification = { ...notification, id };

    set((state) => ({
      notifications: [...state.notifications, newNotification],
    }));

    if (notification.duration !== 0) {
      setTimeout(() => {
        get().removeNotification(id);
      }, notification.duration || 3000);
    }
  },

  removeNotification: (id: string) => {
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    }));
  },

  reset: () => {
    if (incrementalAbortController) {
      incrementalAbortController.abort();
      incrementalAbortController = null;
    }
    set({
      currentSession: null,
      analysisState: null,
      formalizedRequirements: null,
      documentContextPath: null,
      loading: false,
      incrementalLoading: false,
      error: null,
      notifications: [],
      uploadProgress: 0,
    });
  },

  uploadAudio: async (file: File) => {
    const { addNotification } = get();
    set({ loading: true, error: null, uploadProgress: 0 });
    try {
      const result = await apiClient.uploadAudio(file);
      await get().analyzeRequirements(result.transcription);
      addNotification({
        type: 'success',
        message: `Audio uploaded and transcribed: ${result.text_length} characters`,
      });
    } catch (error: any) {
      const message = apiClient.getErrorMessage(error);
      set({ error: message });
      addNotification({ type: 'error', message });
    } finally {
      set({ loading: false, uploadProgress: 0 });
    }
  },

  uploadDocument: async (file: File) => {
    const { addNotification } = get();
    set({ loading: true, error: null, uploadProgress: 0 });
    try {
      const result = await apiClient.uploadDocument(file);
      // Persist the server-side path so all subsequent analyzeRequirements
      // calls can inject this document as context (was always null before).
      if (result?.file_path) {
        set({ documentContextPath: result.file_path });
      }
      addNotification({
        type: 'success',
        message: `Document uploaded: ${file.name} — will be used as context`,
      });
      return result;
    } catch (error: any) {
      const message = apiClient.getErrorMessage(error);
      set({ error: message });
      addNotification({ type: 'error', message });
    } finally {
      set({ loading: false, uploadProgress: 0 });
    }
  },
}));

// Guard against duplicate listener registration (StrictMode double-mount, session re-init)
let wsListenersRegistered = false;

// Setup WebSocket event listeners
export function setupWebSocketListeners() {
  if (wsListenersRegistered) return;
  wsListenersRegistered = true;
  // Listen for analysis updates (SCRIBE MODE)
  window.addEventListener('analysis_update', (event: any) => {
    const message = event.detail;
    const store = useRequirementStore.getState();
    
    // SCRIBE MODE: Extract requirements_list (MANDATORY field)
    const requirements_list = message.requirements_list || [];
    const requirements_count = message.requirements_count || 0;
    const completeness_score = message.completeness_score || 0;
    // Smell-based quality — primary metric for the feed footer. Fall back
    // to completeness so older backends (or the transitional deploy window)
    // still render a meaningful value.
    const quality_score =
      typeof message.quality_score === 'number'
        ? message.quality_score
        : completeness_score;

    console.log(`[Scribe Mode] Received ${requirements_count} requirements with completeness ${completeness_score.toFixed(2)}, quality ${quality_score.toFixed(2)}`);
    console.log('Store received analysis_update:', message);

    // Update analysis state
    store.setAnalysisState({
      session_id: store.currentSession || '',
      status: message.status || 'analyzing',
      interrupt_needed: message.interrupt_needed || false,
      clarification_questions: message.clarification_questions || null,
      analysis_summary: message.analysis_summary || {},
    } as any);

    // Update formalized requirements with requirements_list
    store.setFormalizedRequirements({
      total_requirements: requirements_count,
      ready_for_export: message.status === 'export_ready' || false,
      completeness_score: completeness_score,
      quality_score: quality_score,
      requirements: requirements_list,
      iso_requirements: requirements_list,
    } as any);
  });
  
  // Listen for clarification processed (SCRIBE MODE)
  window.addEventListener('clarification_processed', (event: any) => {
    const message = event.detail;
    const store = useRequirementStore.getState();
    
    // SCRIBE MODE: Extract requirements_list
    const requirements_list = message.requirements_list || [];
    const requirements_count = message.requirements_count || 0;
    const completeness_score = message.completeness_score || 0;
    const quality_score =
      typeof message.quality_score === 'number'
        ? message.quality_score
        : completeness_score;

    console.log(`[Scribe Mode] Clarification processed - ${requirements_count} requirements updated`);
    console.log('Store received clarification_processed:', message);

    // Update analysis state
    store.setAnalysisState({
      session_id: store.currentSession || '',
      status: message.status || 'analyzing',
      interrupt_needed: false,
      clarification_questions: null,
      analysis_summary: message.analysis_summary || {},
    } as any);

    // Update formalized requirements with requirements_list
    store.setFormalizedRequirements({
      total_requirements: requirements_count,
      ready_for_export: message.status === 'export_ready' || false,
      completeness_score: completeness_score,
      quality_score: quality_score,
      requirements: requirements_list,
      iso_requirements: requirements_list,
    } as any);
  });
}
