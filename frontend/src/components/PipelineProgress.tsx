"use client";

import { useState } from "react";
import {
  CheckCircle2,
  Loader2,
  Circle,
  AlertCircle,
  ChevronDown,
  ChevronUp,
  SkipForward,
} from "lucide-react";

export interface ProgressStep {
  agent: string;
  label: string;
  status: "pending" | "started" | "completed" | "error" | "skipped";
  message: string;
  data?: Record<string, unknown>;
}

interface PipelineProgressProps {
  steps: ProgressStep[];
  onSkipStep?: (agent: string) => void;
  skippableAgents?: string[];
}

export default function PipelineProgress({ steps, onSkipStep, skippableAgents = [] }: PipelineProgressProps) {
  const [expandedStep, setExpandedStep] = useState<number | null>(null);

  const doneCount = steps.filter((s) => s.status === "completed" || s.status === "skipped").length;
  const totalCount = steps.length;
  const percent = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;
  const isRunning = steps.some((s) => s.status === "started");

  return (
    <div className="space-y-4">
      {/* Overall progress bar */}
      <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-[var(--text-secondary)]">
            Pipeline Progress
          </span>
          <span className="text-xs text-[var(--text-tertiary)] tabular-nums">
            {doneCount}/{totalCount} steps · {percent}%
          </span>
        </div>
        <div className="h-1.5 rounded-full bg-[var(--card-border)] overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${percent}%`,
              background: `linear-gradient(90deg, var(--accent), var(--success))`,
            }}
          />
        </div>
      </div>

      {/* Steps timeline */}
      <div className="relative">
        {steps.map((step, idx) => {
          const isLast = idx === steps.length - 1;
          const isExpanded = expandedStep === idx;

          const isSkipped = step.status === "skipped";
          const canSkip = isRunning && step.status === "pending" && skippableAgents.includes(step.agent) && !!onSkipStep;

          const dotStyle = step.status === "completed"
            ? "border-[var(--success)]/30 bg-[var(--success)]/10"
            : step.status === "started"
              ? "border-[var(--accent)]/30 bg-[var(--accent)]/10 animate-pulse"
              : step.status === "error"
                ? "border-[var(--error)]/30 bg-[var(--error)]/10"
                : isSkipped
                  ? "border-gray-400/30 bg-gray-400/10 border-dashed"
                  : "border-[var(--card-border)] bg-[var(--card)]";

          const lineColor = step.status === "completed"
            ? "bg-[var(--success)]/30"
            : step.status === "started"
              ? "bg-[var(--accent)]/30"
              : step.status === "error"
                ? "bg-[var(--error)]/30"
                : isSkipped
                  ? "bg-gray-400/30"
                  : "bg-[var(--card-border)]";

          const textColor = step.status === "completed"
            ? "text-[var(--success)]"
            : step.status === "started"
              ? "text-[var(--accent)]"
              : step.status === "error"
                ? "text-[var(--error)]"
                : isSkipped
                  ? "text-gray-400"
                  : "text-[var(--text-tertiary)]";

          const icon = step.status === "completed"
            ? <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />
            : step.status === "started"
              ? <Loader2 className="w-4 h-4 text-[var(--accent)] animate-spin" />
              : step.status === "error"
                ? <AlertCircle className="w-4 h-4 text-[var(--error)]" />
                : isSkipped
                  ? <SkipForward className="w-4 h-4 text-gray-400" />
                  : <Circle className="w-4 h-4 text-[var(--text-tertiary)]" />;

          return (
            <div key={`${step.agent}-${idx}`} className="relative flex gap-4">
              {/* Timeline line + dot */}
              <div className="flex flex-col items-center flex-shrink-0">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all ${dotStyle}`}
                >
                  {icon}
                </div>
                {!isLast && (
                  <div
                    className={`w-0.5 flex-1 min-h-[24px] transition-colors ${lineColor}`}
                  />
                )}
              </div>

              {/* Content */}
              <div className={`flex-1 pb-5 ${isLast ? "pb-0" : ""}`}>
                <div
                  role="button"
                  tabIndex={0}
                  onClick={() =>
                    setExpandedStep(isExpanded ? null : idx)
                  }
                  onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setExpandedStep(isExpanded ? null : idx); } }}
                  className="w-full text-left flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-2 flex-wrap">
                    <span
                      className={`text-sm font-medium ${
                        step.status === "pending"
                          ? "text-[var(--text-tertiary)]"
                          : isSkipped
                            ? "text-gray-400"
                            : "text-[var(--text-primary)]"
                      }`}
                    >
                      {step.label}
                    </span>
                    {isSkipped && (
                      <span className="px-1.5 py-0.5 text-[9px] font-medium uppercase tracking-wider rounded bg-gray-400/10 text-gray-400 border border-gray-400/20 border-dashed">
                        Skipped
                      </span>
                    )}
                    {canSkip && (
                      <button
                        type="button"
                        onClick={(e) => { e.stopPropagation(); onSkipStep!(step.agent); }}
                        className="px-2 py-0.5 text-[10px] font-medium rounded-full bg-amber-500/10 text-amber-400 border border-amber-500/20 hover:bg-amber-500/20 transition-colors flex items-center gap-1"
                      >
                        <SkipForward className="w-3 h-3" />
                        Skip
                      </button>
                    )}
                  </div>
                  <div className="flex items-center gap-1.5">
                    {step.message && step.status !== "pending" && !isSkipped && (
                      <p className={`text-[11px] ${textColor} text-right hidden sm:block`}>
                        {step.message}
                      </p>
                    )}
                    {step.data && Object.keys(step.data).length > 0 && (
                      <span className="p-1 text-[var(--text-tertiary)]">
                        {isExpanded ? (
                          <ChevronUp className="w-3.5 h-3.5" />
                        ) : (
                          <ChevronDown className="w-3.5 h-3.5" />
                        )}
                      </span>
                    )}
                  </div>
                </div>
                {step.message && step.status !== "pending" && !isSkipped && (
                  <p className={`text-[11px] mt-0.5 ${textColor} sm:hidden`}>
                    {step.message}
                  </p>
                )}

                {/* Expanded data */}
                {isExpanded && step.data && (
                  <div className="mt-2 p-3 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] animate-fade-in">
                    <pre className="text-[10px] text-[var(--text-tertiary)] overflow-x-auto max-h-40 overflow-y-auto">
                      {JSON.stringify(step.data, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
