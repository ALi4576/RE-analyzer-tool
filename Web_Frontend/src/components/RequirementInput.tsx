import React, { useState, useRef, useEffect } from 'react';
import { Send, FileUp } from 'lucide-react';

interface RequirementInputProps {
  onAnalyze: (text: string) => Promise<void>;
  isLoading: boolean;
}

export const RequirementInput: React.FC<RequirementInputProps> = ({
  onAnalyze,
  isLoading,
}) => {
  const [text, setText] = useState('');
  const [charCount, setCharCount] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      if (charCount > 0 && charCount % 50 === 0) {
        onAnalyze(text.trim());
      }
    }, 0); // Trigger analysis immediately after every 50 characters

    return () => clearTimeout(delayDebounceFn);
  }, [charCount, text, onAnalyze]);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newText = e.target.value;
    setText(newText);
    setCharCount(newText.length);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      await onAnalyze(text.trim());
      setText('');
      setCharCount(0);
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

  const minLength = 1; // Allow analysis even with 1 character
  const isValid = text.length > 0;

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
