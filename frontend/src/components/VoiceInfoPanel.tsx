"use client";

import { useState } from "react";
import {
  Mic2,
  User,
  Globe,
  Lightbulb,
  BarChart3,
  Music,
  Settings,
} from "lucide-react";
import type { VoiceSelection, HookPreviewResult } from "@/lib/types";

interface VoiceInfoPanelProps {
  voiceSelection: VoiceSelection;
  ttsEngine?: string;
  edgeVoice?: string;
  hookPreviews?: HookPreviewResult;
}

function SettingBar({
  label,
  value,
  color,
  description,
}: {
  label: string;
  value: number | undefined | null;
  color: string;
  description?: string;
}) {
  const safeValue = typeof value === "number" ? value : 0;
  const pct = Math.round(safeValue * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-[var(--text-tertiary)]">{label}</span>
        <span className="text-[var(--text-primary)] font-mono font-medium">{safeValue.toFixed(2)}</span>
      </div>
      <div className="h-2 rounded-full bg-[var(--input-bg)] overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-700 ease-out ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      {description && (
        <p className="text-[10px] text-[var(--text-tertiary)]">{description}</p>
      )}
    </div>
  );
}

function getEngineLabel(engine?: string): string {
  if (engine === "murf") return "Murf AI (Gen2)";
  if (engine === "edge-tts") return "edge-tts (Free)";
  if (engine === "elevenlabs") return "ElevenLabs";
  return "Auto";
}

function getEngineBadgeClass(engine?: string): string {
  if (engine === "murf") return "bg-orange-500/10 text-orange-600 border border-orange-500/20";
  if (engine === "edge-tts") return "bg-green-500/10 text-green-600 border border-green-500/20";
  if (engine === "elevenlabs") return "bg-purple-500/10 text-purple-600 border border-purple-500/20";
  return "bg-gray-500/10 text-gray-600 border border-gray-500/20";
}

export default function VoiceInfoPanel({
  voiceSelection,
  ttsEngine,
  edgeVoice,
  hookPreviews,
}: VoiceInfoPanelProps) {
  const [activeVoiceIdx, setActiveVoiceIdx] = useState(0);

  const actualEngine = hookPreviews?.tts_engine || ttsEngine;
  const voicePool = hookPreviews?.voice_pool || [];

  const productionNotes = voiceSelection?.audio_production_notes || "";
  const voice_settings = voiceSelection?.voice_settings || {
    stability: 0.5,
    similarity_boost: 0.5,
    style: 0.5,
    speed: 1.0,
  };

  const currentPoolVoice = voicePool[activeVoiceIdx];
  const currentVoiceName = currentPoolVoice?.voice_label || voiceSelection?.selected_voice?.name || "Voice";

  const rawRationale = voiceSelection?.rationale || "";
  const rationale = (() => {
    if (voicePool.length > 0) {
      const engineLabel = getEngineLabel(actualEngine || "");
      return `${currentVoiceName} was selected by the ${engineLabel} engine based on the campaign's target market, language, and audience profile. ${
        productionNotes || "The voice is optimized for clarity, warmth, and natural delivery in promotional OBD calls."
      }`;
    }
    return rawRationale;
  })();

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-[var(--accent)]" />
          Voice Analytics
          {actualEngine && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full ${getEngineBadgeClass(actualEngine)}`}>
              {getEngineLabel(actualEngine)}
            </span>
          )}
        </h3>

        {voicePool.length > 1 && (
          <div className="flex items-center gap-1 bg-[var(--input-bg)] p-0.5 rounded-lg border border-[var(--card-border)]">
            {voicePool.map((v, i) => (
              <button
                key={v.voice_index}
                onClick={() => setActiveVoiceIdx(i)}
                className={`px-2.5 py-1 rounded-md text-[10px] font-medium transition-all ${
                  activeVoiceIdx === i
                    ? "bg-[var(--accent)] text-white shadow-sm"
                    : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                }`}
              >
                {v.voice_label}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Voice Card */}
      <div className="rounded-2xl border border-[var(--accent)]/20 bg-[var(--accent-subtle)] p-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/15 flex items-center justify-center shrink-0">
            <User className="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-base font-semibold text-[var(--text-primary)]">
                {currentPoolVoice?.voice_label || voiceSelection?.selected_voice?.name || "Voice"}
              </span>
              {actualEngine && (
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20">
                  {getEngineLabel(actualEngine)}
                </span>
              )}
            </div>
            <p className="text-xs text-[var(--text-secondary)] mt-1">
              {voicePool.length > 0
                ? `Voice ${(currentPoolVoice?.voice_index || 0)} of ${voicePool.length} available for this campaign`
                : voiceSelection?.selected_voice?.description || ""}
            </p>
            <div className="flex items-center gap-3 mt-2 text-[10px] text-[var(--text-tertiary)]">
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {voiceSelection?.selected_voice?.language || "Multilingual"}
              </span>
              {voiceSelection?.selected_voice?.accent && (
                <span>{voiceSelection.selected_voice.accent} accent</span>
              )}
            </div>
          </div>
        </div>

        {/* TTS Engine Detail */}
        {actualEngine && (
          <div className="p-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div className="flex items-center gap-2 text-xs">
              <Music className="w-3.5 h-3.5 text-[var(--accent)]" />
              <span className="text-[var(--text-secondary)] font-medium">Rendering Engine</span>
            </div>
            <div className="mt-1.5 grid grid-cols-2 gap-2 text-[10px]">
              <div>
                <span className="text-[var(--text-tertiary)]">Engine:</span>{" "}
                <span className="text-[var(--text-primary)] font-mono">{getEngineLabel(actualEngine)}</span>
              </div>
              <div>
                <span className="text-[var(--text-tertiary)]">Voices:</span>{" "}
                <span className="text-[var(--text-primary)] font-mono">{voicePool.length || 1} available</span>
              </div>
              {edgeVoice && (
                <div className="col-span-2">
                  <span className="text-[var(--text-tertiary)]">Voice ID:</span>{" "}
                  <span className="text-[var(--text-primary)] font-mono">{edgeVoice}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Why This Voice */}
        {rationale && (
          <div className="p-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--warning)] flex items-center gap-1">
              <Lightbulb className="w-3 h-3" />
              Why This Voice Was Chosen
            </span>
            <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-relaxed">
              {rationale}
            </p>
          </div>
        )}
      </div>

      {/* Voice Parameters */}
      <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card)] p-4 space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1">
          <Settings className="w-3.5 h-3.5" />
          Voice Parameters
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <SettingBar
            label="Stability"
            value={voice_settings.stability}
            color="bg-blue-500"
            description={
              voice_settings.stability < 0.3 ? "Very expressive, high variation" :
              voice_settings.stability < 0.5 ? "Creative, natural variation" :
              voice_settings.stability < 0.7 ? "Balanced expressiveness" :
              "Consistent, stable delivery"
            }
          />
          <SettingBar
            label="Similarity Boost"
            value={voice_settings.similarity_boost}
            color="bg-purple-500"
            description={voice_settings.similarity_boost > 0.7 ? "Close to original voice" : "More creative freedom"}
          />
          <SettingBar
            label="Style Expressiveness"
            value={voice_settings.style}
            color="bg-pink-500"
            description={
              voice_settings.style < 0.3 ? "Subtle style" :
              voice_settings.style < 0.5 ? "Moderate expressiveness" :
              voice_settings.style < 0.7 ? "Highly expressive" :
              "Maximum style exaggeration"
            }
          />
          <SettingBar
            label="Speed"
            value={voice_settings.speed}
            color="bg-emerald-500"
            description={
              voice_settings.speed > 1.05 ? "Faster than normal" :
              voice_settings.speed < 0.95 ? "Slower, more deliberate" :
              "Normal speaking pace"
            }
          />
        </div>
      </div>

      {/* Production Notes */}
      {productionNotes && (
        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
            Production Notes
          </span>
          <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-relaxed">
            {productionNotes}
          </p>
        </div>
      )}
    </div>
  );
}
