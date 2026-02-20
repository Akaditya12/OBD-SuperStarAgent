"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Play,
  Pause,
  FileText,
  Volume2,
  Download,
  Save,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Zap,
  ArrowRight,
  RotateCcw,
  Copy,
  Check,
  Pencil,
  X,
  RefreshCw,
  Loader2,
} from "lucide-react";
import ProductUpload from "@/components/ProductUpload";
import CountryTelcoSelect from "@/components/CountryTelcoSelect";
import PipelineProgress from "@/components/PipelineProgress";
import type { ProgressStep } from "@/components/PipelineProgress";
import ProductPresets, { BNG_PRODUCTS } from "@/components/ProductPresets";
import type { ProductPreset } from "@/components/ProductPresets";
import PromotionTypeSelect, { PROMOTION_TYPES } from "@/components/PromotionTypeSelect";
import type { PromotionType } from "@/components/PromotionTypeSelect";
import VoiceInfoPanel from "@/components/VoiceInfoPanel";
import { useToast } from "@/components/ToastProvider";
import type {
  PipelineResult,
  WsProgressMessage,
  Script,
  AudioFile,
  HookPreviewResult,
  AudioResult,
} from "@/lib/types";
import { Music, Radio } from "lucide-react";

type WizardStep = "input" | "running" | "results";

const PIPELINE_STEPS: { agent: string; label: string }[] = [
  { agent: "ProductAnalyzer", label: "Product Analysis" },
  { agent: "MarketResearcher", label: "Market Research" },
  { agent: "ScriptWriter", label: "Script Writing" },
  { agent: "EvalPanel", label: "Evaluation Panel" },
  { agent: "ScriptWriter_Revision", label: "Script Revision" },
  { agent: "VoiceSelector", label: "Voice Selection" },
  { agent: "AudioProducer", label: "Audio Production" },
];

export default function HomePage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { toast } = useToast();

  // Auth
  const [authChecked, setAuthChecked] = useState(false);
  const [username, setUsername] = useState("user");

  // Form
  const [selectedProduct, setSelectedProduct] = useState("eva");
  const [productText, setProductText] = useState(BNG_PRODUCTS[0].fullDescription);
  const [fileName, setFileName] = useState("");
  const [country, setCountry] = useState("");
  const [telco, setTelco] = useState("");
  const [language, setLanguage] = useState("");
  const [promotionType, setPromotionType] = useState("obd_standard");
  const [ttsEngine, setTtsEngine] = useState<"auto" | "murf" | "elevenlabs" | "edge-tts">("auto");

  // Handle ?product= URL param from sidebar clicks
  useEffect(() => {
    const productParam = searchParams.get("product");
    if (productParam) {
      const found = BNG_PRODUCTS.find((p) => p.id === productParam);
      if (found && found.id !== "custom") {
        setSelectedProduct(found.id);
        setProductText(found.fullDescription);
        setFileName("");
        setWizardStep("input");
      }
    }
  }, [searchParams]);

  // Wizard
  const [wizardStep, setWizardStep] = useState<WizardStep>("input");
  const [progressSteps, setProgressSteps] = useState<ProgressStep[]>(
    PIPELINE_STEPS.map((s) => ({ ...s, status: "pending", message: "" }))
  );
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [error, setError] = useState("");

  // Save
  const [campaignName, setCampaignName] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Audio
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Script expand & edit
  const [expandedScript, setExpandedScript] = useState<number | null>(null);
  const [copiedScript, setCopiedScript] = useState<number | null>(null);
  const [editingVariant, setEditingVariant] = useState<number | null>(null);
  const [editDraft, setEditDraft] = useState<Record<string, string>>({});
  const [editedVariants, setEditedVariants] = useState<Set<number>>(new Set());
  const [savingEdit, setSavingEdit] = useState(false);

  // Audio regeneration
  const [regenVariant, setRegenVariant] = useState<number | null>(null);

  // Hook preview voice selection & full audio generation
  const [voiceChoices, setVoiceChoices] = useState<Record<number, number>>({});
  const [bgmStyle, setBgmStyle] = useState<"upbeat" | "calm" | "corporate">("upbeat");
  const [generatingFullAudio, setGeneratingFullAudio] = useState(false);
  const [bgmPreviewPlaying, setBgmPreviewPlaying] = useState<string | null>(null);
  const bgmAudioRef = useRef<HTMLAudioElement | null>(null);

  // WebSocket ref
  const wsRef = useRef<WebSocket | null>(null);

  // ── Auth Check ──
  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => res.json())
      .then((data) => {
        if (data.authenticated) {
          setUsername(data.username || "user");
          setAuthChecked(true);
        } else {
          router.push("/login");
        }
      })
      .catch(() => {
        setAuthChecked(true);
      });
  }, [router]);

  // ── Update Step helper ──
  const updateStep = useCallback(
    (agent: string, status: string, message: string) => {
      setProgressSteps((prev) =>
        prev.map((s) =>
          s.agent === agent
            ? { ...s, status: status as ProgressStep["status"], message }
            : s
        )
      );
    },
    []
  );

  // ── WebSocket for pipeline progress ──
  const connectProgressWs = useCallback(
    (sessionId: string) => {
      const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      const wsUrl = `${protocol}//${window.location.host}/ws/progress/${sessionId}`;
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onmessage = (event) => {
        try {
          const data: WsProgressMessage = JSON.parse(event.data);

          if (data.status === "done" || data.status === "error") {
            if (data.status === "done" && data.result) {
              setResult(data.result as PipelineResult);
              setWizardStep("results");
              localStorage.removeItem("obd_active_session");
              toast("success", "Campaign generated successfully!");
            } else if (data.status === "error") {
              setError(data.message || "Pipeline failed");
              setWizardStep("results");
              localStorage.removeItem("obd_active_session");
              toast("error", data.message || "Pipeline failed");
            }
          } else {
            updateStep(
              data.agent || "",
              data.status || "",
              data.message || ""
            );
          }
        } catch {
          // ignore parse errors
        }
      };

      ws.onerror = () => {
        setError("Connection lost. Check pipeline status.");
        toast("warning", "WebSocket connection lost");
      };
    },
    [updateStep, toast]
  );

  // ── Resume pipeline on mount ──
  useEffect(() => {
    const activeSession = localStorage.getItem("obd_active_session");
    if (!activeSession) return;

    (async () => {
      try {
        const res = await fetch(`/api/generate/${activeSession}/status`);
        if (!res.ok) {
          localStorage.removeItem("obd_active_session");
          return;
        }
        const data = await res.json();
        if (data.status === "done" && data.result) {
          setResult(data.result);
          setWizardStep("results");
          localStorage.removeItem("obd_active_session");
          if (data.progress) {
            for (const msg of data.progress) {
              updateStep(msg.agent || "", msg.status || "", msg.message || "");
            }
          }
        } else if (data.status === "error") {
          setError(data.error || "Pipeline failed");
          setWizardStep("results");
          localStorage.removeItem("obd_active_session");
        } else {
          setWizardStep("running");
          if (data.progress) {
            for (const msg of data.progress) {
              updateStep(msg.agent || "", msg.status || "", msg.message || "");
            }
          }
          connectProgressWs(activeSession);
        }
      } catch {
        localStorage.removeItem("obd_active_session");
      }
    })();
  }, [connectProgressWs, updateStep]);

  // ── Start pipeline ──
  const handleStart = async () => {
    if (!productText.trim() || !country || !telco) {
      toast("warning", "Please fill in all required fields");
      return;
    }

    setWizardStep("running");
    setError("");
    setResult(null);
    setSaved(false);
    setProgressSteps(
      PIPELINE_STEPS.map((s) => ({ ...s, status: "pending", message: "" }))
    );

    try {
      const promoType = PROMOTION_TYPES.find((t) => t.id === promotionType);
      const promoGuidance = promoType
        ? `\n\n--- PROMOTION TYPE: ${promoType.name} ---\n${promoType.scriptGuidance}`
        : "";
      const fullProductText = productText + promoGuidance;

      const res = await fetch("/api/generate/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          product_text: fullProductText,
          country,
          telco,
          language: language || undefined,
          tts_engine: ttsEngine === "auto" ? undefined : ttsEngine,
        }),
      });

      if (!res.ok) {
        const err = await res.json();
        setError(err.error || "Failed to start pipeline");
        setWizardStep("input");
        toast("error", "Failed to start pipeline");
        return;
      }

      const { session_id } = await res.json();
      localStorage.setItem("obd_active_session", session_id);
      connectProgressWs(session_id);
    } catch (e) {
      setError("Network error. Please try again.");
      setWizardStep("input");
      toast("error", "Network error");
    }
  };

  // ── Save campaign ──
  const handleSaveCampaign = async () => {
    if (!campaignName.trim() || !result?.session_id) return;
    setSaving(true);
    try {
      const res = await fetch("/api/campaigns", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: result.session_id,
          name: campaignName.trim(),
        }),
      });
      if (res.ok) {
        setSaved(true);
        toast("success", "Campaign saved!");
      } else {
        toast("error", "Failed to save campaign");
      }
    } catch {
      toast("error", "Failed to save campaign");
    } finally {
      setSaving(false);
    }
  };

  // ── Audio playback ──
  const toggleAudio = (url: string) => {
    if (playingAudio === url) {
      audioRef.current?.pause();
      setPlayingAudio(null);
    } else {
      if (audioRef.current) audioRef.current.pause();
      const audio = new Audio(url);
      audioRef.current = audio;
      audio.play();
      audio.onended = () => setPlayingAudio(null);
      setPlayingAudio(url);
    }
  };

  // ── Copy script ──
  const copyScript = (text: string, idx: number) => {
    navigator.clipboard.writeText(text);
    setCopiedScript(idx);
    toast("info", "Script copied to clipboard");
    setTimeout(() => setCopiedScript(null), 2000);
  };

  // ── Script editing ──
  const startEditing = (script: Script) => {
    const vid = script.variant_id;
    setEditingVariant(vid);
    setEditDraft({
      hook: script.hook || "",
      body: script.body || "",
      cta: script.cta || "",
      full_script: script.full_script || "",
      fallback_1: script.fallback_1 || "",
      fallback_2: script.fallback_2 || "",
      polite_closure: script.polite_closure || "",
    });
  };

  const cancelEditing = () => {
    setEditingVariant(null);
    setEditDraft({});
  };

  const saveEdit = async (variantId: number) => {
    if (!result?.session_id) return;
    setSavingEdit(true);
    try {
      const res = await fetch(
        `/api/sessions/${result.session_id}/scripts/${variantId}`,
        {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(editDraft),
        }
      );
      if (res.ok) {
        const { script: updated } = await res.json();
        // Update local state
        const updateScripts = (sr: typeof result.final_scripts) => {
          if (!sr?.scripts) return;
          const idx = sr.scripts.findIndex((s) => s.variant_id === variantId);
          if (idx >= 0) sr.scripts[idx] = { ...sr.scripts[idx], ...updated };
        };
        if (result.final_scripts) updateScripts(result.final_scripts);
        if (result.revised_scripts_round_1) updateScripts(result.revised_scripts_round_1);
        if (result.initial_scripts) updateScripts(result.initial_scripts);
        setResult({ ...result });
        setEditedVariants((prev) => new Set(prev).add(variantId));
        setEditingVariant(null);
        setEditDraft({});
        toast("success", "Script updated");
      } else {
        toast("error", "Failed to save script");
      }
    } catch {
      toast("error", "Failed to save script");
    } finally {
      setSavingEdit(false);
    }
  };

  // ── Regenerate audio for a single variant ──
  const regenerateAudio = async (variantId: number) => {
    if (!result?.session_id) return;
    setRegenVariant(variantId);
    try {
      const res = await fetch(
        `/api/sessions/${result.session_id}/regenerate-audio/${variantId}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tts_engine: ttsEngine === "auto" ? undefined : ttsEngine,
          }),
        }
      );
      if (res.ok) {
        const data = await res.json();
        const newFiles: AudioFile[] = data.audio_files || [];
        // Replace old audio files for this variant
        const existingAudio = result.audio || { session_id: result.session_id, session_dir: "", voice_used: { voice_id: "", name: "", settings: {} as any }, audio_files: [], summary: { total_generated: 0, total_failed: 0, variants_count: 0 } };
        const otherFiles = (existingAudio.audio_files || []).filter(
          (af: AudioFile) => af.variant_id !== variantId
        );
        existingAudio.audio_files = [...otherFiles, ...newFiles];
        existingAudio.summary.total_generated = existingAudio.audio_files.filter((f: AudioFile) => !f.error).length;
        setResult({ ...result, audio: { ...existingAudio } });
        setEditedVariants((prev) => {
          const next = new Set(prev);
          next.delete(variantId);
          return next;
        });
        toast("success", `Audio regenerated for Variant ${variantId}`);
      } else {
        toast("error", "Failed to regenerate audio");
      }
    } catch {
      toast("error", "Failed to regenerate audio");
    } finally {
      setRegenVariant(null);
    }
  };

  // ── BGM preview playback ──
  const toggleBgmPreview = (style: string) => {
    if (bgmPreviewPlaying === style) {
      bgmAudioRef.current?.pause();
      setBgmPreviewPlaying(null);
      return;
    }
    if (bgmAudioRef.current) {
      bgmAudioRef.current.pause();
    }
    const audio = new Audio(`/api/bgm-preview/${style}`);
    audio.onended = () => setBgmPreviewPlaying(null);
    audio.play();
    bgmAudioRef.current = audio;
    setBgmPreviewPlaying(style);
  };

  // ── Generate full audio (Phase 2) -- async job with polling ──
  const generateFullAudio = async () => {
    if (!result?.session_id) return;
    setGeneratingFullAudio(true);
    try {
      const sid = result.hook_previews?.session_id || result.session_id;
      const finalScripts = result.final_scripts || result.revised_scripts_round_1 || result.initial_scripts;
      const startRes = await fetch(
        `/api/sessions/${sid}/generate-full-audio`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            voice_choices: voiceChoices,
            bgm_style: bgmStyle,
            tts_engine: ttsEngine === "auto" ? undefined : ttsEngine,
            scripts: finalScripts,
            voice_selection: result.voice_selection,
            country,
            language: language || undefined,
          }),
        }
      );
      if (!startRes.ok) {
        const err = await startRes.json().catch(() => ({ error: "Unknown error" }));
        toast("error", err.error || "Failed to start audio generation");
        return;
      }
      const { job_id } = await startRes.json();

      // Poll until done
      const poll = async (): Promise<void> => {
        for (let i = 0; i < 120; i++) {
          await new Promise((r) => setTimeout(r, 3000));
          try {
            const pollRes = await fetch(`/api/audio-jobs/${job_id}`);
            if (!pollRes.ok) continue;
            const job = await pollRes.json();
            if (job.status === "done") {
              const audioResult: AudioResult = job.audio;
              setResult((prev) => prev ? { ...prev, audio: audioResult } : prev);
              toast("success", `Generated ${audioResult.summary?.total_generated || 0} final audio files!`);
              return;
            }
            if (job.status === "error") {
              toast("error", job.error || "Audio generation failed");
              return;
            }
          } catch { /* retry */ }
        }
        toast("error", "Audio generation timed out");
      };
      await poll();
    } catch {
      toast("error", "Network error generating full audio");
    } finally {
      setGeneratingFullAudio(false);
    }
  };

  // ── Reset ──
  const handleReset = () => {
    setWizardStep("input");
    setResult(null);
    setError("");
    setSaved(false);
    setCampaignName("");
    setVoiceChoices({});
    setBgmStyle("upbeat");
    setGeneratingFullAudio(false);
    setBgmPreviewPlaying(null);
    if (bgmAudioRef.current) bgmAudioRef.current.pause();
    setProgressSteps(
      PIPELINE_STEPS.map((s) => ({ ...s, status: "pending", message: "" }))
    );
    if (wsRef.current) wsRef.current.close();
  };

  // Wait for auth
  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Extract scripts, hook previews, and audio from result
  const scripts =
    result?.final_scripts?.scripts ||
    result?.revised_scripts_round_1?.scripts ||
    result?.initial_scripts?.scripts ||
    [];
  const hookPreviews = result?.hook_previews;
  const hookPreviewFiles = (hookPreviews?.hook_previews || []).filter(
    (af: AudioFile) => af.file_name && !af.error
  );
  const voicePool = hookPreviews?.voice_pool || [];
  const audioFiles = (result?.audio?.audio_files || []).filter(
    (af: AudioFile) => af.file_name && !af.error
  );
  const voiceSelection = result?.voice_selection;
  const hookSessionId = hookPreviews?.session_id || result?.session_id || "";
  const resolvedEngine = hookPreviews?.tts_engine || result?.audio?.tts_engine;
  const resolvedEngineLabel = resolvedEngine === "murf" ? "Murf AI" : resolvedEngine === "edge-tts" ? "Edge TTS" : resolvedEngine === "elevenlabs" ? "ElevenLabs" : null;

  const WIZARD_LABELS = ["Configure", "Generate", "Results"];

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-8 max-w-5xl mx-auto">
      {/* ── Step Indicator ── */}
      <div className="flex items-center justify-center gap-2 mb-10">
        {WIZARD_LABELS.map((label, i) => {
          const stepIndex =
            wizardStep === "input" ? 0 : wizardStep === "running" ? 1 : 2;
          const isActive = i === stepIndex;
          const isComplete = i < stepIndex;
          return (
            <div key={label} className="flex items-center gap-2">
              {i > 0 && (
                <div
                  className={`w-8 h-px transition-colors ${isComplete ? "bg-[var(--accent)]" : "bg-[var(--card-border)]"}`}
                />
              )}
              <div className="flex items-center gap-2">
                <div
                  className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-semibold transition-all ${isActive
                    ? "bg-[var(--accent)] text-white glow-brand"
                    : isComplete
                      ? "bg-[var(--accent-subtle)] text-[var(--accent)]"
                      : "bg-[var(--card)] text-[var(--text-tertiary)]"
                    }`}
                >
                  {isComplete ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : (
                    i + 1
                  )}
                </div>
                <span
                  className={`text-xs font-medium hidden sm:inline ${isActive
                    ? "text-[var(--text-primary)]"
                    : isComplete
                      ? "text-[var(--text-secondary)]"
                      : "text-[var(--text-tertiary)]"
                    }`}
                >
                  {label}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── INPUT STEP ── */}
      {wizardStep === "input" && (
        <div className="animate-fade-in">
          {/* Hero */}
          <div className="text-center mb-10">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] text-xs font-medium mb-4 border border-[var(--accent)]/20">
              <Sparkles className="w-3.5 h-3.5" />
              AI-Powered 6-Agent Pipeline
            </div>
            <h1 className="text-3xl sm:text-4xl font-bold mb-3">
              <span className="gradient-text">Generate OBD Campaigns</span>
            </h1>
            <p className="text-[var(--text-tertiary)] text-sm max-w-md mx-auto">
              Create culturally-relevant promotional scripts and audio with our
              multi-agent AI system.
            </p>
          </div>

          {/* Form */}
          <div className="max-w-2xl mx-auto space-y-5">
            {/* BNG Product Presets */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors">
              <ProductPresets
                selectedProduct={selectedProduct}
                onSelect={(product: ProductPreset) => {
                  setSelectedProduct(product.id);
                  if (product.id !== "custom" && product.fullDescription) {
                    setProductText(product.fullDescription);
                    setFileName("");
                  } else if (product.id === "custom") {
                    setProductText("");
                    setFileName("");
                  }
                }}
              />
            </div>

            {/* Product upload / paste (always visible for editing or custom) */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors">
              <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-3">
                <FileText className="w-4 h-4 text-[var(--accent)]" />
                Product Documentation
                <span className="text-[var(--error)]">*</span>
                {selectedProduct !== "custom" && (
                  <span className="text-[10px] text-[var(--text-tertiary)] ml-1">
                    (auto-filled from preset — edit freely)
                  </span>
                )}
              </label>
              <ProductUpload
                value={productText}
                onChange={(text) => {
                  setProductText(text);
                  if (selectedProduct !== "custom") setSelectedProduct("custom");
                }}
                fileName={fileName}
                onFileNameChange={setFileName}
              />
            </div>

            {/* Promotion Type */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors">
              <PromotionTypeSelect
                selected={promotionType}
                onChange={(type: PromotionType) => setPromotionType(type.id)}
              />
            </div>

            {/* Country, Telco, Language */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors">
              <CountryTelcoSelect
                country={country}
                telco={telco}
                language={language}
                onCountryChange={setCountry}
                onTelcoChange={setTelco}
                onLanguageChange={setLanguage}
              />
            </div>

            {/* TTS Engine */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors">
              <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-3">
                <Volume2 className="w-4 h-4 text-[var(--accent)]" />
                Voice Engine
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                {([
                  { id: "auto", label: "Auto", desc: "Best available" },
                  { id: "murf", label: "Murf AI", desc: "Premium" },
                  { id: "elevenlabs", label: "ElevenLabs", desc: "Premium" },
                  { id: "edge-tts", label: "Free TTS", desc: "edge-tts" },
                ] as const).map((opt) => (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => setTtsEngine(opt.id)}
                    className={`px-3 py-2.5 rounded-xl text-left border transition-all ${
                      ttsEngine === opt.id
                        ? "border-[var(--accent)] bg-[var(--accent-subtle)] ring-1 ring-[var(--accent)]/30"
                        : "border-[var(--card-border)] bg-[var(--input-bg)] hover:border-[var(--card-border-hover)]"
                    }`}
                  >
                    <div className={`text-xs font-medium ${ttsEngine === opt.id ? "text-[var(--accent)]" : "text-[var(--text-primary)]"}`}>
                      {opt.label}
                    </div>
                    <div className="text-[10px] text-[var(--text-tertiary)]">{opt.desc}</div>
                  </button>
                ))}
              </div>
            </div>

            {/* Start button */}
            <button
              onClick={handleStart}
              disabled={!productText.trim() || !country || !telco}
              className="w-full py-3.5 rounded-2xl text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-40 disabled:cursor-not-allowed glow-brand"
              style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
            >
              <Zap className="w-4 h-4" />
              Generate Campaign
              <ArrowRight className="w-4 h-4" />
            </button>

            {/* BNG Stats Bar */}
            <div className="flex items-center justify-center gap-6 py-4 text-[10px] text-[var(--text-tertiary)]">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-[var(--success)] animate-pulse" />
                <span>100+ Countries</span>
              </div>
              <div className="w-px h-3 bg-[var(--card-border)]" />
              <span>160+ Telco Partners</span>
              <div className="w-px h-3 bg-[var(--card-border)]" />
              <span>300M+ Daily Calls</span>
              <div className="w-px h-3 bg-[var(--card-border)]" />
              <span>290M+ Active Users</span>
            </div>
          </div>
        </div>
      )}

      {/* ── RUNNING STEP ── */}
      {wizardStep === "running" && (
        <div className="animate-fade-in max-w-2xl mx-auto">
          <div className="text-center mb-8">
            <h2 className="text-xl font-bold text-[var(--text-primary)] mb-2">
              Generating Your Campaign
            </h2>
            <p className="text-sm text-[var(--text-tertiary)]">
              Our 6-agent pipeline is crafting your scripts...
            </p>
          </div>
          <PipelineProgress steps={progressSteps} />
        </div>
      )}

      {/* ── RESULTS STEP ── */}
      {wizardStep === "results" && (
        <div className="animate-fade-in space-y-6">
          {/* Error */}
          {error && (
            <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
              {error}
            </div>
          )}

          {/* Success header */}
          {result && !error && (
            <div className="text-center mb-6">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[var(--success)]/10 text-[var(--success)] text-sm font-medium border border-[var(--success)]/20 mb-3">
                <CheckCircle2 className="w-4 h-4" />
                {audioFiles.length > 0 ? "Campaign Generated Successfully" : "Scripts & Hook Previews Ready"}
              </div>
              <p className="text-sm text-[var(--text-tertiary)]">
                {scripts.length} script{scripts.length !== 1 ? "s" : ""}
                {hookPreviewFiles.length > 0 && !audioFiles.length && (
                  <> — listen to hook previews below and pick your voices</>
                )}
                {audioFiles.length > 0 && (
                  <> and {audioFiles.length} audio file{audioFiles.length !== 1 ? "s" : ""} ready</>
                )}
              </p>
              {resolvedEngineLabel && (
                <p className="text-[10px] text-[var(--text-tertiary)] mt-1">
                  TTS Engine: <span className="text-[var(--accent)] font-medium">{resolvedEngineLabel}</span>
                </p>
              )}
            </div>
          )}

          {/* Voice Analytics */}
          {voiceSelection && (
            <VoiceInfoPanel
              voiceSelection={voiceSelection}
              ttsEngine={result?.audio?.tts_engine}
              edgeVoice={result?.audio?.voice_used?.voice_id}
            />
          )}

          {/* Scripts */}
          {scripts.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[var(--accent)]" />
                  Generated Scripts
                </h3>
                {result?.session_id && (
                  <div className="flex items-center gap-2">
                    <a
                      href={`/api/sessions/${result.session_id}/scripts?fmt=text`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      Text
                    </a>
                    <a
                      href={`/api/sessions/${result.session_id}/scripts?fmt=json`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] transition-colors"
                    >
                      <Download className="w-3 h-3" />
                      JSON
                    </a>
                  </div>
                )}
              </div>
              {scripts.map((script: Script, idx: number) => {
                const vid = script.variant_id || idx + 1;
                const isEditing = editingVariant === vid;
                const isEdited = editedVariants.has(vid);
                const SECTIONS = ["hook", "body", "cta", "full_script", "fallback_1", "fallback_2", "polite_closure"] as const;

                return (
                  <div
                    key={idx}
                    className={`rounded-2xl bg-[var(--card)] border overflow-hidden transition-colors ${
                      isEdited
                        ? "border-amber-500/40 bg-amber-500/5"
                        : "border-[var(--card-border)] hover:border-[var(--card-border-hover)]"
                    }`}
                  >
                    <button
                      className="w-full flex items-center justify-between px-5 py-4 text-left"
                      onClick={() =>
                        setExpandedScript(expandedScript === idx ? null : idx)
                      }
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-[var(--text-primary)]">
                          Variant {vid}
                        </span>
                        <span className="text-xs text-[var(--text-tertiary)]">
                          {script.theme || ""}
                        </span>
                        {isEdited && (
                          <span className="text-[9px] px-1.5 py-0.5 rounded-full bg-amber-500/20 text-amber-400 font-medium">
                            edited
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] text-[var(--text-tertiary)] bg-[var(--input-bg)] px-2 py-0.5 rounded-full">
                          {script.word_count || "?"} words
                        </span>
                        {expandedScript === idx ? (
                          <ChevronUp className="w-4 h-4 text-[var(--text-tertiary)]" />
                        ) : (
                          <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
                        )}
                      </div>
                    </button>
                    {expandedScript === idx && (
                      <div className="px-5 pb-5 space-y-3 animate-fade-in border-t border-[var(--card-border)]">
                        {/* Edit / Regen toolbar */}
                        <div className="flex items-center gap-2 pt-2">
                          {!isEditing ? (
                            <button
                              onClick={() => startEditing(script)}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] transition-colors"
                            >
                              <Pencil className="w-3 h-3" />
                              Edit Script
                            </button>
                          ) : (
                            <>
                              <button
                                onClick={() => saveEdit(vid)}
                                disabled={savingEdit}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-[var(--accent)] text-white hover:opacity-90 transition-colors disabled:opacity-50"
                              >
                                {savingEdit ? <Loader2 className="w-3 h-3 animate-spin" /> : <Check className="w-3 h-3" />}
                                Save
                              </button>
                              <button
                                onClick={cancelEditing}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-red-500/10 border border-[var(--card-border)] transition-colors"
                              >
                                <X className="w-3 h-3" />
                                Cancel
                              </button>
                            </>
                          )}
                          {isEdited && !isEditing && (
                            <button
                              onClick={() => regenerateAudio(vid)}
                              disabled={regenVariant === vid}
                              className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-amber-400 hover:bg-amber-500/10 border border-amber-500/30 transition-colors disabled:opacity-50"
                            >
                              {regenVariant === vid ? <Loader2 className="w-3 h-3 animate-spin" /> : <RefreshCw className="w-3 h-3" />}
                              Re-generate Audio
                            </button>
                          )}
                        </div>

                        {SECTIONS.map((section) => {
                          const value = isEditing ? (editDraft[section] ?? "") : (script[section] || "");
                          if (!value && !isEditing) return null;
                          return (
                            <div key={section}>
                              <div className="flex items-center justify-between mb-1">
                                <span className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-medium">
                                  {section.replace(/_/g, " ")}
                                </span>
                                {!isEditing && (
                                  <button
                                    onClick={() => copyScript(script[section], idx)}
                                    className="p-1 rounded hover:bg-[var(--accent-subtle)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] transition-colors"
                                  >
                                    {copiedScript === idx ? (
                                      <Check className="w-3 h-3 text-[var(--success)]" />
                                    ) : (
                                      <Copy className="w-3 h-3" />
                                    )}
                                  </button>
                                )}
                              </div>
                              {isEditing ? (
                                <textarea
                                  value={editDraft[section] ?? ""}
                                  onChange={(e) =>
                                    setEditDraft((prev) => ({ ...prev, [section]: e.target.value }))
                                  }
                                  rows={section === "full_script" ? 5 : 3}
                                  className="w-full text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--input-bg)] px-3 py-2 rounded-lg border border-[var(--card-border)] focus:border-[var(--accent)]/50 focus:outline-none resize-y"
                                />
                              ) : (
                                <p className="text-xs text-[var(--text-secondary)] leading-relaxed bg-[var(--input-bg)] px-3 py-2 rounded-lg">
                                  {value}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* ── Hook Previews: voice selection (Phase 1) ── */}
          {hookPreviewFiles.length > 0 && !audioFiles.length && (() => {
            const variantIds = [...new Set(hookPreviewFiles.map((af: AudioFile) => af.variant_id))].sort((a, b) => a - b);

            return (
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
                  <Radio className="w-4 h-4 text-[var(--accent)]" />
                  Choose Your Voice
                  <span className="text-[10px] text-[var(--text-tertiary)] ml-1 font-normal">
                    Listen to hook previews and select a voice for each variant
                  </span>
                </h3>

                {variantIds.map((vid) => {
                  const variantPreviews = hookPreviewFiles.filter((af: AudioFile) => af.variant_id === vid);
                  const voiceIndices = [...new Set(variantPreviews.map((af: AudioFile) => af.voice_index || 1))].sort();
                  const selectedVoice = voiceChoices[vid] || 1;

                  return (
                    <div key={vid} className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] overflow-hidden">
                      <div className="px-5 py-3 border-b border-[var(--card-border)] bg-[var(--input-bg)]/50">
                        <span className="text-xs font-medium text-[var(--text-primary)]">
                          Variant {vid}
                        </span>
                        <span className="text-[10px] text-[var(--text-tertiary)] ml-2">
                          {scripts.find((s: Script) => s.variant_id === vid)?.theme || ""}
                        </span>
                      </div>
                      <div className="p-4 space-y-2">
                        {voiceIndices.map((voiceIdx) => {
                          const preview = variantPreviews.find((af: AudioFile) => (af.voice_index || 1) === voiceIdx);
                          if (!preview) return null;
                          const audioUrl = `/outputs/${hookSessionId}/${preview.file_name}`;
                          const isPlaying = playingAudio === audioUrl;
                          const isSelected = selectedVoice === voiceIdx;
                          const voiceLabel = preview.voice_label || voicePool.find(v => v.voice_index === voiceIdx)?.voice_label || `Voice ${voiceIdx}`;

                          return (
                            <label
                              key={voiceIdx}
                              className={`flex items-center gap-3 p-3 rounded-xl cursor-pointer transition-all ${
                                isSelected
                                  ? "bg-[var(--accent-subtle)] border border-[var(--accent)]/40 ring-1 ring-[var(--accent)]/20"
                                  : "bg-[var(--input-bg)] border border-transparent hover:bg-[var(--accent-subtle)]/30"
                              }`}
                            >
                              <input
                                type="radio"
                                name={`voice-${vid}`}
                                checked={isSelected}
                                onChange={() => setVoiceChoices(prev => ({ ...prev, [vid]: voiceIdx }))}
                                className="sr-only"
                              />
                              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center flex-shrink-0 transition-colors ${
                                isSelected ? "border-[var(--accent)] bg-[var(--accent)]" : "border-[var(--card-border)]"
                              }`}>
                                {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                              </div>
                              <button
                                type="button"
                                onClick={(e) => { e.preventDefault(); toggleAudio(audioUrl); }}
                                className={`p-2 rounded-lg transition-colors flex-shrink-0 ${
                                  isPlaying
                                    ? "bg-[var(--accent)] text-white"
                                    : "bg-[var(--card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                                }`}
                              >
                                {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                              </button>
                              <div className="flex-1 min-w-0">
                                <p className="text-xs font-medium text-[var(--text-primary)]">{voiceLabel}</p>
                                {preview.file_size_bytes && (
                                  <p className="text-[10px] text-[var(--text-tertiary)]">
                                    Hook preview — {(preview.file_size_bytes / 1024).toFixed(0)} KB
                                  </p>
                                )}
                              </div>
                            </label>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}

                {/* BGM Style Picker with Preview */}
                <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
                  <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] mb-1">
                    <Music className="w-4 h-4 text-[var(--accent)]" />
                    Background Music Style
                  </label>
                  <p className="text-[10px] text-[var(--text-tertiary)] mb-3">
                    Click the play button to preview each style before applying
                  </p>
                  <div className="grid grid-cols-3 gap-2">
                    {([
                      { id: "upbeat" as const, label: "Upbeat", desc: "Energetic, 110 BPM" },
                      { id: "calm" as const, label: "Calm", desc: "Soft piano, 80 BPM" },
                      { id: "corporate" as const, label: "Corporate", desc: "Clean & minimal, 100 BPM" },
                    ]).map((opt) => {
                      const isPlaying = bgmPreviewPlaying === opt.id;
                      return (
                        <div
                          key={opt.id}
                          className={`relative rounded-xl border transition-all ${
                            bgmStyle === opt.id
                              ? "border-[var(--accent)] bg-[var(--accent-subtle)] ring-1 ring-[var(--accent)]/30"
                              : "border-[var(--card-border)] bg-[var(--input-bg)] hover:border-[var(--card-border-hover)]"
                          }`}
                        >
                          <button
                            type="button"
                            onClick={() => setBgmStyle(opt.id)}
                            className="w-full px-3 pt-2.5 pb-8 text-left"
                          >
                            <div className={`text-xs font-medium ${bgmStyle === opt.id ? "text-[var(--accent)]" : "text-[var(--text-primary)]"}`}>
                              {opt.label}
                            </div>
                            <div className="text-[10px] text-[var(--text-tertiary)]">{opt.desc}</div>
                          </button>
                          <button
                            type="button"
                            onClick={(e) => { e.stopPropagation(); toggleBgmPreview(opt.id); }}
                            className={`absolute bottom-2 left-3 right-3 flex items-center justify-center gap-1.5 py-1 rounded-lg text-[10px] font-medium transition-all ${
                              isPlaying
                                ? "bg-[var(--accent)] text-white"
                                : "bg-[var(--card)] text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] border border-[var(--card-border)]"
                            }`}
                          >
                            {isPlaying ? <Pause className="w-2.5 h-2.5" /> : <Play className="w-2.5 h-2.5" />}
                            {isPlaying ? "Stop" : "Preview"}
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Generate Full Audio Button */}
                <button
                  onClick={generateFullAudio}
                  disabled={generatingFullAudio}
                  className="w-full py-3.5 rounded-2xl text-white font-semibold text-sm flex items-center justify-center gap-2 transition-all disabled:opacity-60 disabled:cursor-not-allowed glow-brand"
                  style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
                >
                  {generatingFullAudio ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Generating Full Audio...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4" />
                      Generate Full Audio with Selected Voices
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </div>
            );
          })()}

          {/* ── Final Audio Files (Phase 2 complete) ── */}
          {audioFiles.length > 0 && (() => {
            const audioSessionId = result?.audio?.session_id || result?.session_id || "";
            const variantIds = [...new Set(audioFiles.map((af: AudioFile) => af.variant_id))].sort((a, b) => a - b);

            return (
              <div className="space-y-3">
                <h3 className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
                  <Volume2 className="w-4 h-4 text-[var(--accent)]" />
                  Final Audio Files
                  {result?.audio?.tts_engine && (
                    <span className="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)]">
                      {result.audio.tts_engine === "murf" ? "Murf AI" : result.audio.tts_engine === "edge-tts" ? "Edge TTS" : "ElevenLabs"}
                    </span>
                  )}
                  {result?.audio?.summary?.bgm_style && (
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--input-bg)] text-[var(--text-tertiary)]">
                      {result.audio.summary.bgm_style} BGM
                    </span>
                  )}
                </h3>
                {variantIds.map((vid) => {
                  const variantFiles = audioFiles.filter((af: AudioFile) => af.variant_id === vid);
                  const voiceIndices = [...new Set(variantFiles.map((af: AudioFile) => af.voice_index || 1))].sort();
                  const hasMultiVoice = voiceIndices.length > 1;

                  return (
                    <div key={vid} className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] overflow-hidden">
                      <div className="px-5 py-3 border-b border-[var(--card-border)] bg-[var(--input-bg)]/50">
                        <span className="text-xs font-medium text-[var(--text-primary)]">
                          Variant {vid}
                        </span>
                        <span className="text-[10px] text-[var(--text-tertiary)] ml-2">
                          {variantFiles.length} files
                        </span>
                      </div>
                      <div className="p-4 space-y-3">
                        {voiceIndices.map((voiceIdx) => {
                          const voiceFiles = variantFiles.filter((af: AudioFile) => (af.voice_index || 1) === voiceIdx);
                          const voiceLabel = voiceFiles[0]?.voice_label || `Voice ${voiceIdx}`;

                          return (
                            <div key={voiceIdx}>
                              {hasMultiVoice && (
                                <div className="text-[10px] font-medium text-[var(--accent)] mb-1.5 uppercase tracking-wider">
                                  {voiceLabel}
                                </div>
                              )}
                              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                                {voiceFiles.map((af: AudioFile, i: number) => {
                                  const audioUrl = `/outputs/${audioSessionId}/${af.file_name}`;
                                  const isPlaying = playingAudio === audioUrl;
                                  return (
                                    <div
                                      key={i}
                                      className="flex items-center gap-2.5 p-3 rounded-xl bg-[var(--input-bg)] hover:bg-[var(--accent-subtle)]/30 transition-colors"
                                    >
                                      <button
                                        onClick={() => toggleAudio(audioUrl)}
                                        className={`p-2 rounded-lg transition-colors ${
                                          isPlaying
                                            ? "bg-[var(--accent)] text-white"
                                            : "bg-[var(--card)] text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                                        }`}
                                      >
                                        {isPlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
                                      </button>
                                      <div className="flex-1 min-w-0">
                                        <p className="text-[11px] font-medium text-[var(--text-primary)] truncate">
                                          {af.type}
                                        </p>
                                        {af.file_size_bytes && (
                                          <p className="text-[10px] text-[var(--text-tertiary)]">
                                            {(af.file_size_bytes / 1024).toFixed(0)} KB
                                          </p>
                                        )}
                                      </div>
                                      <a
                                        href={audioUrl}
                                        download
                                        className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--card)] transition-colors"
                                      >
                                        <Download className="w-3 h-3" />
                                      </a>
                                    </div>
                                  );
                                })}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  );
                })}
              </div>
            );
          })()}

          {/* Save campaign */}
          {result && !error && (
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
              {saved ? (
                <div className="flex items-center gap-2 text-[var(--success)] text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  Campaign saved! View it on the{" "}
                  <a
                    href="/dashboard"
                    className="underline hover:opacity-80"
                  >
                    Dashboard
                  </a>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <input
                    type="text"
                    placeholder="Campaign name..."
                    className="flex-1 px-4 py-2.5 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 transition-colors"
                    value={campaignName}
                    onChange={(e) => setCampaignName(e.target.value)}
                  />
                  <button
                    onClick={handleSaveCampaign}
                    disabled={!campaignName.trim() || saving}
                    className="px-5 py-2.5 rounded-xl bg-[var(--accent)] text-white text-sm font-medium hover:opacity-90 transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Save className="w-3.5 h-3.5" />
                    {saving ? "Saving..." : "Save"}
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Reset */}
          <div className="text-center">
            <button
              onClick={handleReset}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] transition-colors"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              Start New Campaign
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
