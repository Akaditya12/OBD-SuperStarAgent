"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  AudioLines,
  Upload,
  Play,
  Pause,
  Download,
  Loader2,
  CheckCircle2,
  ArrowRight,
  ArrowLeft,
  Music,
  Mic2,
  RefreshCw,
  AlertCircle,
} from "lucide-react";
import CountryTelcoSelect from "@/components/CountryTelcoSelect";

type Step = "input" | "previews" | "result";

interface VoicePreview {
  variant_id: number;
  voice_index: number;
  voice_name?: string;
  voice_label?: string;
  voice_id?: string;
  url?: string;
  public_url?: string;
  file_path?: string;
  error?: string;
}

const BGM_STYLES = [
  { id: "none", label: "No BGM" },
  { id: "upbeat", label: "Upbeat" },
  { id: "calm", label: "Calm" },
  { id: "corporate", label: "Corporate" },
  { id: "custom", label: "Upload BGM" },
];

const TTS_ENGINES = [
  { id: "auto", label: "Auto (Best Available)" },
  { id: "elevenlabs", label: "ElevenLabs" },
  { id: "murf", label: "Murf AI" },
  { id: "edge-tts", label: "Edge TTS (Free)" },
];

export default function ScriptToVoicePage() {
  const router = useRouter();

  const [authChecked, setAuthChecked] = useState(false);
  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((d) => { if (d.authenticated) setAuthChecked(true); else router.push("/login"); })
      .catch(() => setAuthChecked(true));
  }, [router]);

  const [step, setStep] = useState<Step>("input");

  // Input state
  const [scriptText, setScriptText] = useState("");
  const [country, setCountry] = useState("");
  const [telco, setTelco] = useState("");
  const [language, setLanguage] = useState("");
  const [ttsEngine, setTtsEngine] = useState("auto");
  const [bgmStyle, setBgmStyle] = useState("upbeat");
  const [audioFormat, setAudioFormat] = useState<"mp3" | "wav">("mp3");
  const [bgmId, setBgmId] = useState<string | null>(null);
  const [bgmFileName, setBgmFileName] = useState<string>("");
  const [uploadingBgm, setUploadingBgm] = useState(false);

  // Preview state
  const [previewing, setPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [previews, setPreviews] = useState<VoicePreview[]>([]);
  const [sessionId, setSessionId] = useState("");
  const [selectedVoice, setSelectedVoice] = useState<number>(0);
  const [activeTtsEngine, setActiveTtsEngine] = useState<string>("");

  // Final audio state
  const [generating, setGenerating] = useState(false);
  const [generateError, setGenerateError] = useState("");
  const [finalAudio, setFinalAudio] = useState<{
    url: string;
    public_url?: string;
    voice_name: string;
    duration?: number;
  } | null>(null);

  // Audio playback
  const [playingId, setPlayingId] = useState<string | null>(null);
  const [loadingId, setLoadingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const text = ev.target?.result as string;
      if (text) setScriptText(text);
    };
    reader.readAsText(file);
  };

  const handleBgmUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingBgm(true);
    try {
      const formData = new FormData();
      formData.append("bgm_file", file);
      const res = await fetch("/api/script-to-voice/upload-bgm", {
        method: "POST",
        body: formData,
      });
      if (!res.ok) throw new Error("Upload failed");
      const data = await res.json();
      setBgmId(data.bgm_id);
      setBgmFileName(file.name);
      setBgmStyle("custom");
    } catch {
      setBgmId(null);
      setBgmFileName("");
    } finally {
      setUploadingBgm(false);
    }
  };

  const playAudio = (url: string, id: string) => {
    if (playingId === id) {
      audioRef.current?.pause();
      setPlayingId(null);
      return;
    }
    if (audioRef.current) {
      audioRef.current.pause();
    }
    setLoadingId(id);
    const audio = new Audio(url);
    audioRef.current = audio;
    audio.oncanplaythrough = () => {
      setLoadingId(null);
      setPlayingId(id);
      audio.play();
    };
    audio.onended = () => setPlayingId(null);
    audio.onerror = () => { setLoadingId(null); setPlayingId(null); };
    audio.load();
  };

  const pollJob = async (jobId: string, endpoint: string): Promise<Record<string, unknown>> => {
    for (let i = 0; i < 120; i++) {
      await new Promise((r) => setTimeout(r, 3000));
      const res = await fetch(endpoint);
      if (!res.ok) continue;
      const data = await res.json();
      if (data.status === "done") return data;
      if (data.status === "error") throw new Error(data.error || "Job failed");
    }
    throw new Error("Timed out waiting for audio generation");
  };

  const handlePreview = async () => {
    setPreviewing(true);
    setPreviewError("");
    setPreviews([]);

    try {
      const res = await fetch("/api/script-to-voice/preview", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          script_text: scriptText,
          country,
          language: language || undefined,
          tts_engine: ttsEngine === "auto" ? undefined : ttsEngine,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Preview request failed");
      }
      const { job_id, session_id } = await res.json();
      setSessionId(session_id);

      const result = await pollJob(job_id, `/api/script-to-voice/jobs/${job_id}`);
      const previewData = result.previews as Record<string, unknown>;
      const successful = (
        (previewData?.hook_previews as VoicePreview[])
        || (previewData?.successful_previews as VoicePreview[])
        || []
      );

      if (successful.length === 0) {
        throw new Error("No voice previews were generated. Try a different TTS engine.");
      }
      setPreviews(successful);
      setSelectedVoice(0);
      setActiveTtsEngine((previewData?.tts_engine as string) || "");
      setStep("previews");
    } catch (err: unknown) {
      setPreviewError(err instanceof Error ? err.message : "Preview failed");
    } finally {
      setPreviewing(false);
    }
  };

  const handleGenerate = async () => {
    setGenerating(true);
    setGenerateError("");
    setFinalAudio(null);

    try {
      const res = await fetch("/api/script-to-voice/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          script_text: scriptText,
          voice_choice: selectedVoice,
          country,
          language: language || undefined,
          bgm_style: bgmStyle,
          audio_format: audioFormat,
          tts_engine: ttsEngine === "auto" ? undefined : ttsEngine,
          bgm_id: bgmStyle === "custom" ? bgmId : undefined,
        }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.error || "Generation failed");
      }
      const { job_id } = await res.json();
      const result = await pollJob(job_id, `/api/script-to-voice/jobs/${job_id}`);
      const audioData = result.audio as Record<string, unknown>;
      const files = (audioData?.audio_files || []) as Record<string, unknown>[];
      if (files.length > 0) {
        const f = files[0];
        setFinalAudio({
          url: (f.public_url || f.url || `/api/audio/${sessionId}/${(f.path as string || "").split("/").pop()}`) as string,
          public_url: f.public_url as string | undefined,
          voice_name: (f.voice_name || f.voice_label || previews[selectedVoice]?.voice_label || previews[selectedVoice]?.voice_name || "Voice") as string,
        });
        setStep("result");
      } else {
        throw new Error("No audio files generated");
      }
    } catch (err: unknown) {
      setGenerateError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  const reset = () => {
    setStep("input");
    setPreviews([]);
    setFinalAudio(null);
    setSelectedVoice(0);
    setSessionId("");
    setPreviewError("");
    setGenerateError("");
    setActiveTtsEngine("");
    setBgmId(null);
    setBgmFileName("");
    if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
    setPlayingId(null);
  };

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--background)] py-8 px-4">
      <div className="max-w-3xl mx-auto space-y-8">

        {/* Header */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center gap-3 px-4 py-2 rounded-2xl bg-[var(--accent-subtle)]">
            <AudioLines className="w-5 h-5 text-[var(--accent)]" />
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Script to Voice</h1>
          </div>
          <p className="text-sm text-[var(--text-tertiary)]">
            Paste your script, pick a voice, and generate professional audio
          </p>
        </div>

        {/* Step indicators */}
        <div className="flex items-center justify-center gap-2">
          {(["input", "previews", "result"] as Step[]).map((s, i) => {
            const labels = ["Script & Settings", "Voice Preview", "Final Audio"];
            const isActive = s === step;
            const isDone = (step === "previews" && i === 0) || (step === "result" && i < 2);
            return (
              <div key={s} className="flex items-center gap-2">
                {i > 0 && <div className={`w-8 h-0.5 ${isDone ? "bg-[var(--accent)]" : "bg-[var(--card-border)]"}`} />}
                <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  isActive ? "bg-[var(--accent)] text-white" : isDone ? "bg-[var(--accent-subtle)] text-[var(--accent)]" : "bg-[var(--card)] text-[var(--text-tertiary)] border border-[var(--card-border)]"
                }`}>
                  {isDone ? <CheckCircle2 className="w-3 h-3" /> : <span className="w-4 text-center">{i + 1}</span>}
                  <span className="hidden sm:inline">{labels[i]}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* ── Step 1: Input ── */}
        {step === "input" && (
          <div className="space-y-6">
            {/* Script input */}
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 space-y-4">
              <h2 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <Mic2 className="w-4 h-4 text-[var(--accent)]" />
                Your Script
              </h2>
              <textarea
                value={scriptText}
                onChange={(e) => setScriptText(e.target.value)}
                rows={8}
                placeholder="Paste your script here... (or upload a .txt file below)"
                className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-4 py-3 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)]/30 resize-none"
              />
              <div className="flex items-center justify-between">
                <label className="flex items-center gap-2 px-3 py-2 rounded-lg text-xs text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--input-bg)] cursor-pointer transition-colors border border-[var(--card-border)]">
                  <Upload className="w-3.5 h-3.5" />
                  Upload .txt file
                  <input type="file" accept=".txt" onChange={handleFileUpload} className="hidden" />
                </label>
                <span className="text-xs text-[var(--text-tertiary)]">{scriptText.length} chars</span>
              </div>
            </div>

            {/* Country / Operator / Language */}
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 space-y-3">
              <CountryTelcoSelect
                country={country}
                telco={telco}
                language={language}
                onCountryChange={setCountry}
                onTelcoChange={setTelco}
                onLanguageChange={setLanguage}
              />
              {language && language.toLowerCase() !== "english" && (
                <p className="text-[10px] text-amber-500 bg-amber-500/10 px-3 py-1.5 rounded-lg">
                  Tip: Write your script in {language} for the best pronunciation. The voice engine will match the selected language.
                </p>
              )}
            </div>

            {/* TTS Engine + BGM + Format */}
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 space-y-5">
              <h2 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                <AudioLines className="w-4 h-4 text-[var(--accent)]" />
                Audio Settings
              </h2>

              {/* TTS Engine */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-[var(--text-secondary)]">Voice Engine</label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  {TTS_ENGINES.map((eng) => (
                    <button
                      key={eng.id}
                      onClick={() => setTtsEngine(eng.id)}
                      className={`px-3 py-2 rounded-xl text-xs font-medium border transition-all ${
                        ttsEngine === eng.id
                          ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                          : "border-[var(--card-border)] text-[var(--text-tertiary)] hover:border-[var(--card-border-hover)]"
                      }`}
                    >
                      {eng.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* BGM Style */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-[var(--text-secondary)] flex items-center gap-1.5">
                  <Music className="w-3.5 h-3.5" /> Background Music
                </label>
                <div className="flex flex-wrap gap-2">
                  {BGM_STYLES.filter((s) => s.id !== "custom").map((s) => (
                    <button
                      key={s.id}
                      onClick={() => setBgmStyle(s.id)}
                      className={`px-4 py-2 rounded-xl text-xs font-medium border transition-all ${
                        bgmStyle === s.id
                          ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                          : "border-[var(--card-border)] text-[var(--text-tertiary)] hover:border-[var(--card-border-hover)]"
                      }`}
                    >
                      {s.label}
                    </button>
                  ))}
                  <label
                    className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium border cursor-pointer transition-all ${
                      bgmStyle === "custom"
                        ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                        : "border-[var(--card-border)] text-[var(--text-tertiary)] hover:border-[var(--card-border-hover)]"
                    }`}
                  >
                    <Upload className="w-3 h-3" />
                    {uploadingBgm ? "Uploading..." : bgmFileName || "Upload BGM"}
                    <input
                      type="file"
                      accept=".mp3,.wav,.ogg,.m4a"
                      onChange={handleBgmUpload}
                      className="hidden"
                    />
                  </label>
                </div>
                {bgmStyle === "custom" && bgmFileName && (
                  <p className="text-[10px] text-[var(--text-tertiary)] flex items-center gap-1">
                    <CheckCircle2 className="w-3 h-3 text-[var(--success)]" />
                    Using: {bgmFileName}
                  </p>
                )}
              </div>

              {/* Audio Format */}
              <div className="space-y-2">
                <label className="text-xs font-medium text-[var(--text-secondary)]">Output Format</label>
                <div className="flex gap-2">
                  {(["mp3", "wav"] as const).map((fmt) => (
                    <button
                      key={fmt}
                      onClick={() => setAudioFormat(fmt)}
                      className={`px-4 py-2 rounded-xl text-xs font-medium border uppercase transition-all ${
                        audioFormat === fmt
                          ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]"
                          : "border-[var(--card-border)] text-[var(--text-tertiary)] hover:border-[var(--card-border-hover)]"
                      }`}
                    >
                      {fmt}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Error */}
            {previewError && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 text-red-500 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {previewError}
              </div>
            )}

            {/* Generate Previews Button */}
            <button
              onClick={handlePreview}
              disabled={!scriptText.trim() || previewing}
              className="w-full flex items-center justify-center gap-2 py-3.5 rounded-2xl text-sm font-semibold text-white bg-[var(--accent)] hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
              style={{ boxShadow: "0 4px 20px var(--accent-glow)" }}
            >
              {previewing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Generating 3 voice options...
                </>
              ) : (
                <>
                  Generate Voice Previews
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        )}

        {/* ── Step 2: Voice Previews ── */}
        {step === "previews" && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6 space-y-5">
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-semibold text-[var(--text-primary)] flex items-center gap-2">
                  <Mic2 className="w-4 h-4 text-[var(--accent)]" />
                  Choose Your Voice
                </h2>
                {activeTtsEngine && (
                  <span className="text-[10px] px-2.5 py-1 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] font-medium border border-[var(--accent)]/20">
                    {activeTtsEngine === "elevenlabs" ? "ElevenLabs" : activeTtsEngine === "murf" ? "Murf AI" : activeTtsEngine === "edge-tts" ? "Edge TTS" : activeTtsEngine}
                  </span>
                )}
              </div>
              <p className="text-xs text-[var(--text-tertiary)]">
                Listen to each voice and select the one you prefer for the final audio.
              </p>

              <div className="space-y-3">
                {previews.map((p, i) => {
                  const audioUrl = p.public_url || p.url || (p.file_path ? `/api/audio/${sessionId}/${p.file_path.split("/").pop()}` : "");
                  const id = `preview-${i}`;
                  const isSelected = selectedVoice === i;
                  return (
                    <div
                      key={i}
                      role="button"
                      tabIndex={0}
                      onClick={() => setSelectedVoice(i)}
                      onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") setSelectedVoice(i); }}
                      className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all text-left cursor-pointer ${
                        isSelected
                          ? "border-[var(--accent)] bg-[var(--accent-subtle)] shadow-sm"
                          : "border-[var(--card-border)] hover:border-[var(--card-border-hover)] hover:bg-[var(--card-hover)]"
                      }`}
                      style={isSelected ? { boxShadow: "0 2px 12px var(--accent-glow)" } : undefined}
                    >
                      <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center shrink-0 ${
                        isSelected ? "border-[var(--accent)] bg-[var(--accent)]" : "border-[var(--card-border)]"
                      }`}>
                        {isSelected && <div className="w-2 h-2 rounded-full bg-white" />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <p className={`text-sm font-semibold ${isSelected ? "text-[var(--accent)]" : "text-[var(--text-primary)]"}`}>
                          {p.voice_label || p.voice_name || `Voice ${i + 1}`}
                        </p>
                        <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5">
                          Voice option {i + 1}
                        </p>
                      </div>

                      <button
                        onClick={(e) => { e.stopPropagation(); playAudio(audioUrl, id); }}
                        disabled={!audioUrl}
                        className={`p-2.5 rounded-xl transition-all shrink-0 ${
                          playingId === id
                            ? "bg-[var(--accent)] text-white"
                            : "bg-[var(--input-bg)] text-[var(--text-tertiary)] hover:text-[var(--accent)] hover:bg-[var(--accent-subtle)]"
                        }`}
                      >
                        {loadingId === id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : playingId === id ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Script preview */}
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6">
              <h3 className="text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Script</h3>
              <p className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
                {scriptText}
              </p>
            </div>

            {/* Error */}
            {generateError && (
              <div className="flex items-center gap-2 p-3 rounded-xl bg-red-500/10 text-red-500 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                {generateError}
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-3">
              <button
                onClick={() => setStep("input")}
                className="flex items-center gap-2 px-5 py-3 rounded-2xl text-sm font-medium border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--card-hover)] transition-all"
              >
                <ArrowLeft className="w-4 h-4" />
                Back
              </button>
              <button
                onClick={handleGenerate}
                disabled={generating}
                className="flex-1 flex items-center justify-center gap-2 py-3 rounded-2xl text-sm font-semibold text-white bg-[var(--accent)] hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg"
                style={{ boxShadow: "0 4px 20px var(--accent-glow)" }}
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    Generating final audio...
                  </>
                ) : (
                  <>
                    Generate Final Audio
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* ── Step 3: Result ── */}
        {step === "result" && finalAudio && (
          <div className="space-y-6">
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-8 space-y-6">
              <div className="text-center space-y-2">
                <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[var(--success)]/10">
                  <CheckCircle2 className="w-7 h-7 text-[var(--success)]" />
                </div>
                <h2 className="text-lg font-bold text-[var(--text-primary)]">Audio Ready</h2>
                <p className="text-xs text-[var(--text-tertiary)]">
                  Voice: {finalAudio.voice_name} &middot; Format: {audioFormat.toUpperCase()} &middot; BGM: {bgmStyle === "none" ? "None" : bgmStyle}
                  {activeTtsEngine && (
                    <span className="ml-2 inline-flex px-2 py-0.5 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] text-[10px] font-medium">
                      {activeTtsEngine === "elevenlabs" ? "ElevenLabs" : activeTtsEngine === "murf" ? "Murf AI" : activeTtsEngine === "edge-tts" ? "Edge TTS" : activeTtsEngine}
                    </span>
                  )}
                </p>
              </div>

              {/* Audio player */}
              <div className="flex items-center gap-4 p-4 rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)]">
                <button
                  onClick={() => playAudio(finalAudio.public_url || finalAudio.url, "final")}
                  className={`p-3 rounded-xl transition-all ${
                    playingId === "final"
                      ? "bg-[var(--accent)] text-white"
                      : "bg-[var(--accent-subtle)] text-[var(--accent)] hover:bg-[var(--accent)] hover:text-white"
                  }`}
                >
                  {loadingId === "final" ? (
                    <Loader2 className="w-5 h-5 animate-spin" />
                  ) : playingId === "final" ? (
                    <Pause className="w-5 h-5" />
                  ) : (
                    <Play className="w-5 h-5" />
                  )}
                </button>
                <div className="flex-1">
                  <p className="text-sm font-semibold text-[var(--text-primary)]">Final Audio</p>
                  <p className="text-[10px] text-[var(--text-tertiary)]">{finalAudio.voice_name}</p>
                </div>
                <a
                  href={finalAudio.public_url || finalAudio.url}
                  download={`script-to-voice.${audioFormat}`}
                  className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold text-white bg-[var(--accent)] hover:brightness-110 transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  Download {audioFormat.toUpperCase()}
                </a>
              </div>
            </div>

            {/* Script used */}
            <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-6">
              <h3 className="text-xs font-semibold text-[var(--text-tertiary)] uppercase tracking-wider mb-3">Script Used</h3>
              <p className="text-xs text-[var(--text-secondary)] whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
                {scriptText}
              </p>
            </div>

            {/* Start over */}
            <button
              onClick={reset}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-2xl text-sm font-medium border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--card-hover)] transition-all"
            >
              <RefreshCw className="w-4 h-4" />
              Create Another
            </button>
          </div>
        )}

      </div>
    </div>
  );
}
