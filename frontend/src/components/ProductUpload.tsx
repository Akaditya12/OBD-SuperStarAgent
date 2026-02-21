"use client";

import { useState, useCallback } from "react";
import { Upload, FileText, X, Loader2 } from "lucide-react";

interface ProductUploadProps {
  value: string;
  onChange: (text: string) => void;
  fileName: string;
  onFileNameChange: (name: string) => void;
}

const BINARY_EXTENSIONS = new Set([".pdf", ".doc", ".docx", ".pptx", ".csv", ".xlsx", ".xls"]);

export default function ProductUpload({
  value,
  onChange,
  fileName,
  onFileNameChange,
}: ProductUploadProps) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");

  const handleFile = useCallback(
    async (file: File) => {
      onFileNameChange(file.name);
      setUploadError("");

      const ext = "." + file.name.split(".").pop()?.toLowerCase();

      if (BINARY_EXTENSIONS.has(ext)) {
        setUploading(true);
        try {
          const formData = new FormData();
          formData.append("file", file);

          const res = await fetch("/api/upload/extract-text", {
            method: "POST",
            body: formData,
          });

          const data = await res.json();

          if (!res.ok) {
            setUploadError(data.error || "Failed to extract text");
            onChange("");
            return;
          }

          onChange(data.text);
        } catch (err) {
          setUploadError("Upload failed. Please try again.");
          onChange("");
        } finally {
          setUploading(false);
        }
      } else {
        const text = await file.text();
        onChange(text);
      }
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
    setUploadError("");
  };

  return (
    <div className="space-y-4">
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
            ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
            : "border-[var(--card-border)] hover:border-[var(--accent)]/50"
        }`}
      >
        <input
          type="file"
          accept=".txt,.pdf,.doc,.docx,.pptx,.md,.csv,.xlsx,.xls,.rtf,.json"
          onChange={handleFileInput}
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
          disabled={uploading}
        />
        {uploading ? (
          <>
            <Loader2 className="w-10 h-10 mx-auto mb-3 text-[var(--accent)] animate-spin" />
            <p className="text-sm text-[var(--text-secondary)]">
              Extracting text from document...
            </p>
          </>
        ) : (
          <>
            <Upload className="w-10 h-10 mx-auto mb-3 text-[var(--text-tertiary)]" />
            <p className="text-sm text-[var(--text-secondary)]">
              Drag & drop your product document here, or{" "}
              <span className="text-[var(--accent)] underline">browse</span>
            </p>
            <p className="text-xs text-[var(--text-tertiary)] mt-1">
              Supports PDF, DOCX, PPTX, TXT, CSV, XLSX, MD, JSON
            </p>
          </>
        )}
      </div>

      {/* File indicator */}
      {fileName && fileName !== "pasted-text" && (
        <div className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${
          uploadError
            ? "bg-red-50 border-red-200 dark:bg-red-500/10 dark:border-red-500/20"
            : "bg-[var(--accent-subtle)] border-[var(--accent)]/20"
        }`}>
          <FileText className={`w-4 h-4 ${uploadError ? "text-red-500" : "text-[var(--accent)]"}`} />
          <span className="text-sm text-[var(--text-primary)] flex-1 truncate">
            {fileName}
          </span>
          {uploadError && (
            <span className="text-xs text-red-500 truncate">{uploadError}</span>
          )}
          <button
            onClick={clearFile}
            className="p-1 rounded hover:bg-[var(--accent-subtle)] transition-colors"
          >
            <X className="w-3 h-3 text-[var(--text-secondary)]" />
          </button>
        </div>
      )}

      {/* Or paste text */}
      <div className="relative">
        <div className="absolute inset-x-0 top-0 flex items-center justify-center -mt-3 z-10">
          <span className="px-3 text-xs text-[var(--text-tertiary)] bg-[var(--card)]">
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
          rows={5}
          className="w-full mt-2 px-4 py-3 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 focus:ring-1 focus:ring-[var(--accent)]/20 resize-none transition-all"
        />
      </div>
    </div>
  );
}
