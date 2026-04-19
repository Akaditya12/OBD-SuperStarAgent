"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { Phone, PhoneOff, RotateCcw } from "lucide-react";
import type { IVRState } from "@/lib/ivr-state-machine";

const KEYS = [
  ["1", "2", "3"],
  ["4", "5", "6"],
  ["7", "8", "9"],
  ["*", "0", "#"],
];

const KEY_LETTERS: Record<string, string> = {
  "2": "ABC", "3": "DEF", "4": "GHI", "5": "JKL",
  "6": "MNO", "7": "PQRS", "8": "TUV", "9": "WXYZ",
  "0": "+", "*": "", "#": "",
};

function formatDuration(ms: number): string {
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
}

interface PhoneUIProps {
  ivrState: IVRState;
  isCallActive: boolean;
  canStart: boolean;
  onKeyPress: (key: string) => void;
  onStartCall: () => void;
  onHangUp: () => void;
  campaignName?: string;
  variantLabel?: string;
  onRestart?: () => void;
  estimatedDurationSec?: number;
}

export default function PhoneUI({
  ivrState, isCallActive, canStart, onKeyPress, onStartCall, onHangUp,
  campaignName, variantLabel, onRestart, estimatedDurationSec,
}: PhoneUIProps) {
  const isWaiting = ivrState.status === "waiting_dtmf";
  const isPlaying = ivrState.status === "playing";
  const isRinging = ivrState.status === "ringing";
  const isEnded = ivrState.status === "ended";

  // DTMF visual pulse
  const [pressedKey, setPressedKey] = useState<string | null>(null);
  const pulseTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleKeyPress = useCallback((key: string) => {
    onKeyPress(key);
    setPressedKey(key);
    if (pulseTimer.current) clearTimeout(pulseTimer.current);
    pulseTimer.current = setTimeout(() => setPressedKey(null), 200);
  }, [onKeyPress]);

  useEffect(() => {
    return () => {
      if (pulseTimer.current) clearTimeout(pulseTimer.current);
    };
  }, []);

  return (
    <div className="flex flex-col items-center">
      {/* Phone bezel */}
      <div className="w-[280px] rounded-[2.5rem] bg-[var(--card)] border-2 border-[var(--card-border)] shadow-2xl overflow-hidden">
        {/* Notch */}
        <div className="flex justify-center pt-3 pb-1">
          <div className="w-20 h-1.5 rounded-full bg-[var(--card-border)]" />
        </div>

        {/* Screen */}
        <div className="mx-4 rounded-2xl bg-[var(--background)] border border-[var(--card-border)] p-4 mb-3 min-h-[140px] flex flex-col items-center justify-center gap-2">
          {/* Campaign name header */}
          {campaignName && (
            <p className="text-[10px] text-[var(--text-tertiary)] font-medium tracking-wide uppercase">
              {campaignName}{variantLabel ? ` \u00B7 ${variantLabel}` : ""}
            </p>
          )}

          {/* Status indicator */}
          {isCallActive && (
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  isPlaying ? "bg-green-500 animate-pulse" :
                  isRinging ? "bg-yellow-500 animate-pulse" :
                  isWaiting ? "bg-blue-500 animate-pulse" :
                  "bg-red-500"
                }`}
              />
              <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)]">
                {isRinging ? "Ringing" :
                 isPlaying ? "Connected" :
                 isWaiting ? "Awaiting Input" :
                 isEnded ? "Disconnected" : ""}
              </span>
            </div>
          )}

          {/* Current state label */}
          <p className="text-sm font-semibold text-[var(--text-primary)] text-center">
            {!isCallActive && !isEnded ? "Ready to call" :
             ivrState.currentLabel || "Idle"}
          </p>

          {/* Duration estimate (before call starts) */}
          {!isCallActive && !isEnded && estimatedDurationSec != null && estimatedDurationSec > 0 && (
            <p className="text-[10px] text-[var(--text-tertiary)]">
              ~{estimatedDurationSec}s estimated
            </p>
          )}

          {/* Waveform animation */}
          {isPlaying && (
            <div className="flex items-center gap-[3px] h-6">
              {Array.from({ length: 12 }).map((_, i) => (
                <div
                  key={i}
                  className="w-[3px] rounded-full bg-[var(--accent)] animate-pulse"
                  style={{
                    animationDelay: `${i * 0.06}s`,
                    height: `${6 + Math.sin(i * 0.8) * 14}px`,
                  }}
                />
              ))}
            </div>
          )}

          {/* Duration */}
          {isCallActive && (
            <span className="text-lg font-mono text-[var(--text-secondary)] tabular-nums">
              {formatDuration(ivrState.callDurationMs)}
            </span>
          )}

          {/* Waiting hint */}
          {isWaiting && (
            <p className="text-[10px] text-[var(--accent)] animate-pulse">
              Press 1, 2, or 3...
            </p>
          )}
        </div>

        {/* Keypad */}
        <div className="px-5 pb-2">
          <div className="grid grid-cols-3 gap-2">
            {KEYS.flat().map((key) => {
              const isPulsed = pressedKey === key;
              return (
                <button
                  key={key}
                  onClick={() => handleKeyPress(key)}
                  disabled={!isCallActive || isEnded}
                  className={`
                    flex flex-col items-center justify-center h-14 rounded-xl
                    text-lg font-semibold transition-all duration-150
                    ${isPulsed
                      ? "bg-[var(--accent)] text-white scale-110"
                      : isCallActive && !isEnded
                        ? "bg-[var(--input-bg)] text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] hover:text-[var(--accent)] active:scale-95"
                        : "bg-[var(--input-bg)] text-[var(--text-tertiary)] opacity-40 cursor-not-allowed"
                    }
                  `}
                >
                  <span>{key}</span>
                  {KEY_LETTERS[key] && (
                    <span className={`text-[8px] tracking-[0.15em] -mt-0.5 ${isPulsed ? "text-white/70" : "text-[var(--text-tertiary)]"}`}>
                      {KEY_LETTERS[key]}
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* Call / Hang Up / Restart buttons */}
        <div className="flex justify-center gap-6 px-5 py-4">
          {!isCallActive || isEnded ? (
            <>
              <button
                onClick={onStartCall}
                disabled={!canStart}
                className={`
                  w-14 h-14 rounded-full flex items-center justify-center transition-all
                  ${canStart
                    ? "bg-green-500 hover:bg-green-600 text-white shadow-lg shadow-green-500/30 active:scale-95"
                    : "bg-green-500/30 text-white/50 cursor-not-allowed"
                  }
                `}
              >
                <Phone className="w-5 h-5" />
              </button>
              {isEnded && onRestart && (
                <button
                  onClick={onRestart}
                  className="w-14 h-14 rounded-full bg-[var(--accent)] hover:bg-[var(--accent)]/80 text-white flex items-center justify-center shadow-lg shadow-[var(--accent)]/30 active:scale-95 transition-all"
                  title="Restart call"
                >
                  <RotateCcw className="w-5 h-5" />
                </button>
              )}
            </>
          ) : (
            <button
              onClick={onHangUp}
              className="w-14 h-14 rounded-full bg-red-500 hover:bg-red-600 text-white flex items-center justify-center shadow-lg shadow-red-500/30 active:scale-95 transition-all"
            >
              <PhoneOff className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Bottom bar */}
        <div className="flex justify-center pb-3">
          <div className="w-28 h-1 rounded-full bg-[var(--card-border)]" />
        </div>
      </div>

    </div>
  );
}
