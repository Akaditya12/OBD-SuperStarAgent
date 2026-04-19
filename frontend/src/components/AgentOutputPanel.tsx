"use client";

import { useState, useEffect } from "react";
import {
  Package,
  Globe,
  PenTool,
  Trophy,
  Mic2,
  Volume2,
  ChevronDown,
  ChevronUp,
  Bot,
  Clock,
  Database,
} from "lucide-react";
import type { ProgressStep } from "./PipelineProgress";

interface AgentOutputPanelProps {
  steps: ProgressStep[];
}

// ── Safe text helper — prevents rendering objects as React children ──
function safeText(val: unknown, maxLen?: number): string {
  if (val == null) return "";
  if (typeof val === "string") return maxLen ? val.slice(0, maxLen) : val;
  if (typeof val === "number" || typeof val === "boolean") return String(val);
  try { const s = JSON.stringify(val); return maxLen ? s.slice(0, maxLen) : s; }
  catch { return ""; }
}

// ── Per-agent compact renderers ──

function ProductAnalysisCard({ data }: { data: Record<string, unknown> }) {
  const brief = ((data.data || data) as Record<string, unknown>) || {};
  const name = safeText(brief.product_name || brief.name);
  const features = Array.isArray(brief.key_features) ? brief.key_features : Array.isArray(brief.features) ? brief.features : [];
  const target = safeText(brief.target_audience || brief.audience, 80);
  const cta = safeText(brief.cta || brief.shortcode || brief.activation);
  const pricing = safeText(brief.pricing);

  return (
    <div className="space-y-2">
      {name && <p className="text-sm font-semibold text-[var(--text-primary)]">{name}</p>}
      {features.length > 0 && (
        <div>
          <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-medium">Key Features</span>
          <ul className="mt-1 space-y-0.5">
            {features.slice(0, 4).map((f: unknown, i: number) => (
              <li key={i} className="text-xs text-[var(--text-secondary)] flex items-start gap-1.5">
                <span className="text-[var(--accent)] mt-0.5">•</span>
                {safeText(f)}
              </li>
            ))}
            {features.length > 4 && (
              <li className="text-[10px] text-[var(--text-tertiary)]">+{features.length - 4} more</li>
            )}
          </ul>
        </div>
      )}
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px] text-[var(--text-tertiary)]">
        {target && <span>Target: {target}</span>}
        {cta && <span>CTA: {cta}</span>}
        {pricing && <span>Price: {pricing}</span>}
      </div>
    </div>
  );
}

function MarketInsightsCard({ data }: { data: Record<string, unknown> }) {
  const d = ((data.data || data) as Record<string, unknown>);
  const tone = safeText(d.communication_style || d.tone || d.cultural_tone, 80);
  const taboos = Array.isArray(d.taboos) ? d.taboos : Array.isArray(d.avoid) ? d.avoid : [];
  const callTimes = safeText(d.best_call_times || d.call_times, 60);
  const competitive = safeText(d.competitive_landscape || d.competitors, 80);
  const audience = safeText(d.target_audience_psyche || d.target_psyche || d.audience, 80);

  return (
    <div className="space-y-2">
      {tone && (
        <p className="text-xs text-[var(--text-secondary)]">
          <span className="font-medium text-[var(--text-primary)]">Tone:</span> {tone}
        </p>
      )}
      {callTimes && (
        <p className="text-xs text-[var(--text-secondary)]">
          <span className="font-medium text-[var(--text-primary)]">Best time:</span> {callTimes}
        </p>
      )}
      {taboos.length > 0 && (
        <div className="flex items-start gap-1.5">
          <span className="text-[10px] text-amber-500 font-medium shrink-0">Avoid:</span>
          <span className="text-[10px] text-[var(--text-tertiary)]">
            {taboos.slice(0, 3).map((t: unknown) => safeText(t)).join(" · ")}
          </span>
        </div>
      )}
      {audience && <p className="text-[10px] text-[var(--text-tertiary)]">Audience: {audience}</p>}
      {competitive && <p className="text-[10px] text-[var(--text-tertiary)]">Competitors: {competitive}</p>}
    </div>
  );
}

function ScriptsCard({ data }: { data: Record<string, unknown> }) {
  // Scripts may be at data.scripts or data.data.scripts (nested from backend progress)
  const nested = (data.data || data) as Record<string, unknown>;
  const scripts = (nested.scripts || data.scripts || []) as Array<Record<string, unknown>>;
  const lang = ((nested.language_used || data.language_used || "") as string);

  return (
    <div className="space-y-2">
      {scripts.length > 0 ? (
        <div className="space-y-1.5">
          {scripts.map((s, i) => {
            const theme = (s.theme || "") as string;
            const hook = (s.hook_line || s.full_script || "") as string;
            const words = typeof hook === "string" ? hook.split(/\s+/).filter(Boolean).length : 0;
            const duration = (s.estimated_duration_seconds || Math.round(words / 2.5)) as number;
            return (
              <div key={i} className="flex items-baseline gap-2">
                <span className="text-[10px] font-mono text-[var(--accent)] shrink-0">V{i + 1}</span>
                <span className="text-xs font-medium text-[var(--text-primary)] shrink-0">{theme}</span>
                <span className="text-[10px] text-[var(--text-tertiary)]">{words}w · ~{duration}s</span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-[var(--text-secondary)]">Scripts generated</p>
      )}
      {lang && <p className="text-[10px] text-[var(--text-tertiary)]">Language: {lang}</p>}
    </div>
  );
}

function EvalCard({ data }: { data: Record<string, unknown> }) {
  const d = ((data.data || data) as Record<string, unknown>);
  const ranking = Array.isArray(d.consensus_ranking) ? d.consensus_ranking : Array.isArray(d.ranking) ? d.ranking : [];
  const assessment = safeText(d.overall_assessment || d.assessment, 120);
  const improvements = Array.isArray(d.critical_improvements) ? d.critical_improvements : Array.isArray(d.improvements) ? d.improvements : [];

  return (
    <div className="space-y-2">
      {ranking.length > 0 && (
        <div className="space-y-1">
          {ranking.slice(0, 5).map((r: unknown, i: number) => {
            const entry = (typeof r === "object" && r !== null ? r : {}) as Record<string, unknown>;
            const medal = i === 0 ? "\u{1F947}" : i === 1 ? "\u{1F948}" : i === 2 ? "\u{1F949}" : `${i + 1}`;
            const theme = safeText(entry.theme || entry.variant_theme);
            const score = entry.average_score || entry.score;
            return (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="w-5 text-center">{medal}</span>
                <span className="text-[var(--text-primary)] font-medium flex-1">{theme || `V${i + 1}`}</span>
                <span className="font-mono text-[var(--accent)]">{typeof score === "number" ? score.toFixed(1) : safeText(score)}/10</span>
              </div>
            );
          })}
        </div>
      )}
      {improvements.length > 0 && (
        <div className="text-[10px] text-[var(--text-tertiary)]">
          Top feedback: {improvements.slice(0, 2).map((im: unknown) => safeText(im)).join(" \u00B7 ")}
        </div>
      )}
      {!ranking.length && assessment && (
        <p className="text-xs text-[var(--text-secondary)]">{assessment}</p>
      )}
    </div>
  );
}

function VoiceCard({ data }: { data: Record<string, unknown> }) {
  const d = ((data.data || data) as Record<string, unknown>);
  const voice = (d.selected_voice || {}) as Record<string, unknown>;
  const name = (voice.name || "") as string;
  const rationale = (d.rationale || "") as string;

  return (
    <div className="space-y-1">
      {name && <p className="text-sm font-semibold text-[var(--text-primary)]">{name}</p>}
      {rationale && typeof rationale === "string" && (
        <p className="text-xs text-[var(--text-secondary)]">{rationale.slice(0, 120)}</p>
      )}
    </div>
  );
}

function AudioCard({ data }: { data: Record<string, unknown> }) {
  const summary = (data.summary || {}) as Record<string, unknown>;
  const engine = (data.tts_engine_label || data.tts_engine || "") as string;
  const count = (summary.total_generated || 0) as number;

  return (
    <div className="space-y-1">
      <p className="text-xs text-[var(--text-secondary)]">
        <span className="font-medium text-[var(--text-primary)]">{count}</span> hook previews generated
        {engine ? ` via ${engine}` : ""}
      </p>
      <p className="text-[10px] text-[var(--text-tertiary)]">Select voices below to generate final audio</p>
    </div>
  );
}

// ── Agent metadata ──

const AGENT_META: Record<string, {
  icon: typeof Package;
  label: string;
  color: string;
  inputDesc: string;
  renderer: ((props: { data: Record<string, unknown> }) => React.ReactNode) | null;
}> = {
  ProductAnalyzer: {
    icon: Package,
    label: "Product Analysis",
    color: "text-blue-400",
    inputDesc: "Raw product documentation",
    renderer: ProductAnalysisCard,
  },
  MarketResearcher: {
    icon: Globe,
    label: "Market Insights",
    color: "text-emerald-400",
    inputDesc: "Product brief + country/telco context",
    renderer: MarketInsightsCard,
  },
  ScriptWriter: {
    icon: PenTool,
    label: "Script Generation",
    color: "text-purple-400",
    inputDesc: "Product brief + market insights + cultural guidelines",
    renderer: ScriptsCard,
  },
  ScriptWriter_Revision: {
    icon: PenTool,
    label: "Script Revision",
    color: "text-purple-400",
    inputDesc: "Scripts + evaluation feedback",
    renderer: ScriptsCard,
  },
  EvalPanel: {
    icon: Trophy,
    label: "Evaluation Panel",
    color: "text-amber-400",
    inputDesc: "Script variants + market context",
    renderer: EvalCard,
  },
  VoiceSelector: {
    icon: Mic2,
    label: "Voice Selection",
    color: "text-pink-400",
    inputDesc: "Scripts + market analysis + voice catalog",
    renderer: VoiceCard,
  },
  AudioProducer: {
    icon: Volume2,
    label: "Audio Production",
    color: "text-cyan-400",
    inputDesc: "Final scripts + voice selection + TTS engine",
    renderer: AudioCard,
  },
};

// ── Expanded detail view ──

function DetailedView({ data, agent }: { data: Record<string, unknown>; agent: string }) {
  const meta = AGENT_META[agent];
  const systemPrompt = data.system_prompt as string | undefined;
  const userPrompt = data.user_prompt as string | undefined;

  // Filter out prompts and message from display data
  const displayData = Object.fromEntries(
    Object.entries(data).filter(([k]) => !["system_prompt", "user_prompt", "message"].includes(k))
  );

  return (
    <div className="space-y-3 pt-2 border-t border-[var(--card-border)]">
      {/* Source info */}
      <div className="grid grid-cols-1 gap-1.5 text-[10px]">
        <div className="flex items-center gap-1.5 text-[var(--text-tertiary)]">
          <Bot className="w-3 h-3" />
          <span>Azure OpenAI · GPT-5.1-chat</span>
        </div>
        {meta && (
          <div className="flex items-center gap-1.5 text-[var(--text-tertiary)]">
            <Database className="w-3 h-3" />
            <span>Input: {meta.inputDesc}</span>
          </div>
        )}
        {typeof data.message === "string" && data.message.includes("cached") && (
          <div className="flex items-center gap-1.5 text-emerald-400">
            <Clock className="w-3 h-3" />
            <span>Cached — reused from previous analysis</span>
          </div>
        )}
      </div>

      {/* System prompt preview */}
      {systemPrompt && (
        <details className="group">
          <summary className="text-[10px] text-[var(--text-tertiary)] cursor-pointer hover:text-[var(--accent)] transition-colors">
            View agent system prompt
          </summary>
          <pre className="mt-1.5 p-2 rounded-lg bg-[var(--input-bg)] text-[9px] text-[var(--text-tertiary)] overflow-auto max-h-40 whitespace-pre-wrap font-mono">
            {systemPrompt.slice(0, 1500)}{systemPrompt.length > 1500 ? "..." : ""}
          </pre>
        </details>
      )}

      {/* Raw data preview */}
      <details className="group">
        <summary className="text-[10px] text-[var(--text-tertiary)] cursor-pointer hover:text-[var(--accent)] transition-colors">
          View raw output data
        </summary>
        <pre className="mt-1.5 p-2 rounded-lg bg-[var(--input-bg)] text-[9px] text-[var(--text-tertiary)] overflow-auto max-h-60 whitespace-pre-wrap font-mono">
          {JSON.stringify(displayData, null, 2).slice(0, 3000)}
        </pre>
      </details>
    </div>
  );
}

// ── Main component ──

export default function AgentOutputPanel({ steps }: AgentOutputPanelProps) {
  const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
  const [activeAgent, setActiveAgent] = useState<string | null>(null);

  // Auto-select latest completed step with data
  const completedWithData = steps.filter((s) => s.status === "completed" && s.data);
  const latestCompleted = completedWithData[completedWithData.length - 1];

  useEffect(() => {
    if (latestCompleted) {
      setActiveAgent(latestCompleted.agent);
    }
  }, [latestCompleted?.agent]);

  const stepsWithData = steps.filter((s) => s.data && (s.status === "completed" || s.status === "error"));

  if (stepsWithData.length === 0) {
    return (
      <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 flex flex-col items-center justify-center min-h-[200px] text-center">
        <Bot className="w-8 h-8 text-[var(--text-tertiary)] mb-3 animate-pulse" />
        <p className="text-sm font-medium text-[var(--text-secondary)]">Agents are working...</p>
        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Outputs will appear here as each step completes</p>
      </div>
    );
  }

  return (
    <div className="space-y-2 sticky top-6">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-[var(--text-tertiary)] flex items-center gap-1.5 mb-3">
        <Bot className="w-3.5 h-3.5 text-[var(--accent)]" />
        Agent Outputs
      </h3>

      {stepsWithData.map((step) => {
        const meta = AGENT_META[step.agent] || {
          icon: Bot,
          label: step.label || step.agent,
          color: "text-[var(--accent)]",
          inputDesc: "",
          renderer: null,
        };
        const Icon = meta.icon;
        const isActive = activeAgent === step.agent;
        const isExpanded = expandedAgent === step.agent;
        const Renderer = meta.renderer;

        return (
          <div
            key={step.agent}
            className={`rounded-2xl border transition-all ${
              isActive
                ? "border-[var(--accent)]/30 bg-[var(--card)] shadow-sm"
                : "border-[var(--card-border)] bg-[var(--card)] opacity-80"
            }`}
          >
            {/* Compact header — always visible */}
            <button
              onClick={() => setActiveAgent(isActive ? null : step.agent)}
              className="w-full p-3 flex items-start gap-2.5 text-left"
            >
              <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${meta.color}`} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-[var(--text-primary)]">{meta.label}</span>
                  {step.message?.includes("cached") && (
                    <span className="text-[8px] px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-400 font-medium">cached</span>
                  )}
                </div>

                {/* Compact summary — renderer output */}
                {isActive && Renderer && step.data && (
                  <div className="mt-2 animate-fade-in">
                    <Renderer data={step.data} />
                  </div>
                )}
              </div>
            </button>

            {/* Show details toggle */}
            {isActive && step.data && (
              <div className="px-3 pb-3">
                <button
                  onClick={() => setExpandedAgent(isExpanded ? null : step.agent)}
                  className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)] hover:text-[var(--accent)] transition-colors"
                >
                  {isExpanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                  {isExpanded ? "Hide details" : "Show details"}
                </button>

                {isExpanded && (
                  <div className="mt-2 animate-fade-in">
                    <DetailedView data={step.data} agent={step.agent} />
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
