import React, { useEffect, useRef } from 'react';
import { Mic } from 'lucide-react';

interface WaveformVisualizerProps {
  isRecording: boolean;
  analyser?: AnalyserNode;
}

function cssVar(name: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  isRecording,
  analyser,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!isRecording || !analyser || !canvasRef.current) {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      // Resolve colors on every frame so theme changes during recording also take effect.
      const bg = cssVar('--color-surface-sunken', '#F8FAFC');
      const lineColor = cssVar('--color-primary', '#2563EB');
      const guideColor = cssVar('--color-border', '#E2E8F0');

      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      const sliceWidth = (canvas.width * 1.0) / bufferLength;
      let x = 0;

      ctx.strokeStyle = lineColor;
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
        x += sliceWidth;
      }

      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      ctx.strokeStyle = guideColor;
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
    };
  }, [isRecording, analyser]);

  return (
    <div
      className="p-3"
      style={{
        backgroundColor: 'var(--color-surface)',
        border: '1px solid var(--color-border)',
        borderRadius: 'var(--radius-md)',
      }}
    >
      <div className="flex items-center gap-2 mb-2">
        <div className="flex items-center gap-1.5">
          <span
            className={`w-1.5 h-1.5 rounded-full ${isRecording ? 'animate-pulse' : ''}`}
            style={{
              backgroundColor: isRecording
                ? 'var(--color-danger)'
                : 'var(--color-text-muted)',
            }}
          />
          <span
            className="text-xs font-medium"
            style={{
              color: isRecording
                ? 'var(--color-danger-text)'
                : 'var(--color-text-secondary)',
            }}
          >
            {isRecording ? 'Recording' : 'Ready'}
          </span>
        </div>
        {isRecording && (
          <span
            className="text-xs ml-auto"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Live waveform
          </span>
        )}
      </div>

      <canvas
        ref={canvasRef}
        width={300}
        height={60}
        className="w-full block"
        style={{
          backgroundColor: 'var(--color-surface-sunken)',
          border: '1px solid var(--color-border)',
          borderRadius: 'var(--radius-sm)',
        }}
      />

      {!isRecording && (
        <div
          className="flex items-center justify-center gap-1.5 mt-2 text-xs"
          style={{ color: 'var(--color-text-muted)' }}
        >
          <Mic className="w-3 h-3" />
          <span>Click record to see waveform</span>
        </div>
      )}
    </div>
  );
};
