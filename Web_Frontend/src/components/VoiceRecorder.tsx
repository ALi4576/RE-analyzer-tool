import React, { useState, useEffect, useRef } from 'react';
import { Mic, MicOff, Send, Loader } from 'lucide-react';
import { WebSocketAudioStreamer } from '@/services/audioStreaming';
import { useRequirementStore } from '@/store/requirementStore';

interface VoiceRecorderProps {
  sessionId: string | null;
  onTranscription?: (text: string) => void;
  onInterrupt?: (payload: unknown) => void;
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

  useEffect(() => {
    return () => {
      if (streamerRef.current) streamerRef.current.disconnect();
      if (audioLevelIntervalRef.current) clearInterval(audioLevelIntervalRef.current);
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

      await streamer.connect();

      await streamer.startRecording(
        (chunk) => {
          // Accumulate transcription for display. The WS handler on the backend
          // already runs incremental analysis — do NOT double-fire analyze here.
          setTranscription((prev) => prev + ' ' + chunk);
          if (onTranscription) onTranscription(chunk);
        },
        (payload) => {
          if (onInterrupt) onInterrupt(payload);
          addNotification({
            type: 'warning',
            message: 'AI requires clarification',
          });
        }
      );

      setIsRecording(true);
      setIsConnecting(false);

      audioLevelIntervalRef.current = setInterval(() => {
        if (streamer) setAudioLevel(streamer.getAudioLevel());
      }, 50);

      addNotification({ type: 'success', message: 'Voice recording started' });
    } catch (err) {
      const errorMsg = (err as Error).message || 'Failed to start recording';
      setError(errorMsg);
      setIsConnecting(false);

      let userMessage = errorMsg;
      if (errorMsg.includes('microphone')) {
        userMessage = 'Microphone access denied. Check browser permissions.';
      } else if (errorMsg.includes('WebSocket')) {
        userMessage = 'Could not connect to backend. Is the server running?';
      }

      addNotification({ type: 'error', message: userMessage });

      if (streamerRef.current) {
        streamerRef.current.disconnect();
        streamerRef.current = null;
      }
    }
  };

  const handleStopRecording = async () => {
    try {
      if (streamerRef.current) await streamerRef.current.stopRecording();

      setIsRecording(false);
      setAudioLevel(0);

      if (audioLevelIntervalRef.current) clearInterval(audioLevelIntervalRef.current);

      if (transcription.trim()) {
        addNotification({ type: 'success', message: 'Recording complete. Analyzing…' });
        await analyzeRequirements(transcription);
      }
    } catch (err) {
      const message = (err as Error).message || 'Failed to stop recording';
      setError(message);
      addNotification({ type: 'error', message });
    }
  };

  return (
    <div className="space-y-3">
      {/* Recording indicator */}
      {isRecording && (
        <div
          className="flex items-center justify-between px-3 py-2"
          style={{
            backgroundColor: 'var(--color-danger-subtle)',
            border: '1px solid var(--color-danger-subtle-border)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <div className="flex items-center gap-2">
            <span
              className="w-2 h-2 rounded-full animate-pulse"
              style={{ backgroundColor: 'var(--color-danger)' }}
            />
            <span
              className="text-xs font-semibold"
              style={{ color: 'var(--color-danger-text)' }}
            >
              Recording
            </span>
          </div>
          <div
            className="flex-1 mx-3 h-1.5 overflow-hidden"
            style={{
              backgroundColor: 'var(--color-border)',
              borderRadius: 'var(--radius-full)',
            }}
          >
            <div
              className="h-full transition-all"
              style={{
                width: `${audioLevel}%`,
                backgroundColor: 'var(--color-danger)',
                borderRadius: 'var(--radius-full)',
              }}
            />
          </div>
        </div>
      )}

      {/* Transcription preview */}
      {transcription && (
        <div
          className="p-3 text-sm min-h-[64px]"
          style={{
            backgroundColor: 'var(--color-surface)',
            border: '1px solid var(--color-border)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-text-primary)',
          }}
        >
          {transcription}
          {isRecording && (
            <span
              className="ml-1 inline-block w-0.5 h-4 align-middle animate-pulse"
              style={{ backgroundColor: 'var(--color-primary)' }}
            />
          )}
        </div>
      )}

      {/* Error */}
      {error && (
        <div
          className="px-3 py-2 text-sm"
          style={{
            backgroundColor: 'var(--color-danger-subtle)',
            border: '1px solid var(--color-danger-subtle-border)',
            color: 'var(--color-danger-text)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="flex gap-2">
        {!isRecording ? (
          <button
            type="button"
            onClick={handleStartRecording}
            disabled={isConnecting || isLoading}
            className="btn-secondary flex-1"
          >
            {isConnecting ? (
              <>
                <Loader className="w-4 h-4 animate-spin" />
                Connecting…
              </>
            ) : (
              <>
                <Mic className="w-4 h-4" />
                Start voice input
              </>
            )}
          </button>
        ) : (
          <>
            <button
              type="button"
              onClick={handleStopRecording}
              className="btn-secondary flex-1"
            >
              <MicOff className="w-4 h-4" />
              Stop
            </button>
            <button
              type="button"
              onClick={handleStopRecording}
              className="btn-primary"
            >
              <Send className="w-4 h-4" />
              Analyze
            </button>
          </>
        )}
      </div>
    </div>
  );
};
