import React, { useState, useRef, useCallback } from 'react';
import { Send, FileUp } from 'lucide-react';
import { useRequirementStore } from '@/store/requirementStore';

// Fire an incremental analysis every time the user crosses a new multiple of
// this many characters. Each call sends the FULL cumulative text so the backend
// sees a sliding window: chars 1-30, then 1-60, 1-90, …
const INCREMENTAL_CHAR_THRESHOLD = 30;

interface RequirementInputProps {
  onAnalyze: (text: string) => Promise<void>;
  // Non-blocking variant fired while the user is still typing.
  onIncrementalAnalyze?: (text: string) => void;
  isLoading: boolean;
}

export const RequirementInput: React.FC<RequirementInputProps> = ({
  onAnalyze,
  onIncrementalAnalyze,
  isLoading,
}) => {
  const [text, setText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const { uploadAudio } = useRequirementStore();

  // Tracks the highest 30-char milestone already dispatched for current text.
  // Ref (not state) so we don't fire on every render, and so deletions can
  // correctly lower the watermark without re-firing past milestones.
  const lastFiredMilestoneRef = useRef(0);
  // Debounce so a 60-char paste triggers once, not twice.
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const maybeFireIncremental = useCallback(
    (fullText: string) => {
      const len = fullText.trim().length;
      const milestone =
        Math.floor(len / INCREMENTAL_CHAR_THRESHOLD) * INCREMENTAL_CHAR_THRESHOLD;

      if (milestone < lastFiredMilestoneRef.current) {
        lastFiredMilestoneRef.current = milestone;
        return;
      }

      if (
        milestone > lastFiredMilestoneRef.current &&
        milestone >= INCREMENTAL_CHAR_THRESHOLD
      ) {
        lastFiredMilestoneRef.current = milestone;
        if (onIncrementalAnalyze) onIncrementalAnalyze(fullText.trim());
      }
    },
    [onIncrementalAnalyze]
  );

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);
    setCharCount(newText.length);

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      maybeFireIncremental(newText);
    }, 150);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      await onAnalyze(text.trim());
      setText('');
      setCharCount(0);
      lastFiredMilestoneRef.current = 0;
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
        debounceRef.current = null;
      }
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await uploadAudio(file);
      } catch (error) {
        console.error('Audio upload error:', error);
      }
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const minLength = 20;
  const isValid = text.trim().length >= minLength;

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <label
        htmlFor="requirement-input"
        className="block text-xs font-semibold uppercase tracking-wide"
        style={{ color: 'var(--color-text-secondary)' }}
      >
        Enter your requirement
      </label>

      <textarea
        id="requirement-input"
        value={text}
        onChange={handleChange}
        placeholder="The system shall provide user authentication with OAuth2…"
        rows={5}
        className="input-base"
        style={{ resize: 'vertical', minHeight: 120 }}
      />

      <div className="flex items-center justify-between">
        <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
          {charCount} character{charCount === 1 ? '' : 's'}
        </p>
        {charCount < minLength && charCount > 0 && (
          <p
            className="text-xs"
            style={{ color: 'var(--color-warning-text)' }}
          >
            {minLength - charCount} more character
            {minLength - charCount === 1 ? '' : 's'} needed
          </p>
        )}
      </div>

      <div className="flex items-center gap-2">
        <button
          type="submit"
          disabled={!isValid || isLoading}
          className="btn-primary flex-1"
        >
          <Send className="w-4 h-4" />
          {isLoading ? 'Analyzing…' : 'Analyze requirement'}
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".mp3,.wav,.m4a,.ogg,.flac"
          onChange={handleFileSelect}
          className="hidden"
        />
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          className="btn-secondary"
          title="Upload audio"
        >
          <FileUp className="w-4 h-4" />
          Audio
        </button>
      </div>
    </form>
  );
};
