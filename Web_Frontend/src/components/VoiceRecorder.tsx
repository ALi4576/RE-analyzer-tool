import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Loader } from 'lucide-react';
import { WebSocketAudioStreamer } from '@/services/audioStreaming';
import { useRequirementStore } from '@/store/requirementStore';

interface VoiceRecorderProps {
    sessionId: string | null;
    onTranscription?: (text: string) => void;
    onInterrupt?: (payload: any) => void;
    isLoading?: boolean;
}

export const VoiceRecorder: React.FC<VoiceRecorderProps> = ({
    sessionId,
    onTranscription,
    onInterrupt,
    isLoading = false,
}) => {
    const [isRecording, setIsRecording] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [transcription, setTranscription] = useState('');
    const [audioLevel, setAudioLevel] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const streamerRef = useRef<WebSocketAudioStreamer | null>(null);
    const audioLevelIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
    const { addNotification, analyzeRequirements } = useRequirementStore();

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (streamerRef.current) {
                streamerRef.current.disconnect();
            }
            if (audioLevelIntervalRef.current) {
                clearInterval(audioLevelIntervalRef.current);
            }
        };
    }, []);

    const handleStartRecording = async () => {
        if (!sessionId) {
            setError('No session ID available');
            addNotification({ type: 'error', message: 'Session not initialized' });
            return;
        }

        try {
            setIsConnecting(true);
            setError(null);
            setTranscription('');

            const streamer = new WebSocketAudioStreamer(sessionId);
            streamerRef.current = streamer;

            // Connect to WebSocket
            await streamer.connect();

            // Start recording and streaming
            await streamer.startRecording(
                (chunk) => {
                    // Handle real-time transcription updates
                    setTranscription((prev) => {
                        const updatedTranscription = prev + ' ' + chunk;
                        if (updatedTranscription.trim().length >= 50) {
                            analyzeRequirements(updatedTranscription);
                        }
                        return updatedTranscription;
                    });
                    if (onTranscription) onTranscription(chunk);
                },
                (payload) => {
                    // Handle AI interrupts
                    console.log('AI Interrupt:', payload);
                    if (onInterrupt) onInterrupt(payload);
                    addNotification({
                        type: 'warning',
                        message: 'AI requires clarification',
                    });
                }
            );

            setIsRecording(true);
            setIsConnecting(false);

            // Update audio level indicator
            audioLevelIntervalRef.current = setInterval(() => {
                if (streamer) {
                    setAudioLevel(streamer.getAudioLevel());
                }
            }, 50);

            addNotification({
                type: 'success',
                message: 'Voice recording started',
            });
        } catch (err) {
            const errorMsg = (err as Error).message || 'Failed to start recording';
            console.error('Voice Input Error:', {
                message: errorMsg,
                stack: (err as Error).stack,
                error: err,
            });
            setError(errorMsg);
            setIsConnecting(false);

            // Provide more helpful error message for common issues
            let userMessage = errorMsg;
            if (errorMsg.includes('microphone')) {
                userMessage = 'Microphone access denied or unavailable. Check browser permissions.';
            } else if (errorMsg.includes('WebSocket')) {
                userMessage = 'Could not connect to backend. Is the server running?';
            }

            addNotification({ type: 'error', message: userMessage });

            // Clean up
            if (streamerRef.current) {
                streamerRef.current.disconnect();
                streamerRef.current = null;
            }
        }
    };

    const handleStopRecording = async () => {
        try {
            if (streamerRef.current) {
                await streamerRef.current.stopRecording();
            }

            setIsRecording(false);
            setAudioLevel(0);

            if (audioLevelIntervalRef.current) {
                clearInterval(audioLevelIntervalRef.current);
            }

            // Auto-analyze the transcribed text
            if (transcription.trim()) {
                addNotification({
                    type: 'success',
                    message: 'Recording complete. Analyzing...',
                });

                // Trigger analysis with the transcribed text
                await analyzeRequirements(transcription);
            }
        } catch (err) {
            const message = (err as Error).message || 'Failed to stop recording';
            setError(message);
            addNotification({ type: 'error', message });
        }
    };

    return (
        <div className="card p-6 space-y-4">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h3 className="font-semibold text-neutral-900">Voice Input</h3>
                    <p className="text-sm text-neutral-500">
                        Speak directly to the AI for real-time analysis
                    </p>
                </div>
                <div className="text-right text-xs text-neutral-500">
                    {isRecording && (
                        <div className="flex items-center gap-2">
                            <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                            Recording
                        </div>
                    )}
                </div>
            </div>

            {/* Audio Level Indicator */}
            {isRecording && (
                <div className="space-y-2">
                    <label className="text-xs font-medium text-neutral-600">
                        Audio Level
                    </label>
                    <div className="w-full bg-neutral-200 rounded-full h-2">
                        <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-100"
                            style={{ width: `${audioLevel}%` }}
                        ></div>
                    </div>
                </div>
            )}

            {/* Transcription Display */}
            {transcription && (
                <div className="bg-neutral-50 rounded-lg p-4 border border-neutral-200 min-h-20">
                    <p className="text-sm text-neutral-700">
                        {transcription}
                        {isRecording && (
                            <span className="ml-1 inline-block w-1.5 h-5 bg-blue-500 animate-pulse"></span>
                        )}
                    </p>
                </div>
            )}

            {/* Error Message */}
            {error && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                    <p className="text-sm text-red-700">{error}</p>
                </div>
            )}

            {/* Controls */}
            <div className="flex gap-3">
                {!isRecording ? (
                    <button
                        onClick={handleStartRecording}
                        disabled={isConnecting || isLoading}
                        className="btn-primary flex items-center gap-2 flex-1"
                    >
                        {isConnecting ? (
                            <>
                                <Loader className="w-4 h-4 animate-spin" />
                                Connecting...
                            </>
                        ) : (
                            <>
                                <Mic className="w-4 h-4" />
                                Start Voice Input
                            </>
                        )}
                    </button>
                ) : (
                    <>
                        <button
                            onClick={handleStopRecording}
                            className="btn-secondary px-4 flex items-center gap-2 flex-1"
                        >
                            <MicOff className="w-4 h-4" />
                            Stop Recording
                        </button>
                        <button
                            onClick={handleStopRecording}
                            className="btn-primary px-4 flex items-center gap-2"
                        >
                            <Send className="w-4 h-4" />
                            Analyze
                        </button>
                    </>
                )}
            </div>

            {/* Info Text */}
            <p className="text-xs text-neutral-500 leading-relaxed">
                💡 Tip: The AI will automatically interrupt if it needs clarification.
                Speak naturally—agile requirements, edge cases, security concerns,
                anything! The system captures everything in real-time.
            </p>
        </div>
    );
};
