import React from 'react';
import { AlertCircle } from 'lucide-react';

interface SmellMeterProps {
  smellScore: number; // 0-1 range
  label?: string;
}

export const SmellMeter: React.FC<SmellMeterProps> = ({ 
  smellScore, 
  label = 'Quality Score'
}) => {
  // Determine color based on score (inverted: high score = bad)
  // 0-0.3: Green (good)
  // 0.3-0.6: Yellow (warning)
  // 0.6-1.0: Red (critical)
  
  const getColor = () => {
    if (smellScore < 0.3) return { bg: 'bg-emerald-500', text: 'text-emerald-700', label: 'Good' };
    if (smellScore < 0.6) return { bg: 'bg-amber-500', text: 'text-amber-700', label: 'Warning' };
    return { bg: 'bg-red-500', text: 'text-red-700', label: 'Critical' };
  };

  const color = getColor();
  const percentage = Math.min(smellScore * 100, 100);

  return (
    <div className="card p-4 bg-neutral-50">
      <div className="flex items-center justify-between mb-3">
        <label className="text-sm font-medium text-neutral-600">{label}</label>
        <span className={`text-xs font-semibold px-2 py-1 rounded ${color.text} bg-opacity-10`}>
          {color.label}
        </span>
      </div>

      {/* Animated Gauge */}
      <div className="relative h-8 bg-gradient-to-r from-emerald-200 via-amber-200 to-red-200 rounded-full overflow-hidden shadow-inner">
        <div
          className={`h-full transition-all duration-500 ease-out ${color.bg} rounded-full flex items-center justify-end pr-2`}
          style={{ width: `${percentage}%` }}
        >
          {percentage > 15 && (
            <span className="text-xs font-bold text-white drop-shadow-md">
              {(smellScore * 100).toFixed(0)}%
            </span>
          )}
        </div>
      </div>

      {/* Feedback Text */}
      <div className="mt-2 flex items-start gap-2">
        {smellScore < 0.3 ? (
          <p className="text-xs text-emerald-700">✓ Requirement is well-defined and clear</p>
        ) : smellScore < 0.6 ? (
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3 h-3 text-amber-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-700">Some ambiguities detected. Review and clarify.</p>
          </div>
        ) : (
          <div className="flex items-start gap-2">
            <AlertCircle className="w-3 h-3 text-red-600 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-red-700">Multiple quality issues. Requires clarification.</p>
          </div>
        )}
      </div>
    </div>
  );
};
