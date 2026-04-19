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

export const DocumentUpload: React.FC<DocumentUploadProps> = ({ }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadStatus, setUploadStatus] = useState<'idle' | 'uploading' | 'done' | 'error'>('idle');
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
    } catch (e: any) {
      setUploadStatus('error');
      const msg = e?.message || 'Upload failed';
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
    <div className="card p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold text-neutral-900">Document Upload</h3>
          <p className="text-sm text-neutral-500">Upload PDF, TXT, DOC, or DOCX as context</p>
        </div>
        {uploadStatus === 'done' && (
          <CheckCircle className="w-5 h-5 text-green-500" />
        )}
      </div>

      {/* Drop Zone */}
      {uploadStatus !== 'done' && (
        <div
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`
            relative border-2 border-dashed rounded-lg p-6 flex flex-col items-center gap-3
            cursor-pointer transition-colors select-none
            ${isDragging
              ? 'border-blue-400 bg-blue-50'
              : 'border-neutral-300 bg-neutral-50 hover:border-neutral-400 hover:bg-neutral-100'}
          `}
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
              <Loader className="w-8 h-8 text-blue-500 animate-spin" />
              <p className="text-sm text-neutral-600">Uploading {uploadedFile?.name}…</p>
            </>
          ) : (
            <>
              <Upload className="w-8 h-8 text-neutral-400" />
              <div className="text-center">
                <p className="text-sm font-medium text-neutral-700">
                  Drop a file here or <span className="text-blue-600 underline">browse</span>
                </p>
                <p className="text-xs text-neutral-500 mt-1">PDF · TXT · DOC · DOCX — up to 20 MB</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* Uploaded file pill */}
      {uploadedFile && uploadStatus === 'done' && (
        <div className="flex items-center gap-3 bg-green-50 border border-green-200 rounded-lg px-4 py-3">
          <FileText className="w-5 h-5 text-green-600 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-green-900 truncate">{uploadedFile.name}</p>
            <p className="text-xs text-green-700">
              {ACCEPTED_TYPES[uploadedFile.type] ?? 'Document'} · {(uploadedFile.size / 1024).toFixed(0)} KB · Ready as context
            </p>
          </div>
          <button
            onClick={reset}
            className="shrink-0 text-green-600 hover:text-green-800 transition-colors"
            title="Remove"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Error */}
      {errorMsg && uploadStatus === 'error' && (
        <div className="flex items-start gap-2 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          <p className="text-sm text-red-700 flex-1">{errorMsg}</p>
          <button onClick={reset} className="text-red-500 hover:text-red-700 shrink-0">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  );
};
