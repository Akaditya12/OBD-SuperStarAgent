"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Star, Clock, Hash, Download, FileJson, FileText, Languages, Loader2 } from "lucide-react";
import type { Script } from "@/lib/types";

interface ScriptReviewProps {
  scripts: Script[];
  bestVariantId?: number;
  sessionId?: string;
}

function highlightAudioTags(text: string | undefined | null) {
  if (!text) return null;
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
  const [translating, setTranslating] = useState(false);
  const [translation, setTranslation] = useState<string | null>(null);
  const [showTranslation, setShowTranslation] = useState(false);

  const isNonEnglish = script.language && !script.language.toLowerCase().startsWith("english");

  const handleTranslate = async () => {
    if (translation) {
      setShowTranslation(!showTranslation);
      return;
    }
    setTranslating(true);
    try {
      const res = await fetch("/api/translate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          text: script.full_script || `${script.hook}\n${script.body}\n${script.cta}`,
          source_language: script.language,
        }),
      });
      if (!res.ok) throw new Error("Translation failed");
      const data = await res.json();
      setTranslation(data.translated);
      setShowTranslation(true);
    } catch {
      setTranslation("Translation failed. Please try again.");
      setShowTranslation(true);
    } finally {
      setTranslating(false);
    }
  };

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

          {/* Translate button */}
          {isNonEnglish && (
            <button
              onClick={handleTranslate}
              disabled={translating}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all ${
                showTranslation
                  ? "bg-blue-500/15 text-blue-400 border border-blue-500/30"
                  : "bg-[var(--input-bg)] text-[var(--text-tertiary)] border border-[var(--card-border)] hover:text-blue-400 hover:border-blue-500/30"
              }`}
            >
              {translating ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <Languages className="w-3 h-3" />
              )}
              {translating ? "Translating..." : showTranslation ? "Hide Translation" : "Translate to English"}
            </button>
          )}

          {/* Translation result */}
          {showTranslation && translation && (
            <div className="p-3 rounded-lg bg-blue-500/5 border border-blue-500/20">
              <span className="text-[10px] font-semibold uppercase tracking-wider text-blue-400 flex items-center gap-1">
                <Languages className="w-3 h-3" />
                English Translation
              </span>
              <p className="mt-1.5 text-sm text-gray-300 leading-relaxed whitespace-pre-wrap">
                {translation}
              </p>
            </div>
          )}

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

          {/* Audio tags used */}
          {script.audio_tags_used && script.audio_tags_used.length > 0 && (
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-purple-400">
                Audio Tags Used
              </span>
              <div className="mt-1 flex flex-wrap gap-1">
                {script.audio_tags_used.map((tag, i) => (
                  <span
                    key={i}
                    className="inline-block px-2 py-0.5 rounded text-xs font-mono bg-purple-500/15 text-purple-300 border border-purple-500/20"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

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

function triggerDownload(filename: string, content: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadScriptsAsJson(scripts: Script[], sessionId: string) {
  const content = JSON.stringify({ scripts }, null, 2);
  triggerDownload(`obd_scripts_${sessionId}.json`, content, "application/json");
}

function downloadScriptsAsText(scripts: Script[], sessionId: string) {
  const lines: string[] = [];
  for (const s of scripts) {
    lines.push("=".repeat(60));
    lines.push(`VARIANT ${s.variant_id}: ${s.theme}`);
    lines.push(`Language: ${s.language}  |  Words: ${s.word_count}  |  ~${s.estimated_duration_seconds}s`);
    lines.push("=".repeat(60));
    lines.push(`\n--- HOOK (0-5s) ---\n${s.hook}`);
    lines.push(`\n--- BODY (5-23s) ---\n${s.body}`);
    lines.push(`\n--- CTA (23-30s) ---\n${s.cta}`);
    lines.push(`\n--- FULL SCRIPT ---\n${s.full_script}`);
    lines.push(`\n--- FALLBACK 1 (Urgency) ---\n${s.fallback_1}`);
    lines.push(`\n--- FALLBACK 2 (Psychology) ---\n${s.fallback_2}`);
    lines.push(`\n--- POLITE CLOSURE ---\n${s.polite_closure}`);
    lines.push("");
  }
  triggerDownload(`obd_scripts_${sessionId}.txt`, lines.join("\n"), "text/plain");
}

export default function ScriptReview({
  scripts,
  bestVariantId,
  sessionId,
}: ScriptReviewProps) {
  const hasNonEnglish = scripts?.some(
    (s) => s.language && !s.language.toLowerCase().startsWith("english")
  );

  if (!scripts || scripts.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--muted)]">
        No scripts generated yet.
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider flex items-center gap-2">
          Generated Scripts ({scripts.length} variants)
          {hasNonEnglish && (
            <span className="text-[10px] font-normal normal-case tracking-normal px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Languages className="w-3 h-3 inline mr-1" />
              Use translate button on each variant
            </span>
          )}
        </h3>
        <div className="flex items-center gap-2">
          <button
            onClick={() => downloadScriptsAsJson(scripts, sessionId || "export")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-brand-400 bg-brand-500/10 border border-brand-500/20 hover:bg-brand-500/20 transition-all"
            title="Download as JSON"
          >
            <FileJson className="w-3.5 h-3.5" />
            JSON
          </button>
          <button
            onClick={() => downloadScriptsAsText(scripts, sessionId || "export")}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-purple-400 bg-purple-500/10 border border-purple-500/20 hover:bg-purple-500/20 transition-all"
            title="Download as Text"
          >
            <FileText className="w-3.5 h-3.5" />
            TXT
          </button>
          <button
            onClick={() => {
              downloadScriptsAsJson(scripts, sessionId || "export");
              downloadScriptsAsText(scripts, sessionId || "export");
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-[var(--success)] bg-[var(--success)]/10 border border-[var(--success)]/20 hover:bg-[var(--success)]/20 transition-all"
            title="Download All"
          >
            <Download className="w-3.5 h-3.5" />
            All
          </button>
        </div>
      </div>
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
