"use client";

import { useState } from "react";
import {
  FileSearch,
  Globe2,
  PenTool,
  Users,
  Mic2,
  AudioLines,
  CheckCircle2,
  Loader2,
  Circle,
  AlertCircle,
  ChevronDown,
  ChevronRight,
  Eye,
} from "lucide-react";

export interface ProgressStep {
  agent: string;
  label: string;
  status: "pending" | "started" | "completed" | "error";
  message: string;
  data?: Record<string, unknown>;
}

interface PipelineProgressProps {
  steps: ProgressStep[];
}

const AGENT_ICONS: Record<string, React.ReactNode> = {
  ProductAnalyzer: <FileSearch className="w-5 h-5" />,
  MarketResearcher: <Globe2 className="w-5 h-5" />,
  ScriptWriter: <PenTool className="w-5 h-5" />,
  EvalPanel: <Users className="w-5 h-5" />,
  VoiceSelector: <Mic2 className="w-5 h-5" />,
  AudioProducer: <AudioLines className="w-5 h-5" />,
};

function StatusIcon({ status }: { status: ProgressStep["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="w-4 h-4 text-[var(--success)]" />;
    case "started":
      return <Loader2 className="w-4 h-4 text-brand-400 animate-spin" />;
    case "error":
      return <AlertCircle className="w-4 h-4 text-[var(--error)]" />;
    default:
      return <Circle className="w-4 h-4 text-gray-600" />;
  }
}

/** Recursively render a JSON value as a readable tree */
function JsonValue({ value, depth = 0 }: { value: unknown; depth?: number }) {
  if (value === null || value === undefined) {
    return <span className="text-gray-500 italic">null</span>;
  }

  if (typeof value === "string") {
    // Long strings get truncated with expand
    if (value.length > 200) {
      return <ExpandableString text={value} />;
    }
    return <span className="text-emerald-400">&quot;{value}&quot;</span>;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return <span className="text-amber-400">{String(value)}</span>;
  }

  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-gray-500">[]</span>;
    // Simple string arrays render inline
    if (value.every((v) => typeof v === "string") && value.length <= 5) {
      return (
        <div className="flex flex-wrap gap-1">
          {value.map((item, i) => (
            <span
              key={i}
              className="inline-block px-2 py-0.5 rounded text-xs bg-brand-500/10 text-brand-300 border border-brand-500/15"
            >
              {String(item)}
            </span>
          ))}
        </div>
      );
    }
    return (
      <div className="space-y-1 ml-3 border-l border-gray-800 pl-3">
        {value.map((item, i) => (
          <div key={i} className="flex items-start gap-1">
            <span className="text-gray-600 text-xs mt-0.5 flex-shrink-0">
              {i + 1}.
            </span>
            <JsonValue value={item} depth={depth + 1} />
          </div>
        ))}
      </div>
    );
  }

  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>);
    if (entries.length === 0)
      return <span className="text-gray-500">{"{}"}</span>;
    return (
      <div className="space-y-1.5">
        {entries.map(([key, val]) => (
          <div key={key}>
            <span className="text-purple-400 text-xs font-medium">{key}:</span>
            <div className="ml-3 mt-0.5">
              <JsonValue value={val} depth={depth + 1} />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return <span className="text-gray-400">{String(value)}</span>;
}

function ExpandableString({ text }: { text: string }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div>
      <span className="text-emerald-400 text-xs">
        &quot;{expanded ? text : text.slice(0, 150) + "..."}&quot;
      </span>
      <button
        onClick={() => setExpanded(!expanded)}
        className="ml-1 text-xs text-brand-400 hover:text-brand-300"
      >
        {expanded ? "less" : "more"}
      </button>
    </div>
  );
}

function AgentOutputPanel({ step }: { step: ProgressStep }) {
  const [expanded, setExpanded] = useState(false);
  const data = step.data;

  if (!data || Object.keys(data).length === 0) return null;

  return (
    <div className="mt-2 animate-fade-in">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1.5 text-xs text-brand-400 hover:text-brand-300 transition-colors"
      >
        <Eye className="w-3 h-3" />
        <span>View Output</span>
        {expanded ? (
          <ChevronDown className="w-3 h-3" />
        ) : (
          <ChevronRight className="w-3 h-3" />
        )}
      </button>

      {expanded && (
        <div className="mt-2 p-3 rounded-lg bg-[var(--background)] border border-[var(--card-border)] max-h-[400px] overflow-y-auto text-xs animate-slide-up">
          <JsonValue value={data} />
        </div>
      )}
    </div>
  );
}

export default function PipelineProgress({ steps }: PipelineProgressProps) {
  return (
    <div className="space-y-1">
      <h3 className="text-sm font-medium text-gray-400 mb-4 uppercase tracking-wider">
        Pipeline Progress
      </h3>
      <div className="space-y-0">
        {steps.map((step, i) => (
          <div key={step.agent + i} className="relative">
            {/* Connector line */}
            {i < steps.length - 1 && (
              <div
                className={`absolute left-[19px] w-0.5 h-4 ${
                  step.status === "completed"
                    ? "bg-[var(--success)]/30"
                    : "bg-gray-800"
                }`}
                style={{ top: step.data && Object.keys(step.data).length > 0 ? "calc(100% - 8px)" : "40px" }}
              />
            )}

            <div
              className={`p-3 rounded-xl transition-all duration-300 ${
                step.status === "started"
                  ? "bg-brand-500/5 border border-brand-500/20 glow-accent"
                  : step.status === "completed"
                  ? "bg-[var(--success)]/5"
                  : step.status === "error"
                  ? "bg-[var(--error)]/5"
                  : ""
              }`}
            >
              <div className="flex items-start gap-3">
                {/* Icon */}
                <div
                  className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center ${
                    step.status === "started"
                      ? "bg-brand-500/15 text-brand-400"
                      : step.status === "completed"
                      ? "bg-[var(--success)]/15 text-[var(--success)]"
                      : step.status === "error"
                      ? "bg-[var(--error)]/15 text-[var(--error)]"
                      : "bg-gray-800/50 text-gray-600"
                  }`}
                >
                  {AGENT_ICONS[step.agent] || <Circle className="w-5 h-5" />}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-sm font-medium ${
                        step.status === "started"
                          ? "text-brand-300"
                          : step.status === "completed"
                          ? "text-[var(--success)]"
                          : step.status === "error"
                          ? "text-[var(--error)]"
                          : "text-gray-500"
                      }`}
                    >
                      {step.label}
                    </span>
                    <StatusIcon status={step.status} />
                  </div>
                  {step.message && (
                    <p className="text-xs text-[var(--muted)] mt-0.5">
                      {step.message}
                    </p>
                  )}

                  {/* Agent output panel */}
                  {step.status === "completed" && <AgentOutputPanel step={step} />}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
