import React, { useState, useRef, useCallback } from 'react';
import { Send, FileUp } from 'lucide-react';

// Fire an incremental analysis every time the user crosses a new
// multiple of this many characters. Each call sends the FULL cumulative
// text so the backend sees a sliding window: chars 1-30, then 1-60, 1-90...
const INCREMENTAL_CHAR_THRESHOLD = 30;

interface RequirementInputProps {
  onAnalyze: (text: string) => Promise<void>;
  // Non-blocking variant fired while the user is still typing.
  // Synchronous (returns void) so the textarea onChange never awaits it.
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

  // Tracks the highest 30-char milestone we've already dispatched for the
  // current text. Using a ref (not state) so we don't fire on every render,
  // and so that shrinking text (deletions) correctly lowers the watermark
  // without re-firing milestones the user has already passed.
  const lastFiredMilestoneRef = useRef(0);
  // Debounce timer handle — 150ms pause means we don't fire mid-keystroke
  // burst (a 60-char paste triggers once, not twice).
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const maybeFireIncremental = useCallback(
    (fullText: string) => {
      const len = fullText.trim().length;
      const milestone =
        Math.floor(len / INCREMENTAL_CHAR_THRESHOLD) * INCREMENTAL_CHAR_THRESHOLD;

      // If the user deleted below a previous milestone, reset the watermark
      // so crossing that boundary again will re-trigger analysis.
      if (milestone < lastFiredMilestoneRef.current) {
        lastFiredMilestoneRef.current = milestone;
        return;
      }

      // Only fire when we've crossed into a new, strictly-higher milestone
      // (and we have at least one full threshold's worth of content).
      if (milestone > lastFiredMilestoneRef.current && milestone >= INCREMENTAL_CHAR_THRESHOLD) {
        lastFiredMilestoneRef.current = milestone;
        if (onIncrementalAnalyze) {
          onIncrementalAnalyze(fullText.trim());
        }
      }
    },
    [onIncrementalAnalyze]
  );

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);
    setCharCount(newText.length);

    // Debounce the incremental trigger: coalesces rapid keystrokes / pastes
    // so a single 90-char paste does NOT fan out into three overlapping
    // network requests. The store also cancels stale in-flight requests.
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

  const handleDocumentUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to upload document');
      }

      const data = await response.json();
      setText(data.context);
      setCharCount(data.context.length);
    } catch (error) {
      console.error('Document upload error:', error);
      alert('Failed to upload document');
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const supportedTypes = [
        'text/plain',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];
      if (supportedTypes.includes(file.type)) {
        await handleDocumentUpload(file);
      } else {
        alert('Unsupported file type. Please upload a .txt, .pdf, or .doc file.');
      }
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const minLength = 20; // Match the backend's input-length gate
  const isValid = text.trim().length >= minLength;

  return (
    <div className="w-full">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Input Area */}
        <div className="card p-6 border-2 border-neutral-200 hover:border-neutral-300 transition-colors">
          <label htmlFor="requirement-input" className="block text-sm font-semibold text-neutral-900 mb-3">
            Enter Your Requirement
          </label>

          <textarea
            id="requirement-input"
            value={text}
            onChange={handleChange}
            placeholder="The system shall provide user authentication with OAuth2 security..."
            className="input-base resize-none h-32"
          />

          {/* Input Info */}
          <div className="mt-3 flex items-center justify-between">
            <p className="text-xs text-neutral-500">
              {charCount} characters
            </p>
            {charCount < minLength && charCount > 0 && (
              <p className="text-xs text-warning">
                {minLength - charCount} more characters needed
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3">
          <button
            type="submit"
            disabled={!isValid || isLoading}
            className="btn-primary flex items-center gap-2 flex-1"
          >
            <Send className="w-4 h-4" />
            {isLoading ? 'Analyzing...' : 'Analyze Requirement'}
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
            className="btn-secondary px-6 flex items-center gap-2"
          >
            <FileUp className="w-4 h-4" />
            Upload Audio
          </button>
        </div>

        {/* Helper Text */}
        <p className="text-xs text-neutral-500 text-center">
          Upload audio or paste requirement text. Our AI agents will analyze for quality issues, logical gaps, and ISO 29148 compliance.
        </p>
      </form>
    </div>
  );
};
