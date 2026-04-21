import React, { useState, useRef } from 'react';
import { FileText, Upload, X, Loader, CheckCircle } from 'lucide-react';
import { useRequirementStore } from '@/store/requirementStore';

const ACCEPTED_TYPES: Record<string, string> = {
  'application/pdf': 'PDF',
  'text/plain': 'TXT',
  'application/msword': 'DOC',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
};
const ACCEPTED_EXTENSIONS = '.pdf,.txt,.doc,.docx';

interface DocumentUploadProps {
  isLoading?: boolean;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>(
    'idle'
  );
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const { uploadDocument, addNotification } = useRequirementStore();

  const validate = (file: File): string | null => {
    if (!ACCEPTED_TYPES[file.type] && !file.name.match(/\.(pdf|txt|doc|docx)$/i)) {
      return 'Unsupported file type. Please upload PDF, TXT, DOC, or DOCX.';
    }
    if (file.size > 20 * 1024 * 1024) {
      return 'File too large. Maximum size is 20 MB.';
    }
    return null;
  };

  const handleFile = async (file: File) => {
    const err = validate(file);
    if (err) {
      setErrorMsg(err);
      addNotification({ type: 'error', message: err });
      return;
    }

    setUploadedFile(file);
    setErrorMsg(null);
    setUploadStatus('uploading');

    try {
      await uploadDocument(file);
      setUploadStatus('done');
      addNotification({ type: 'success', message: `${file.name} uploaded successfully` });
    } catch (e: unknown) {
      setUploadStatus('error');
      const msg = e instanceof Error ? e.message : 'Upload failed';
      setErrorMsg(msg);
      addNotification({ type: 'error', message: msg });
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  };

  const reset = () => {
    setUploadedFile(null);
    setUploadStatus('idle');
    setErrorMsg(null);
  };

  return (
    <div className="space-y-3">
      {uploadStatus !== 'done' && (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
          className="relative p-5 flex flex-col items-center gap-2 cursor-pointer select-none transition-colors"
          style={{
            backgroundColor: isDragging
              ? 'var(--color-primary-subtle)'
              : 'var(--color-surface)',
            border: `1px dashed ${
              isDragging ? 'var(--color-primary)' : 'var(--color-border-strong)'
            }`,
            borderRadius: 'var(--radius-md)',
          }}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS}
            onChange={handleInputChange}
            className="sr-only"
          />

          {uploadStatus === 'uploading' ? (
            <>
              <Loader
                className="w-6 h-6 animate-spin"
                style={{ color: 'var(--color-primary)' }}
              />
              <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
                Uploading {uploadedFile?.name}…
              </p>
            </>
          ) : (
            <>
              <Upload
                className="w-6 h-6"
                style={{ color: 'var(--color-text-muted)' }}
              />
              <div className="text-center">
                <p
                  className="text-sm font-medium"
                  style={{ color: 'var(--color-text-primary)' }}
                >
                  Drop a file here or{' '}
                  <span
                    className="underline"
                    style={{ color: 'var(--color-primary-text)' }}
                  >
                    browse
                  </span>
                </p>
                <p
                  className="text-xs mt-1"
                  style={{ color: 'var(--color-text-muted)' }}
                >
                  PDF, TXT, DOC, DOCX — up to 20 MB
                </p>
              </div>
            </>
          )}
        </div>
      )}

      {uploadedFile && uploadStatus === 'done' && (
        <div
          className="flex items-center gap-3 px-3 py-2.5"
          style={{
            backgroundColor: 'var(--color-success-subtle)',
            border: '1px solid var(--color-success-subtle-border)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <CheckCircle
            className="w-4 h-4 flex-shrink-0"
            style={{ color: 'var(--color-success)' }}
          />
          <div className="flex-1 min-w-0">
            <p
              className="text-sm font-medium truncate"
              style={{ color: 'var(--color-success-text)' }}
            >
              {uploadedFile.name}
            </p>
            <p
              className="text-xs"
              style={{ color: 'var(--color-success-text)', opacity: 0.85 }}
            >
              {ACCEPTED_TYPES[uploadedFile.type] ?? 'Document'} ·{' '}
              {(uploadedFile.size / 1024).toFixed(0)} KB · Ready as context
            </p>
          </div>
          <button
            type="button"
            onClick={reset}
            className="flex-shrink-0"
            style={{ color: 'var(--color-success-text)' }}
            aria-label="Remove file"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {errorMsg && uploadStatus === 'error' && (
        <div
          className="flex items-start gap-2 px-3 py-2.5"
          style={{
            backgroundColor: 'var(--color-danger-subtle)',
            border: '1px solid var(--color-danger-subtle-border)',
            borderRadius: 'var(--radius-md)',
          }}
        >
          <FileText
            className="w-4 h-4 mt-0.5 flex-shrink-0"
            style={{ color: 'var(--color-danger)' }}
          />
          <p
            className="text-sm flex-1"
            style={{ color: 'var(--color-danger-text)' }}
          >
            {errorMsg}
          </p>
          <button
            type="button"
            onClick={reset}
            style={{ color: 'var(--color-danger-text)' }}
            aria-label="Dismiss error"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
