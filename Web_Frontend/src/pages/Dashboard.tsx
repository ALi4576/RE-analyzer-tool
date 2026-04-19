import React, { useEffect } from 'react';
import {
    RequirementInput,
    ClarificationPanel,
    RequirementViewer,
    VoiceRecorder,
    SmellMeter,
    RequirementFeed,
    WaveformVisualizer,
} from '@/components/index';
import { useRequirementStore, setupWebSocketListeners } from '@/store/requirementStore';
import { generateSessionId } from '@/utils/helpers';
import { apiClient } from '@/services/api';
import { ExportRequest } from '@/types/index';

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
        fetchFormalizedRequirements,
        addNotification,
    } = useRequirementStore();

    // Initialize session
    useEffect(() => {
        if (!currentSession) {
            setSession(generateSessionId());
        }
        // Setup WebSocket listeners
        setupWebSocketListeners();
    }, [currentSession, setSession]);

    // Requirements are now returned inline by /analyze and /clarify.
    // fetchFormalizedRequirements is kept as a fallback for manual refresh
    // but is no longer needed for the main flow.

    const handleClarify = async (clarifications: Record<string, string>) => {
        await clarifyRequirements(clarifications);
    };

    const handleExport = async (request: ExportRequest) => {
        try {
            const result = await apiClient.exportRequirements(request);
            addNotification({
                type: 'success',
                message: `Successfully exported ${result.items_exported || 0} requirements to ${request.target}!`,
            });
        } catch (error: any) {
            const message = apiClient.getErrorMessage(error);
            addNotification({ type: 'error', message });
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-neutral-50 to-neutral-100">
            {/* Hero Section */}
            <div className="bg-white border-b border-neutral-200 sticky top-0 z-10">
                <div className="max-w-full px-6 py-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h1 className="text-3xl font-bold text-neutral-900">
                                Requirements Elicitation
                            </h1>
                            <p className="text-sm text-neutral-600 mt-1">
                                AI-native analysis with ISO 29148 compliance
                            </p>
                        </div>
                        {currentSession && (
                            <div className="text-right text-xs text-neutral-500">
                                Session: <span className="font-mono text-primary-600">{currentSession.substring(0, 8)}...</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Split-Screen Layout */}
            <div className="max-w-full h-[calc(100vh-120px)] flex overflow-hidden">
                {/* LEFT PANE: INPUT ZONE */}
                <div className="flex-1 border-r border-neutral-200 overflow-y-auto p-6 space-y-6 bg-white">
                    <div>
                        <h2 className="text-lg font-bold text-neutral-900 mb-4 flex items-center gap-2">
                            📝 Input Zone
                        </h2>

                        {/* Text Input - Scratchpad */}
                        <RequirementInput
                            onAnalyze={analyzeRequirements}
                            onIncrementalAnalyze={analyzeRequirementsIncremental}
                            isLoading={loading}
                        />
                    </div>

                    {/* Waveform Visualizer */}
                    <div>
                        <WaveformVisualizer 
                            isRecording={false}
                        />
                    </div>

                    {/* Voice Recording */}
                    <div>
                        <VoiceRecorder
                            sessionId={currentSession}
                            isLoading={loading}
                        />
                    </div>
                </div>

                {/* RIGHT PANE: INTELLIGENCE ZONE */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-neutral-50">
                    <div>
                        <h2 className="text-lg font-bold text-neutral-900 mb-4 flex items-center gap-2">
                            🧠 Intelligence Zone
                            {incrementalLoading && (
                                <span
                                    className="ml-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary-700 bg-primary-50 border border-primary-200 px-2 py-0.5 rounded-full"
                                    aria-live="polite"
                                >
                                    <span className="w-1.5 h-1.5 rounded-full bg-primary-500 animate-pulse" />
                                    Updating
                                </span>
                            )}
                        </h2>

                        {/* Smell Meter - Quality Gauge */}
                        {analysisState && (
                            <SmellMeter
                                smellScore={analysisState.analysis_summary?.smell_score ?? 0}
                                label="Quality Score"
                            />
                        )}

                        {/* Requirement Feed - Scrolling ISO 29148 specs */}
                        <div className="mt-6">
                            <h3 className="text-sm font-semibold text-neutral-700 mb-3 flex items-center justify-between">
                                <span>ISO 29148 Formatted Requirements</span>
                                {formalizedRequirements && formalizedRequirements.total_requirements > 0 && (
                                    <span className="text-xs font-normal text-neutral-500">
                                        {formalizedRequirements.total_requirements} spec
                                        {formalizedRequirements.total_requirements === 1 ? '' : 's'}
                                    </span>
                                )}
                            </h3>
                            {/*
                              Only show the skeleton on the INITIAL full-submit load.
                              For incremental refreshes, keep the previous specs visible
                              (and let the "Updating" pill above signal background work)
                              so the panel doesn't flash empty on every keystroke milestone.
                            */}
                            <RequirementFeed
                                requirements={formalizedRequirements}
                                isLoading={loading && !formalizedRequirements}
                            />
                        </div>

                        {/* Export Controls */}
                        {formalizedRequirements && formalizedRequirements.total_requirements > 0 && (
                            <RequirementViewer
                                requirements={formalizedRequirements}
                                sessionId={currentSession}
                                isLoading={loading}
                                onExport={handleExport}
                            />
                        )}

                        {/* Clarification Overlay - High Priority Modal */}
                        {analysisState?.interrupt_needed && analysisState.clarification_questions && (
                            <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
                                <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-96 overflow-y-auto">
                                    <ClarificationPanel
                                        questions={analysisState.clarification_questions}
                                        onSubmit={handleClarify}
                                        isLoading={loading}
                                    />
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
