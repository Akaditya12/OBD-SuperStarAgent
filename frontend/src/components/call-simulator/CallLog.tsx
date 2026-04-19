"use client";

import { useEffect, useRef } from "react";
import { Play, Hash, Clock, AlertCircle, PhoneCall, PhoneOff, Info } from "lucide-react";
import type { CallLogEntry } from "@/lib/ivr-state-machine";

const ICONS: Record<CallLogEntry["type"], typeof Play> = {
  call_start: PhoneCall,
  call_end: PhoneOff,
  audio_start: Play,
  audio_end: Play,
  dtmf: Hash,
  timeout: Clock,
  error: AlertCircle,
  info: Info,
};

const COLORS: Record<CallLogEntry["type"], string> = {
  call_start: "text-green-400",
  call_end: "text-red-400",
  audio_start: "text-[var(--accent)]",
  audio_end: "text-[var(--accent)]",
  dtmf: "text-emerald-400",
  timeout: "text-yellow-400",
  error: "text-red-400",
  info: "text-[var(--text-tertiary)]",
};

function formatElapsed(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

interface CallLogProps {
  entries: CallLogEntry[];
  onClear: () => void;
}

export default function CallLog({ entries, onClear }: CallLogProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [entries.length]);

  return (
    <div className="flex flex-col h-full rounded-2xl bg-[var(--card)] border border-[var(--card-border)] overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-[var(--card-border)]">
        <h3 className="text-sm font-semibold text-[var(--text-primary)]">Call Log</h3>
        {entries.length > 0 && (
          <button
            onClick={onClear}
            className="text-[10px] text-[var(--text-tertiary)] hover:text-[var(--accent)] transition-colors"
          >
            Clear
          </button>
        )}
      </div>

      {/* Log entries */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-3 space-y-1.5 min-h-[300px] max-h-[500px]">
        {entries.length === 0 ? (
          <p className="text-xs text-[var(--text-tertiary)] text-center py-8">
            Start a call to see events here
          </p>
        ) : (
          entries.map((entry, i) => {
            const Icon = ICONS[entry.type] || Info;
            const color = COLORS[entry.type] || "text-[var(--text-tertiary)]";
            return (
              <div key={i} className="flex items-start gap-2 group">
                <span className="text-[10px] font-mono text-[var(--text-tertiary)] mt-0.5 shrink-0 tabular-nums">
                  {formatElapsed(entry.elapsed)}
                </span>
                <Icon className={`w-3 h-3 mt-0.5 shrink-0 ${color}`} />
                <span className="text-xs text-[var(--text-secondary)] leading-relaxed">
                  {entry.message}
                  {entry.key && (
                    <span className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded bg-emerald-500/20 text-emerald-400 text-[10px] font-bold">
                      {entry.key}
                    </span>
                  )}
                </span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
