import React, { useState, useRef } from 'react';
import { UploadCloud, X, FileArchive, AlertCircle } from 'lucide-react';
import { projectService } from '../../services/projectService';

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  onUploadSuccess: (projectId: string) => void;
}

export const UploadModal: React.FC<UploadModalProps> = ({
  isOpen,
  onClose,
  onUploadSuccess,
}) => {
  const [dragOver, setDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [studentName, setStudentName] = useState('Alex Chen');
  const [course, setCourse] = useState('CS499 Final Project');
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Only .zip archive files are supported.');
      }
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      if (file.name.endsWith('.zip')) {
        setSelectedFile(file);
        setError(null);
      } else {
        setError('Only .zip archive files are supported.');
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setError('Please select a project ZIP file to upload.');
      return;
    }

    try {
      setIsUploading(true);
      setError(null);
      const res = await projectService.uploadProject(selectedFile, studentName, course);
      setIsUploading(false);
      onUploadSuccess(res.project_id);
      onClose();
    } catch (err: any) {
      setIsUploading(false);
      setError(err.message || 'Upload failed. Please try again.');
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-lg bg-bg-card border border-border rounded-xl p-6 shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-zinc-400 hover:text-white transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <h3 className="font-headline font-bold text-xl text-white mb-1">
          Upload Student Project
        </h3>
        <p className="text-xs text-zinc-400 mb-6">
          Upload a project ZIP file to run static AST code metrics and structural analysis.
        </p>

        {error && (
          <div className="mb-4 p-3 rounded-md bg-status-red/10 border border-status-red/30 text-status-red text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-mono text-zinc-400 mb-1">Student Author</label>
              <input
                type="text"
                value={studentName}
                onChange={(e) => setStudentName(e.target.value)}
                className="w-full py-1.5 px-3 bg-bg-main border border-border rounded-md text-xs text-white focus:outline-none focus:border-border-active"
                required
              />
            </div>
            <div>
              <label className="block text-[11px] font-mono text-zinc-400 mb-1">Course / Assessment</label>
              <input
                type="text"
                value={course}
                onChange={(e) => setCourse(e.target.value)}
                className="w-full py-1.5 px-3 bg-bg-main border border-border rounded-md text-xs text-white focus:outline-none focus:border-border-active"
                required
              />
            </div>
          </div>

          {/* Dropzone */}
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-all ${
              dragOver
                ? 'border-primary bg-primary/5'
                : 'border-border hover:border-border-active hover:bg-bg-main/50'
            }`}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".zip"
              className="hidden"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center gap-2">
                <FileArchive className="w-10 h-10 text-primary" />
                <span className="text-sm font-medium text-white">{selectedFile.name}</span>
                <span className="text-[11px] text-zinc-500 font-mono">
                  {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                </span>
              </div>
            ) : (
              <div className="flex flex-col items-center gap-2">
                <UploadCloud className="w-10 h-10 text-zinc-400" />
                <span className="text-sm font-medium text-white">
                  Drag and drop project <strong className="text-primary">.zip</strong> here
                </span>
                <span className="text-xs text-zinc-500">or click to browse local files</span>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="py-2 px-4 rounded-md bg-zinc-800 text-zinc-300 text-xs font-semibold hover:bg-zinc-700 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !selectedFile}
              className="py-2 px-5 rounded-md bg-primary text-white text-xs font-semibold hover:bg-primary-hover transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {isUploading ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Uploading...</span>
                </>
              ) : (
                <span>Start Analysis</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
