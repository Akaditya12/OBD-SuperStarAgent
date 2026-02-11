"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Star, Clock, Hash } from "lucide-react";
import type { Script } from "@/lib/types";

interface ScriptReviewProps {
  scripts: Script[];
  bestVariantId?: number;
}

function highlightAudioTags(text: string) {
  // Highlight ElevenLabs V3 audio tags
  return text.split(/(\[.*?\])/).map((part, i) => {
    if (part.startsWith("[") && part.endsWith("]")) {
      return (
        <span
          key={i}
          className="inline-block px-1.5 py-0.5 mx-0.5 rounded text-xs font-mono bg-purple-500/15 text-purple-300 border border-purple-500/20"
        >
          {part}
        </span>
      );
    }
    // Highlight CAPS words
    return part.split(/(\b[A-Z]{2,}\b)/).map((word, j) => {
      if (/^[A-Z]{2,}$/.test(word)) {
        return (
          <span key={`${i}-${j}`} className="font-bold text-brand-300">
            {word}
          </span>
        );
      }
      return <span key={`${i}-${j}`}>{word}</span>;
    });
  });
}

function ScriptCard({
  script,
  isBest,
}: {
  script: Script;
  isBest: boolean;
}) {
  const [expanded, setExpanded] = useState(isBest);

  return (
    <div
      className={`rounded-xl border transition-all duration-200 ${
        isBest
          ? "border-[var(--warning)]/30 bg-[var(--warning)]/5"
          : "border-[var(--card-border)] bg-[var(--card)]"
      }`}
    >
      {/* Header */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-3 p-4 text-left"
      >
        <div
          className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
            isBest
              ? "bg-[var(--warning)]/15 text-[var(--warning)]"
              : "bg-brand-500/10 text-brand-400"
          }`}
        >
          {script.variant_id}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-gray-200 truncate">
              {script.theme}
            </span>
            {isBest && (
              <span className="flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-[var(--warning)]/15 text-[var(--warning)] border border-[var(--warning)]/20">
                <Star className="w-3 h-3" /> Best
              </span>
            )}
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <span className="flex items-center gap-1 text-xs text-[var(--muted)]">
              <Hash className="w-3 h-3" />
              {script.word_count} words
            </span>
            <span className="flex items-center gap-1 text-xs text-[var(--muted)]">
              <Clock className="w-3 h-3" />~{script.estimated_duration_seconds}s
            </span>
            <span className="text-xs text-[var(--muted)]">
              {script.language}
            </span>
          </div>
        </div>
        {expanded ? (
          <ChevronUp className="w-4 h-4 text-gray-500" />
        ) : (
          <ChevronDown className="w-4 h-4 text-gray-500" />
        )}
      </button>

      {/* Expanded content */}
      {expanded && (
        <div className="px-4 pb-4 space-y-3 animate-fade-in">
          <div className="h-px bg-[var(--card-border)]" />

          {/* Hook */}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-red-400">
              Hook (0-5s)
            </span>
            <p className="mt-1 text-sm text-gray-300 leading-relaxed">
              {highlightAudioTags(script.hook)}
            </p>
          </div>

          {/* Body */}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-brand-400">
              Body (5-23s)
            </span>
            <p className="mt-1 text-sm text-gray-300 leading-relaxed">
              {highlightAudioTags(script.body)}
            </p>
          </div>

          {/* CTA */}
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--success)]">
              CTA (23-30s)
            </span>
            <p className="mt-1 text-sm text-gray-300 leading-relaxed">
              {highlightAudioTags(script.cta)}
            </p>
          </div>

          <div className="h-px bg-[var(--card-border)]" />

          {/* Fallbacks */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            <div className="p-3 rounded-lg bg-[var(--background)]">
              <span className="text-xs font-semibold uppercase tracking-wider text-[var(--warning)]">
                Fallback 1 (Urgency)
              </span>
              <p className="mt-1 text-xs text-gray-400 leading-relaxed">
                {highlightAudioTags(script.fallback_1)}
              </p>
            </div>
            <div className="p-3 rounded-lg bg-[var(--background)]">
              <span className="text-xs font-semibold uppercase tracking-wider text-orange-400">
                Fallback 2 (Psychology)
              </span>
              <p className="mt-1 text-xs text-gray-400 leading-relaxed">
                {highlightAudioTags(script.fallback_2)}
              </p>
            </div>
          </div>

          {/* Polite closure */}
          <div className="p-3 rounded-lg bg-[var(--background)]">
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Polite Closure
            </span>
            <p className="mt-1 text-xs text-gray-400 leading-relaxed">
              {highlightAudioTags(script.polite_closure)}
            </p>
          </div>

          {/* Full script */}
          <details className="group">
            <summary className="text-xs text-[var(--muted)] cursor-pointer hover:text-gray-400 transition-colors">
              View full combined script
            </summary>
            <div className="mt-2 p-3 rounded-lg bg-[var(--background)] border border-[var(--card-border)]">
              <p className="text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {highlightAudioTags(script.full_script)}
              </p>
            </div>
          </details>
        </div>
      )}
    </div>
  );
}

export default function ScriptReview({
  scripts,
  bestVariantId,
}: ScriptReviewProps) {
  if (!scripts || scripts.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--muted)]">
        No scripts generated yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
        Generated Scripts ({scripts.length} variants)
      </h3>
      {scripts.map((script) => (
        <ScriptCard
          key={script.variant_id}
          script={script}
          isBest={script.variant_id === bestVariantId}
        />
      ))}
    </div>
  );
}
