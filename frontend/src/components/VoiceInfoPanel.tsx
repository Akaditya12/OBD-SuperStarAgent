"use client";

import { useState } from "react";
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
} from "lucide-react";
import type { VoiceSelection } from "@/lib/types";

interface VoiceInfoPanelProps {
  voiceSelection: VoiceSelection;
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
      className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-gray-400 hover:text-white hover:bg-white/5 transition-all"
      title="Copy to clipboard"
    >
      {copied ? (
        <>
          <Check className="w-3 h-3 text-green-400" />
          <span className="text-green-400">Copied</span>
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
}: {
  label: string;
  value: number | undefined | null;
  color: string;
}) {
  const safeValue = typeof value === "number" ? value : 0;
  const pct = Math.round(safeValue * 100);
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-gray-400">{label}</span>
        <span className="text-gray-300 font-mono">{safeValue.toFixed(2)}</span>
      </div>
      <div className="h-2 rounded-full bg-white/5 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function VoiceInfoPanel({
  voiceSelection,
}: VoiceInfoPanelProps) {
  const [showApiParams, setShowApiParams] = useState(false);
  const [showAlternatives, setShowAlternatives] = useState(false);

  const selected_voice = voiceSelection?.selected_voice || {
    voice_id: "", name: "Unknown", description: "", language: "", gender: "", age: "", accent: "",
  };
  const voice_settings = voiceSelection?.voice_settings || {
    stability: 0, similarity_boost: 0, style: 0, speed: 1,
  };
  const elevenlabs_api_params = voiceSelection?.elevenlabs_api_params;
  const rationale = voiceSelection?.rationale || "";
  const alternative_voices = voiceSelection?.alternative_voices;
  const audio_production_notes = voiceSelection?.audio_production_notes;

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider flex items-center gap-2">
        <Mic2 className="w-4 h-4" />
        ElevenLabs Voice Selection
      </h3>

      {/* Selected Voice Card */}
      <div className="rounded-xl border border-brand-500/20 bg-brand-500/5 p-4 space-y-3">
        <div className="flex items-start gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-500/15 flex items-center justify-center shrink-0">
            <User className="w-5 h-5 text-brand-400" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-base font-semibold text-white">
                {selected_voice.name}
              </span>
              <span className="px-2 py-0.5 rounded-full text-xs bg-brand-500/15 text-brand-300 border border-brand-500/20">
                {selected_voice.gender}
              </span>
              {selected_voice.age && (
                <span className="px-2 py-0.5 rounded-full text-xs bg-purple-500/15 text-purple-300 border border-purple-500/20">
                  {selected_voice.age}
                </span>
              )}
            </div>
            <p className="text-sm text-gray-400 mt-1">
              {selected_voice.description}
            </p>
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
              <span className="flex items-center gap-1">
                <Globe className="w-3 h-3" />
                {selected_voice.language || selected_voice.accent || "Multilingual"}
              </span>
              {selected_voice.accent && selected_voice.language && (
                <span>{selected_voice.accent} accent</span>
              )}
              <span className="font-mono text-gray-600">
                ID: {selected_voice.voice_id}
              </span>
            </div>
          </div>
        </div>

        {/* Rationale */}
        <div className="p-3 rounded-lg bg-[var(--background)]">
          <span className="text-xs font-semibold uppercase tracking-wider text-[var(--warning)] flex items-center gap-1">
            <Lightbulb className="w-3 h-3" />
            Why This Voice
          </span>
          <p className="mt-1 text-sm text-gray-300 leading-relaxed">
            {rationale}
          </p>
        </div>
      </div>

      {/* Voice Settings */}
      <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] p-4 space-y-3">
        <h4 className="text-xs font-semibold uppercase tracking-wider text-gray-400 flex items-center gap-1">
          <Settings className="w-3 h-3" />
          Voice Parameters
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <SettingBar
            label="Stability"
            value={voice_settings.stability}
            color="bg-blue-500"
          />
          <SettingBar
            label="Similarity Boost"
            value={voice_settings.similarity_boost}
            color="bg-purple-500"
          />
          <SettingBar
            label="Style"
            value={voice_settings.style}
            color="bg-pink-500"
          />
          <SettingBar
            label="Speed"
            value={voice_settings.speed}
            color="bg-green-500"
          />
        </div>
        {elevenlabs_api_params && (
          <div className="flex items-center gap-3 pt-2 text-xs text-gray-500">
            <span>
              Model: <span className="text-gray-300 font-mono">{elevenlabs_api_params.model_id}</span>
            </span>
            <span>
              Format: <span className="text-gray-300 font-mono">{elevenlabs_api_params.output_format}</span>
            </span>
          </div>
        )}
      </div>

      {/* ElevenLabs API Call */}
      {elevenlabs_api_params && (
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] overflow-hidden">
          <button
            onClick={() => setShowApiParams(!showApiParams)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-green-400 flex items-center gap-1">
              <Terminal className="w-3 h-3" />
              ElevenLabs API Call Parameters
            </span>
            {showApiParams ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>
          {showApiParams && (
            <div className="px-4 pb-4 space-y-3 animate-fade-in">
              <div className="h-px bg-[var(--card-border)]" />

              {/* JSON params */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-xs text-gray-500">API Parameters (JSON)</span>
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
                <pre className="p-3 rounded-lg bg-[var(--background)] text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap border border-[var(--card-border)]">
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

              {/* Sample curl */}
              {elevenlabs_api_params.sample_api_call && (
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs text-gray-500">Sample API Call</span>
                    <CopyButton text={elevenlabs_api_params.sample_api_call} />
                  </div>
                  <pre className="p-3 rounded-lg bg-[var(--background)] text-xs text-green-300/80 font-mono overflow-x-auto whitespace-pre-wrap border border-[var(--card-border)]">
                    {elevenlabs_api_params.sample_api_call}
                  </pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Production Notes */}
      {audio_production_notes && (
        <div className="p-3 rounded-lg bg-[var(--background)] border border-[var(--card-border)]">
          <span className="text-xs font-semibold uppercase tracking-wider text-gray-500">
            Production Notes
          </span>
          <p className="mt-1 text-xs text-gray-400 leading-relaxed">
            {audio_production_notes}
          </p>
        </div>
      )}

      {/* Alternative Voices */}
      {alternative_voices && alternative_voices.length > 0 && (
        <div className="rounded-xl border border-[var(--card-border)] bg-[var(--card)] overflow-hidden">
          <button
            onClick={() => setShowAlternatives(!showAlternatives)}
            className="w-full flex items-center justify-between p-4 text-left hover:bg-white/[0.02] transition-colors"
          >
            <span className="text-xs font-semibold uppercase tracking-wider text-gray-400">
              Alternative Voices ({alternative_voices.length})
            </span>
            {showAlternatives ? (
              <ChevronUp className="w-4 h-4 text-gray-500" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-500" />
            )}
          </button>
          {showAlternatives && (
            <div className="px-4 pb-4 space-y-2 animate-fade-in">
              <div className="h-px bg-[var(--card-border)]" />
              {alternative_voices.map((alt, i) => (
                <div
                  key={i}
                  className="flex items-start gap-3 p-3 rounded-lg bg-[var(--background)]"
                >
                  <div className="w-6 h-6 rounded-md bg-gray-800 flex items-center justify-center text-xs text-gray-500 shrink-0">
                    {i + 1}
                  </div>
                  <div>
                    <span className="text-sm text-gray-300 font-medium">
                      {alt.name}
                    </span>
                    <span className="ml-2 text-xs text-gray-600 font-mono">
                      {alt.voice_id}
                    </span>
                    <p className="text-xs text-gray-500 mt-0.5">{alt.reason}</p>
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
