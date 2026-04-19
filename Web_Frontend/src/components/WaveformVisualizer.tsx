import React, { useEffect, useRef } from 'react';
import { Mic } from 'lucide-react';

interface WaveformVisualizerProps {
  isRecording: boolean;
  analyser?: AnalyserNode;
}

export const WaveformVisualizer: React.FC<WaveformVisualizerProps> = ({
  isRecording,
  analyser,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animationRef = useRef<number>();

  useEffect(() => {
    if (!isRecording || !analyser || !canvasRef.current) {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
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

      // Clear canvas
      ctx.fillStyle = 'rgba(248, 250, 252, 1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Draw waveform
      const sliceWidth = (canvas.width * 1.0) / bufferLength;
      let x = 0;

      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';
      ctx.beginPath();

      for (let i = 0; i < bufferLength; i++) {
        const v = dataArray[i] / 128.0;
        const y = (v * canvas.height) / 2;

        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }

        x += sliceWidth;
      }

      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();

      // Draw center line
      ctx.strokeStyle = 'rgba(229, 231, 235, 0.5)';
      ctx.setLineDash([5, 5]);
      ctx.beginPath();
      ctx.moveTo(0, canvas.height / 2);
      ctx.lineTo(canvas.width, canvas.height / 2);
      ctx.stroke();
      ctx.setLineDash([]);
    };

    draw();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [isRecording, analyser]);

  return (
    <div className="card p-4 bg-neutral-50">
      <div className="flex items-center gap-2 mb-3">
        <div className={`flex items-center gap-2 ${isRecording ? 'text-red-600' : 'text-neutral-400'}`}>
          <div className={`w-2 h-2 rounded-full ${isRecording ? 'bg-red-600 animate-pulse' : 'bg-neutral-400'}`}></div>
          <span className="text-xs font-medium">
            {isRecording ? 'Recording...' : 'Ready to Record'}
          </span>
        </div>
        {isRecording && (
          <span className="text-xs text-neutral-500 ml-auto">Live Waveform</span>
        )}
      </div>

      {/* Canvas for waveform */}
      <canvas
        ref={canvasRef}
        width={300}
        height={80}
        className="w-full border border-neutral-200 rounded bg-white"
      />

      {!isRecording && (
        <div className="flex items-center justify-center gap-2 text-xs text-neutral-500 mt-2">
          <Mic className="w-3 h-3" />
          <span>Click record to see waveform</span>
        </div>
      )}
    </div>
  );
};
