"use client";

import { useState, useRef } from "react";
import {
  Mic2,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Settings,
  User,
  Globe,
  Lightbulb,
  Terminal,
  BarChart3,
  Music,
  Play,
  Square,
} from "lucide-react";
import type { VoiceSelection } from "@/lib/types";

interface VoiceInfoPanelProps {
  voiceSelection: VoiceSelection;
  ttsEngine?: string;
  edgeVoice?: string;
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleCopy}
      className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] transition-all"
      title="Copy to clipboard"
    >
      {copied ? (
        <>
          <Check className="w-3 h-3 text-[var(--success)]" />
          <span className="text-[var(--success)]">Copied</span>
        </>
      ) : (
        <>
          <Copy className="w-3 h-3" />
          <span>Copy</span>
        </>
      )}
    </button>
  );
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

function getStabilityLabel(v: number): string {
  if (v < 0.3) return "Very expressive, high variation";
  if (v < 0.5) return "Creative, natural variation";
  if (v < 0.7) return "Balanced expressiveness";
  return "Consistent, stable delivery";
}

function getStyleLabel(v: number): string {
  if (v < 0.3) return "Subtle style";
  if (v < 0.5) return "Moderate expressiveness";
  if (v < 0.7) return "Highly expressive";
  return "Maximum style exaggeration";
}

function VoicePreviewButton({ url, label }: { url?: string; label?: string }) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const [playing, setPlaying] = useState(false);

  if (!url) return null;

  const toggle = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(url);
      audioRef.current.onended = () => setPlaying(false);
      audioRef.current.onerror = () => setPlaying(false);
    }
    if (playing) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  };

  return (
    <button
      onClick={toggle}
      className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-medium transition-all ${playing
        ? "bg-[var(--accent)] text-white"
        : "bg-[var(--accent-subtle)] text-[var(--accent)] hover:bg-[var(--accent)]/20"
        }`}
      title={playing ? "Stop preview" : "Play voice preview"}
    >
      {playing ? <Square className="w-3 h-3" /> : <Play className="w-3 h-3" />}
      {label || (playing ? "Stop" : "Preview")}
    </button>
  );
}

interface VoiceProfile {
  voice_id: string;
  name: string;
  description: string;
  language?: string;
  gender?: string;
  age?: string;
  accent?: string;
  preview_url?: string;
  rationale: string;
  settings: {
    stability: number;
    similarity_boost: number;
    style: number;
    speed: number;
  };
  production_notes?: string;
  is_primary: boolean;
}

export default function VoiceInfoPanel({
  voiceSelection,
  ttsEngine,
  edgeVoice,
}: VoiceInfoPanelProps) {
  const [showApiParams, setShowApiParams] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);
  const [activeVoiceIdx, setActiveVoiceIdx] = useState(0);

  const isEdgeTts = ttsEngine === "edge-tts";
  const isMurf = ttsEngine === "murf";

  // If we have alternative voices, we treat them as part of the "pool"
  const voices: VoiceProfile[] = [];
  if (voiceSelection?.selected_voice) {
    voices.push({
      ...voiceSelection.selected_voice,
      rationale: voiceSelection.rationale,
      settings: voiceSelection.voice_settings,
      production_notes: voiceSelection.audio_production_notes,
      is_primary: true
    });
  }

  if (voiceSelection?.alternative_voices) {
    voiceSelection.alternative_voices.forEach(alt => {
      voices.push({
        voice_id: alt.voice_id,
        name: alt.name,
        description: alt.reason,
        rationale: alt.reason,
        preview_url: alt.preview_url,
        settings: voiceSelection.voice_settings, // assume same settings for now
        is_primary: false,
        language: "", gender: "", age: "", accent: "" // Fallbacks for alternatives
      });
    });
  }

  // Ensure we have at least something to show
  const displayVoices: VoiceProfile[] = voices.length > 0 ? voices.slice(0, 3) : [{
    voice_id: "", name: "Unknown", description: "", language: "", gender: "", age: "", accent: "",
    rationale: "", settings: { stability: 0, similarity_boost: 0, style: 0, speed: 1 }, is_primary: true
  }];

  const currentVoice = displayVoices[activeVoiceIdx] || displayVoices[0];
  const voice_settings = currentVoice.settings;
  const elevenlabs_api_params = voiceSelection?.elevenlabs_api_params;
  const alternative_voices = voiceSelection?.alternative_voices;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-[var(--accent)]" />
          Voice Analytics
          {ttsEngine && (
            <span className={`text-[10px] px-2 py-0.5 rounded-full ${isEdgeTts
              ? "bg-green-500/10 text-green-600 border border-green-500/20"
              : "bg-purple-500/10 text-purple-600 border border-purple-500/20"
              }`}>
              {isMurf ? "Murf AI (Gen2)" : isEdgeTts ? "edge-tts (Free)" : "ElevenLabs"}
            </span>
          )}
        </h3>

        {displayVoices.length > 1 && (
          <div className="flex items-center gap-1 bg-[var(--input-bg)] p-0.5 rounded-lg border border-[var(--card-border)]">
            {displayVoices.map((v, i) => (
              <button
                key={v.voice_id || i}
                onClick={() => setActiveVoiceIdx(i)}
                className={`px-2 py-1 rounded-md text-[10px] font-medium transition-all ${activeVoiceIdx === i
                  ? "bg-[var(--accent)] text-white shadow-sm"
                  : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)]"
                  }`}
              >
                {v.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* AI Voice Analysis Card */}
      <div className="rounded-2xl border border-[var(--accent)]/20 bg-[var(--accent-subtle)] p-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-[var(--accent)]/15 flex items-center justify-center shrink-0">
            <User className="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-base font-semibold text-[var(--text-primary)]">
                {currentVoice.name}
              </span>
              {currentVoice.gender && (
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-[var(--accent)]/10 text-[var(--accent)] border border-[var(--accent)]/20">
                  {currentVoice.gender}
                </span>
              )}
              {currentVoice.age && (
                <span className="px-2 py-0.5 rounded-full text-[10px] bg-purple-500/10 text-purple-600 border border-purple-500/20">
                  {currentVoice.age}
                </span>
              )}
              <VoicePreviewButton url={currentVoice.preview_url} label="Listen" />
            </div>
            {currentVoice.description && (
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                {currentVoice.description}
              </p>
            )}
            <div className="flex items-center gap-3 mt-2 text-[10px] text-[var(--text-tertiary)]">
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {currentVoice.language || currentVoice.accent || "Multilingual"}
              </span>
              {currentVoice.accent && currentVoice.language && (
                <span>{currentVoice.accent} accent</span>
              )}
            </div>
          </div>
        </div>

        {/* TTS Engine Info */}
        {isEdgeTts && edgeVoice && (
          <div className="p-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <div className="flex items-center gap-2 text-xs">
              <Music className="w-3.5 h-3.5 text-green-500" />
              <span className="text-[var(--text-secondary)] font-medium">Rendering Engine</span>
            </div>
            <div className="mt-1.5 grid grid-cols-2 gap-2 text-[10px]">
              <div>
                <span className="text-[var(--text-tertiary)]">Engine:</span>{" "}
                <span className="text-[var(--text-primary)] font-mono">Microsoft Neural TTS</span>
              </div>
              <div>
                <span className="text-[var(--text-tertiary)]">Voice ID:</span>{" "}
                <span className="text-[var(--text-primary)] font-mono">{edgeVoice}</span>
              </div>
              <div>
                <span className="text-[var(--text-tertiary)]">Cost:</span>{" "}
                <span className="text-green-600 font-medium">Free (unlimited)</span>
              </div>
              <div>
                <span className="text-[var(--text-tertiary)]">Features:</span>{" "}
                <span className="text-[var(--text-primary)]">Prosody + Background Music</span>
              </div>
            </div>
          </div>
        )}

        {/* Why This Voice - Rationale */}
        {currentVoice.rationale && (
          <div className="p-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)]">
            <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--warning)] flex items-center gap-1">
              <Lightbulb className="w-3 h-3" />
              {currentVoice.is_primary ? "Why This Voice Was Chosen" : "Voice Characteristics"}
            </span>
            <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-relaxed">
              {currentVoice.rationale}
            </p>
          </div>
        )}
      </div>

      {/* Voice Settings Visualization */}
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
            description={getStabilityLabel(voice_settings.stability)}
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
            description={getStyleLabel(voice_settings.style)}
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
        {elevenlabs_api_params && (
          <div className="flex items-center gap-3 pt-2 text-[10px] text-[var(--text-tertiary)]">
            <span>
              Model: <span className="text-[var(--text-primary)] font-mono">{elevenlabs_api_params.model_id}</span>
            </span>
            <span>
              Format: <span className="text-[var(--text-primary)] font-mono">{elevenlabs_api_params.output_format}</span>
            </span>
          </div>
        )}
      </div>

      {/* Production Notes */}
      {currentVoice.production_notes && (
        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
          <span className="text-[10px] font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
            Production Notes
          </span>
          <p className="mt-1.5 text-xs text-[var(--text-secondary)] leading-relaxed">
            {currentVoice.production_notes}
          </p>
        </div>
      )}

      {/* API Parameters (collapsible) */}
      {elevenlabs_api_params && (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card)] overflow-hidden">
          <button
            onClick={() => setShowApiParams(!showApiParams)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-[var(--accent-subtle)] transition-colors"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-green-600 flex items-center gap-1">
              <Terminal className="w-3.5 h-3.5" />
              API Parameters
            </span>
            {showApiParams ? (
              <ChevronUp className="w-4 h-4 text-[var(--text-tertiary)]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
            )}
          </button>
          {showApiParams && (
            <div className="px-4 pb-4 space-y-3 animate-fade-in border-t border-[var(--card-border)]">
              <div className="mt-3">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] text-[var(--text-tertiary)]">JSON Parameters</span>
                  <CopyButton
                    text={JSON.stringify(
                      {
                        model_id: elevenlabs_api_params.model_id,
                        voice_id: elevenlabs_api_params.voice_id,
                        output_format: elevenlabs_api_params.output_format,
                        voice_settings: elevenlabs_api_params.voice_settings,
                      },
                      null,
                      2
                    )}
                  />
                </div>
                <pre className="p-3 rounded-xl bg-[var(--input-bg)] text-xs text-[var(--text-secondary)] font-mono overflow-x-auto whitespace-pre-wrap border border-[var(--card-border)]">
                  {JSON.stringify(
                    {
                      model_id: elevenlabs_api_params.model_id,
                      voice_id: elevenlabs_api_params.voice_id,
                      output_format: elevenlabs_api_params.output_format,
                      voice_settings: elevenlabs_api_params.voice_settings,
                    },
                    null,
                    2
                  )}
                </pre>
              </div>

              {elevenlabs_api_params.sample_api_call && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] text-[var(--text-tertiary)]">Sample curl</span>
                    <CopyButton text={elevenlabs_api_params.sample_api_call} />
                  </div>
                  <pre className="p-3 rounded-xl bg-[var(--input-bg)] text-xs text-green-600 font-mono overflow-x-auto whitespace-pre-wrap border border-[var(--card-border)]">
                    {elevenlabs_api_params.sample_api_call}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Alternative Voices */}
      {alternative_voices && alternative_voices.length > 0 && (
        <div className="rounded-2xl border border-[var(--card-border)] bg-[var(--card)] overflow-hidden">
          <button
            onClick={() => setShowAlternatives(!showAlternatives)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-[var(--accent-subtle)] transition-colors"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)]">
              Alternative Voices ({alternative_voices.length})
            </span>
            {showAlternatives ? (
              <ChevronUp className="w-4 h-4 text-[var(--text-tertiary)]" />
            ) : (
              <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
            )}
          </button>
          {showAlternatives && (
            <div className="px-4 pb-4 space-y-2 animate-fade-in border-t border-[var(--card-border)]">
              <div className="mt-3" />
              {alternative_voices.map((alt, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-xl bg-[var(--input-bg)]"
                >
                  <div className="w-6 h-6 rounded-lg bg-[var(--accent-subtle)] flex items-center justify-center text-[10px] text-[var(--text-tertiary)] shrink-0 font-medium">
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-xs text-[var(--text-primary)] font-medium">
                        {alt.name}
                      </span>
                      <VoicePreviewButton url={alt.preview_url} />
                    </div>
                    <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5">{alt.reason}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
