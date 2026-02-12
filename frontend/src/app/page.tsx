"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import {
  Zap,
  ArrowRight,
  ArrowLeft,
  Rocket,
  Sparkles,
  Settings2,
  Mic2,
} from "lucide-react";
import ProductUpload from "@/components/ProductUpload";
import CountryTelcoSelect from "@/components/CountryTelcoSelect";
import PipelineProgress, {
  type ProgressStep,
} from "@/components/PipelineProgress";
import ScriptReview from "@/components/ScriptReview";
import AudioPlayer from "@/components/AudioPlayer";
import VoiceInfoPanel from "@/components/VoiceInfoPanel";
import type { PipelineResult, VoiceSelection, WsProgressMessage } from "@/lib/types";

// Pipeline step definitions
const PIPELINE_STEPS: Omit<ProgressStep, "status" | "message">[] = [
  { agent: "ProductAnalyzer", label: "Product Analysis" },
  { agent: "MarketResearcher", label: "Market Research" },
  { agent: "ScriptWriter", label: "Script Generation" },
  { agent: "EvalPanel", label: "Evaluation Panel" },
  { agent: "ScriptWriter", label: "Script Revision" },
  { agent: "VoiceSelector", label: "Voice Selection" },
  { agent: "AudioProducer", label: "Audio Production" },
];

type WizardStep = "input" | "running" | "results";

export default function Home() {
  // Form state
  const [productText, setProductText] = useState("");
  const [fileName, setFileName] = useState("");
  const [country, setCountry] = useState("");
  const [telco, setTelco] = useState("");
  const [language, setLanguage] = useState("");
  const [provider, setProvider] = useState("azure_openai");

  // Pipeline state
  const [wizardStep, setWizardStep] = useState<WizardStep>("input");
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>(
    PIPELINE_STEPS.map((s) => ({ ...s, status: "pending", message: "" }))
  );
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  const canStart = productText.trim() && country && telco;

  // Track which step index we're on for progress updates
  const stepIndexRef = useRef(0);

  const updateStep = useCallback(
    (
      agent: string,
      status: ProgressStep["status"],
      message: string,
      wsData?: Record<string, unknown>
    ) => {
      setProgressSteps((prev) => {
        const updated = [...prev];
        // Find the next matching agent step that hasn't been completed
        let targetIdx = -1;
        for (let i = 0; i < updated.length; i++) {
          if (
            updated[i].agent === agent &&
            updated[i].status !== "completed"
          ) {
            targetIdx = i;
            break;
          }
        }
        if (targetIdx >= 0) {
          // Extract prompts and data from the WS payload
          const systemPrompt = wsData?.system_prompt as string | undefined;
          const userPrompt = wsData?.user_prompt as string | undefined;
          // data = everything except the prompt fields
          const agentData = wsData
            ? Object.fromEntries(
                Object.entries(wsData).filter(
                  ([k]) => k !== "system_prompt" && k !== "user_prompt"
                )
              )
            : undefined;

          updated[targetIdx] = {
            ...updated[targetIdx],
            status,
            message,
            ...(status === "completed" && agentData && Object.keys(agentData).length > 0
              ? { data: agentData }
              : {}),
            ...(status === "completed" && systemPrompt
              ? { systemPrompt }
              : {}),
            ...(status === "completed" && userPrompt ? { userPrompt } : {}),
          };
        }
        return updated;
      });
    },
    []
  );

  const startPipeline = useCallback(() => {
    setWizardStep("running");
    setError(null);
    setResult(null);
    stepIndexRef.current = 0;
    setProgressSteps(
      PIPELINE_STEPS.map((s) => ({ ...s, status: "pending", message: "" }))
    );

    // Determine WebSocket URL
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.hostname}:8000/ws/generate`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(
        JSON.stringify({
          product_text: productText,
          country,
          telco,
          language: language || undefined,
          provider: provider || undefined,
        })
      );
    };

    ws.onmessage = (event) => {
      try {
        const data: WsProgressMessage = JSON.parse(event.data);
        const { agent, status, message } = data;

        if (agent === "Pipeline" && status === "done") {
          // Pipeline completed successfully -- show results
          const pipelineResult = (data.result || {}) as PipelineResult;
          setResult(pipelineResult);
          setWizardStep("results");
          return;
        }

        if (agent === "Pipeline" && status === "error") {
          // Pipeline failed -- show error with any partial results
          setError(message || "Pipeline failed");
          if (data.result) {
            setResult(data.result as PipelineResult);
          }
          setWizardStep("results");
          return;
        }

        // Agent progress updates
        if (agent && status) {
          updateStep(
            agent,
            status as ProgressStep["status"],
            message || "",
            data.data as Record<string, unknown> | undefined
          );
        }
      } catch {
        // Ignore parse errors
      }
    };

    ws.onerror = () => {
      setError(
        "WebSocket connection failed. Make sure the backend is running on port 8000."
      );
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  }, [productText, country, telco, language, provider, updateStep]);

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      wsRef.current?.close();
    };
  }, []);

  // Extract data from results (typed via PipelineResult)
  const scripts = result?.final_scripts?.scripts || [];
  const bestVariantId = result?.evaluation_round_1?.consensus?.best_variant_id;
  const audioFiles = result?.audio?.audio_files || [];
  const sessionId = result?.session_id || "";
  const voiceUsed = result?.audio?.voice_used;
  const voiceSelection = result?.voice_selection as VoiceSelection | undefined;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--card-border)] bg-[var(--card)]/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">
                OBD SuperStar Agent
              </h1>
              <p className="text-xs text-[var(--muted)]">
                AI-Powered OBD Script & Audio Generator
              </p>
            </div>
          </div>

          {/* Provider selector */}
          <div className="flex items-center gap-2">
            <Settings2 className="w-4 h-4 text-gray-500" />
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="text-xs px-2 py-1 rounded-lg bg-[var(--card)] border border-[var(--card-border)] text-gray-400 focus:outline-none"
            >
              <option value="azure_openai">GPT-5.1 (Azure OpenAI)</option>
            </select>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8">
        {/* ── INPUT STEP ── */}
        {wizardStep === "input" && (
          <div className="animate-fade-in">
            {/* Hero */}
            <div className="text-center mb-10">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-brand-500/10 border border-brand-500/20 text-brand-400 text-xs mb-4">
                <Sparkles className="w-3 h-3" />
                Multi-Agent AI Pipeline
              </div>
              <h2 className="text-3xl font-bold text-white mb-3">
                Generate OBD Scripts & Audio
              </h2>
              <p className="text-gray-400 max-w-lg mx-auto">
                Upload your product documentation, select the target market, and
                let our 6-agent AI pipeline create culturally-relevant OBD
                scripts with professional audio recordings.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Left: Product upload */}
              <div className="space-y-6">
                <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                  <ProductUpload
                    value={productText}
                    onChange={setProductText}
                    fileName={fileName}
                    onFileNameChange={setFileName}
                  />
                </div>
              </div>

              {/* Right: Country & Telco */}
              <div className="space-y-6">
                <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                  <CountryTelcoSelect
                    country={country}
                    telco={telco}
                    language={language}
                    onCountryChange={setCountry}
                    onTelcoChange={setTelco}
                    onLanguageChange={setLanguage}
                  />
                </div>
              </div>
            </div>

            {/* Start button */}
            <div className="flex justify-center mt-10">
              <button
                onClick={startPipeline}
                disabled={!canStart}
                className="group flex items-center gap-3 px-8 py-4 rounded-2xl bg-gradient-to-r from-brand-600 to-brand-700 text-white font-semibold text-lg shadow-lg shadow-brand-500/20 hover:shadow-brand-500/30 hover:from-brand-500 hover:to-brand-600 transition-all duration-200 disabled:opacity-30 disabled:cursor-not-allowed disabled:shadow-none"
              >
                <Rocket className="w-5 h-5" />
                Generate OBD Campaign
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>

            {!canStart && (
              <p className="text-center text-xs text-[var(--muted)] mt-3">
                Please provide product documentation and select a country and
                telco to continue.
              </p>
            )}
          </div>
        )}

        {/* ── RUNNING STEP ── */}
        {wizardStep === "running" && (
          <div className="animate-fade-in">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-white mb-2">
                Pipeline Running
              </h2>
              <p className="text-gray-400">
                {country} / {telco} &mdash; Click &quot;View Output&quot; on each completed agent to review its results
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
              <PipelineProgress steps={progressSteps} />
            </div>

            {error && (
              <div className="mt-6 p-4 rounded-xl bg-[var(--error)]/10 border border-[var(--error)]/20">
                <p className="text-sm text-[var(--error)]">{error}</p>
                <button
                  onClick={() => setWizardStep("input")}
                  className="mt-3 flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Back to input
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── RESULTS STEP ── */}
        {wizardStep === "results" && result && (
          <div className="animate-fade-in">
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-2xl font-bold text-white mb-1">
                  Campaign Ready
                </h2>
                <p className="text-gray-400">
                  {country} / {telco} &mdash; Session: {sessionId}
                </p>
              </div>
              <button
                onClick={() => {
                  setWizardStep("input");
                  setResult(null);
                  setError(null);
                }}
                className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--card-border)] text-sm text-gray-400 hover:text-white hover:border-brand-500/30 transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                New Campaign
              </button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8">
              {/* Scripts */}
              <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                <ScriptReview
                  scripts={scripts}
                  bestVariantId={bestVariantId}
                  sessionId={sessionId}
                />
              </div>

              {/* Voice Selection & Audio */}
              <div className="space-y-6">
                {voiceSelection && (
                  <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                    <VoiceInfoPanel voiceSelection={voiceSelection} />
                  </div>
                )}

                {audioFiles.length > 0 && (
                  <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                    <AudioPlayer
                      sessionId={sessionId}
                      audioFiles={audioFiles}
                      voiceInfo={
                        voiceUsed
                          ? {
                              name: voiceUsed.name,
                              voice_id: voiceUsed.voice_id,
                              settings: voiceUsed.settings,
                            }
                          : undefined
                      }
                    />
                  </div>
                )}

                {voiceSelection && audioFiles.length === 0 && (
                  <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                    <div className="text-center py-6 space-y-3">
                      <div className="w-12 h-12 mx-auto rounded-xl bg-[var(--warning)]/15 flex items-center justify-center">
                        <Mic2 className="w-6 h-6 text-[var(--warning)]" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-300">Audio Generation Not Available</p>
                        <p className="text-xs text-[var(--muted)] mt-1">
                          Add a valid <code className="px-1.5 py-0.5 rounded bg-[var(--background)] text-brand-400 text-xs">ELEVENLABS_API_KEY</code> to your <code className="px-1.5 py-0.5 rounded bg-[var(--background)] text-brand-400 text-xs">.env</code> file to enable voice recordings.
                        </p>
                        <p className="text-xs text-[var(--muted)] mt-2">
                          The voice parameters above are ready to use with ElevenLabs API directly.
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {!voiceSelection && audioFiles.length === 0 && (
                  <div className="p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                    <p className="text-center text-sm text-[var(--muted)] py-4">
                      Voice selection and audio generation will appear here when enabled.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Pipeline completed progress */}
            <div className="mt-8 p-6 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
              <PipelineProgress
                steps={PIPELINE_STEPS.map((s) => ({
                  ...s,
                  status: "completed" as const,
                  message: "Done",
                }))}
              />
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-[var(--card-border)] mt-16">
        <div className="max-w-5xl mx-auto px-6 py-4 text-center text-xs text-[var(--muted)]">
          OBD SuperStar Agent &mdash; Powered by Claude, GPT-4 & ElevenLabs V3
        </div>
      </footer>
    </div>
  );
}
