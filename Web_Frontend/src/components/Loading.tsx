import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  message?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  message,
}) => {
  const dim = { sm: 20, md: 32, lg: 48 }[size];

  return (
    <div
      className="flex flex-col items-center justify-center gap-3 py-8"
      role="status"
      aria-live="polite"
    >
      <div
        className="animate-spin rounded-full border-2"
        style={{
          width: dim,
          height: dim,
          borderColor: 'var(--color-border)',
          borderTopColor: 'var(--color-primary)',
        }}
      />
      {message && (
        <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
          {message}
        </p>
      )}
    </div>
  );
};

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = 'h-4 w-full',
}) => <div className={`${className} skeleton`} />;
