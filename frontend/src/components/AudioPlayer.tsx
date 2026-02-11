"use client";

import { useState, useRef } from "react";
import {
  Play,
  Pause,
  Download,
  Mic2,
  FileAudio,
} from "lucide-react";
import type { AudioFile, VoiceSettings } from "@/lib/types";

interface AudioPlayerProps {
  sessionId: string;
  audioFiles: AudioFile[];
  voiceInfo?: {
    name: string;
    voice_id: string;
    settings: VoiceSettings;
  };
}

function SingleAudioPlayer({
  file,
  sessionId,
}: {
  file: AudioFile;
  sessionId: string;
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const audioRef = useRef<HTMLAudioElement>(null);

  const audioUrl = `/outputs/${sessionId}/${file.file_name}`;

  const togglePlay = () => {
    if (!audioRef.current) return;
    if (isPlaying) {
      audioRef.current.pause();
    } else {
      audioRef.current.play();
    }
    setIsPlaying(!isPlaying);
  };

  const handleEnded = () => setIsPlaying(false);

  const typeLabels: Record<string, string> = {
    main: "Main Script",
    fallback_1: "Fallback 1",
    fallback_2: "Fallback 2",
    polite_closure: "Closure",
  };

  const typeColors: Record<string, string> = {
    main: "text-brand-400 bg-brand-500/10",
    fallback_1: "text-[var(--warning)] bg-[var(--warning)]/10",
    fallback_2: "text-orange-400 bg-orange-500/10",
    polite_closure: "text-gray-400 bg-gray-500/10",
  };

  if (file.error) {
    return (
      <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--error)]/5 border border-[var(--error)]/20">
        <FileAudio className="w-4 h-4 text-[var(--error)]" />
        <span className="text-sm text-[var(--error)]">
          Variant {file.variant_id} - {typeLabels[file.type] || file.type}:
          Failed
        </span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-3 p-3 rounded-lg bg-[var(--card)] border border-[var(--card-border)] hover:border-brand-500/30 transition-all">
      <audio ref={audioRef} src={audioUrl} onEnded={handleEnded} preload="none" />

      {/* Play button */}
      <button
        onClick={togglePlay}
        className="flex-shrink-0 w-9 h-9 rounded-lg bg-brand-500/15 text-brand-400 flex items-center justify-center hover:bg-brand-500/25 transition-colors"
      >
        {isPlaying ? (
          <Pause className="w-4 h-4" />
        ) : (
          <Play className="w-4 h-4 ml-0.5" />
        )}
      </button>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-300">
            Variant {file.variant_id}
          </span>
          <span
            className={`px-2 py-0.5 rounded text-xs ${
              typeColors[file.type] || "text-gray-400 bg-gray-500/10"
            }`}
          >
            {typeLabels[file.type] || file.type}
          </span>
        </div>
        {file.theme && (
          <p className="text-xs text-[var(--muted)] truncate mt-0.5">
            {file.theme}
          </p>
        )}
      </div>

      {/* Download */}
      <a
        href={audioUrl}
        download={file.file_name}
        className="flex-shrink-0 p-2 rounded-lg hover:bg-white/5 transition-colors"
      >
        <Download className="w-4 h-4 text-gray-500 hover:text-gray-300" />
      </a>
    </div>
  );
}

export default function AudioPlayer({
  sessionId,
  audioFiles,
  voiceInfo,
}: AudioPlayerProps) {
  if (!audioFiles || audioFiles.length === 0) {
    return (
      <div className="text-center py-8 text-[var(--muted)]">
        No audio files generated yet.
      </div>
    );
  }

  // Group by variant
  const grouped: Record<number, AudioFile[]> = {};
  for (const file of audioFiles) {
    if (!grouped[file.variant_id]) grouped[file.variant_id] = [];
    grouped[file.variant_id].push(file);
  }

  return (
    <div className="space-y-4">
      {/* Voice info */}
      {voiceInfo && (
        <div className="flex items-center gap-3 p-3 rounded-xl bg-purple-500/5 border border-purple-500/20">
          <Mic2 className="w-5 h-5 text-purple-400" />
          <div>
            <span className="text-sm text-purple-300 font-medium">
              Voice: {voiceInfo.name}
            </span>
            <div className="flex items-center gap-3 mt-0.5">
              {Object.entries(voiceInfo.settings).map(([key, val]) => (
                <span key={key} className="text-xs text-[var(--muted)]">
                  {key}: {typeof val === "number" ? val.toFixed(2) : val}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      <h3 className="text-sm font-medium text-gray-400 uppercase tracking-wider">
        Audio Recordings ({audioFiles.filter((f) => !f.error).length} files)
      </h3>

      {Object.entries(grouped)
        .sort(([a], [b]) => Number(a) - Number(b))
        .map(([variantId, files]) => (
          <div key={variantId} className="space-y-1.5">
            <h4 className="text-xs font-medium text-gray-500 pl-1">
              Variant {variantId}
            </h4>
            {files.map((file) => (
              <SingleAudioPlayer
                key={file.file_name || `${file.variant_id}-${file.type}`}
                file={file}
                sessionId={sessionId}
              />
            ))}
          </div>
        ))}

      {/* Download all */}
      <div className="pt-2">
        <p className="text-xs text-[var(--muted)] text-center">
          Audio files are saved in the backend at{" "}
          <code className="text-gray-500">backend/outputs/{sessionId}/</code>
        </p>
      </div>
    </div>
  );
}
