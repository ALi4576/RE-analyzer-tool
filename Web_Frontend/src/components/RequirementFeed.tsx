import React, { useEffect, useRef } from 'react';
import { CheckCircle } from 'lucide-react';
import { FormalizedRequirement, ISORequirement } from '@/types/index';
import RequirementCard from './RequirementCard';

interface RequirementFeedProps {
  requirements: FormalizedRequirement | null;
  isLoading: boolean;
}

export const RequirementFeed: React.FC<RequirementFeedProps> = ({
  requirements,
  isLoading,
}) => {
  const feedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new requirements arrive
  useEffect(() => {
    if (feedRef.current) {
      feedRef.current.scrollTop = feedRef.current.scrollHeight;
    }
  }, [requirements]);

  if (isLoading) {
    return (
      <div className="space-y-3">
        {/* Loading skeleton */}
        {[1, 2, 3].map((i) => (
          <div key={i} className="card p-4 bg-neutral-50 animate-pulse">
            <div className="h-4 bg-neutral-200 rounded w-3/4 mb-3"></div>
            <div className="h-3 bg-neutral-200 rounded w-full mb-2"></div>
            <div className="h-3 bg-neutral-200 rounded w-5/6"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!requirements || requirements.total_requirements === 0) {
    return (
      <div className="card p-8 text-center bg-neutral-50">
        <CheckCircle className="w-10 h-10 text-neutral-300 mx-auto mb-2" />
        <p className="text-sm text-neutral-500">No requirements generated yet</p>
        <p className="text-xs text-neutral-400 mt-1">Speak or type to create requirements</p>
      </div>
    );
  }

  const allRequirements = requirements.iso_requirements || [];
  const completeness_score = requirements.completeness_score || 0;

  return (
    <div
      ref={feedRef}
      className="space-y-3 max-h-96 overflow-y-auto pr-2"
      style={{ scrollBehavior: 'smooth' }}
    >
      {allRequirements.length === 0 ? (
        <div className="card p-6 text-center">
          <p className="text-sm text-neutral-500">Processing requirements...</p>
        </div>
      ) : (
        <>
          {allRequirements.map((req: ISORequirement, idx: number) => (
            <RequirementCard
              key={req.requirement_id || idx}
              requirement={req}
              completeness_score={completeness_score}
              is_highlighted={false}
            />
          ))}

          {/* Completeness Score Footer */}
          <div className="card p-3 bg-gradient-to-r from-primary-50 to-primary-100 border border-primary-200 text-center sticky bottom-0">
            <p className="text-xs font-medium text-primary-900">
              Overall Completeness: <span className="font-bold">{Math.round(completeness_score * 100)}%</span>
            </p>
            <p className="text-xs text-primary-700 mt-1">
              {allRequirements.length} requirement{allRequirements.length !== 1 ? 's' : ''} generated
            </p>
          </div>
        </>
      )}
    </div>
  );
};

