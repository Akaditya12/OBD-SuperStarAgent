"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, X } from "lucide-react";

interface ProductUploadProps {
  value: string;
  onChange: (text: string) => void;
  fileName: string;
  onFileNameChange: (name: string) => void;
}

export default function ProductUpload({
  value,
  onChange,
  fileName,
  onFileNameChange,
}: ProductUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);

  const handleFile = useCallback(
    async (file: File) => {
      onFileNameChange(file.name);
      const text = await file.text();
      onChange(text);
    },
    [onChange, onFileNameChange]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragOver(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const clearFile = () => {
    onChange("");
    onFileNameChange("");
  };

  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-gray-300">
        Product Documentation
      </label>

      {/* Drop zone */}
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200 ${
          isDragOver
            ? "border-brand-500 bg-brand-500/5"
            : "border-[var(--card-border)] hover:border-brand-500/50"
        }`}
      >
        <input
          type="file"
          accept=".txt,.pdf,.doc,.docx,.pptx,.md"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
        />
        <Upload className="w-10 h-10 mx-auto mb-3 text-[var(--muted)]" />
        <p className="text-sm text-gray-400">
          Drag & drop your product document here, or{" "}
          <span className="text-brand-400 underline">browse</span>
        </p>
        <p className="text-xs text-[var(--muted)] mt-1">
          Supports .txt, .md, .pdf, .doc, .docx, .pptx
        </p>
      </div>

      {/* File indicator */}
      {fileName && (
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-brand-500/10 border border-brand-500/20">
          <FileText className="w-4 h-4 text-brand-400" />
          <span className="text-sm text-brand-300 flex-1 truncate">
            {fileName}
          </span>
          <button
            onClick={clearFile}
            className="p-1 rounded hover:bg-white/10 transition-colors"
          >
            <X className="w-3 h-3 text-gray-400" />
          </button>
        </div>
      )}

      {/* Or paste text */}
      <div className="relative">
        <div className="absolute inset-x-0 top-0 flex items-center justify-center -mt-3">
          <span className="px-3 text-xs text-[var(--muted)] bg-[var(--background)]">
            or paste product description
          </span>
        </div>
        <textarea
          value={value}
          onChange={(e) => {
            onChange(e.target.value);
            if (e.target.value && !fileName) onFileNameChange("pasted-text");
          }}
          placeholder="Paste your product documentation, features, pricing, and details here..."
          rows={6}
          className="w-full mt-2 px-4 py-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 resize-none transition-all"
        />
      </div>
    </div>
  );
}
