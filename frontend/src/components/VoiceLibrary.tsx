"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Search, Play, Pause, Check, X, Loader2, Mic, Volume2, Plus, Save, Trash2, AlertCircle, ChevronDown } from "lucide-react";
import { useVoice, type SelectedVoice } from "./VoiceContext";

interface VoiceData {
  voice_id: string;
  name: string;
  description: string;
  labels: { accent?: string; gender?: string; age?: string };
  category: string;
  preview_url: string | null;
  best_for_regions: string[];
}

// Verified ElevenLabs preview URLs (from public /v1/voices API, no key needed)
// Fallback for when the backend returns curated voices without preview_url
const CURATED_PREVIEW_URLS: Record<string, string> = {
  CwhRBWXzGAHq8TQ4Fs17: "https://storage.googleapis.com/eleven-public-prod/premade/voices/CwhRBWXzGAHq8TQ4Fs17/58ee3ff5-f6f2-4628-93b8-e38eb31806b0.mp3",
  EXAVITQu4vr4xnSDxMaL: "https://storage.googleapis.com/eleven-public-prod/premade/voices/EXAVITQu4vr4xnSDxMaL/01a3e33c-6e99-4ee7-8543-ff2216a32186.mp3",
  FGY2WhTYpPnrIDTdsKH5: "https://storage.googleapis.com/eleven-public-prod/premade/voices/FGY2WhTYpPnrIDTdsKH5/67341759-ad08-41a5-be6e-de12fe448618.mp3",
  IKne3meq5aSn9XLyUdCD: "https://storage.googleapis.com/eleven-public-prod/premade/voices/IKne3meq5aSn9XLyUdCD/102de6f2-22ed-43e0-a1f1-111fa75c5481.mp3",
  JBFqnCBsd6RMkjVDRZzb: "https://storage.googleapis.com/eleven-public-prod/premade/voices/JBFqnCBsd6RMkjVDRZzb/e6206d1a-0721-4787-aafb-06a6e705cac5.mp3",
  N2lVS1w4EtoT3dr4eOWO: "https://storage.googleapis.com/eleven-public-prod/premade/voices/N2lVS1w4EtoT3dr4eOWO/ac833bd8-ffda-4938-9ebc-b0f99ca25481.mp3",
  SAz9YHcvj6GT2YYXdXww: "https://storage.googleapis.com/eleven-public-prod/premade/voices/SAz9YHcvj6GT2YYXdXww/e6c95f0b-2227-491a-b3d7-2249240decb7.mp3",
  SOYHLrjzK2X1ezoPC6cr: "https://storage.googleapis.com/eleven-public-prod/premade/voices/SOYHLrjzK2X1ezoPC6cr/86d178f6-f4b6-4e0e-85be-3de19f490794.mp3",
  TX3LPaxmHKxFdv7VOQHJ: "https://storage.googleapis.com/eleven-public-prod/premade/voices/TX3LPaxmHKxFdv7VOQHJ/63148076-6363-42db-aea8-31424308b92c.mp3",
  Xb7hH8MSUJpSbSDYk0k2: "https://storage.googleapis.com/eleven-public-prod/premade/voices/Xb7hH8MSUJpSbSDYk0k2/d10f7534-11f6-41fe-a012-2de1e482d336.mp3",
  XrExE9yKIg1WjnnlVkGX: "https://storage.googleapis.com/eleven-public-prod/premade/voices/XrExE9yKIg1WjnnlVkGX/b930e18d-6b4d-466e-bab2-0ae97c6d8535.mp3",
  bIHbv24MWmeRgasZH58o: "https://storage.googleapis.com/eleven-public-prod/premade/voices/bIHbv24MWmeRgasZH58o/8caf8f3d-ad29-4980-af41-53f20c72d7a4.mp3",
  cgSgspJ2msm6clMCkdW9: "https://storage.googleapis.com/eleven-public-prod/premade/voices/cgSgspJ2msm6clMCkdW9/56a97bf8-b69b-448f-846c-c3a11683d45a.mp3",
  cjVigY5qzO86Huf0OWal: "https://storage.googleapis.com/eleven-public-prod/premade/voices/cjVigY5qzO86Huf0OWal/d098fda0-6456-4030-b3d8-63aa048c9070.mp3",
  hpp4J3VqNfWAUOO0d1Us: "https://storage.googleapis.com/eleven-public-prod/premade/voices/hpp4J3VqNfWAUOO0d1Us/dab0f5ba-3aa4-48a8-9fad-f138fea1126d.mp3",
  iP95p4xoKVk53GoZ742B: "https://storage.googleapis.com/eleven-public-prod/premade/voices/iP95p4xoKVk53GoZ742B/3f4bde72-cc48-40dd-829f-57fbf906f4d7.mp3",
  nPczCjzI2devNBz1zQrb: "https://storage.googleapis.com/eleven-public-prod/premade/voices/nPczCjzI2devNBz1zQrb/2dd3e72c-4fd3-42f1-93ea-abc5d4e5aa1d.mp3",
  onwK4e9ZLuTAKqWW03F9: "https://storage.googleapis.com/eleven-public-prod/premade/voices/onwK4e9ZLuTAKqWW03F9/7eee0236-1a72-4b86-b303-5dcadc007ba9.mp3",
  pFZP5JQG7iQjIQuC4Bku: "https://storage.googleapis.com/eleven-public-prod/premade/voices/pFZP5JQG7iQjIQuC4Bku/89b68b35-b3dd-4348-a84a-a3c13a3c2b30.mp3",
  pNInz6obpgDQGcFmaJgB: "https://storage.googleapis.com/eleven-public-prod/premade/voices/pNInz6obpgDQGcFmaJgB/d6905d7a-dd26-4187-bfff-1bd3a5ea7cac.mp3",
  pqHfZKP75CvOlQylNhV4: "https://storage.googleapis.com/eleven-public-prod/premade/voices/pqHfZKP75CvOlQylNhV4/d782b3ff-84ba-4029-848c-acf01285524d.mp3",
};

export default function VoiceLibrary() {
  const { selectedVoice, setSelectedVoice } = useVoice();
  const [voices, setVoices] = useState<VoiceData[]>([]);
  const [source, setSource] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [genderFilter, setGenderFilter] = useState<string>("All");
  const [accentFilter, setAccentFilter] = useState<string>("All");
  const [playingId, setPlayingId] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  // Custom voice state
  const [showAddVoice, setShowAddVoice] = useState(false);
  const [customVoiceId, setCustomVoiceId] = useState("");
  const [customName, setCustomName] = useState("");
  const [customGender, setCustomGender] = useState("");
  const [customAccent, setCustomAccent] = useState("");
  const [customDesc, setCustomDesc] = useState("");
  const [testingVoice, setTestingVoice] = useState(false);
  const [testAudioUrl, setTestAudioUrl] = useState<string | null>(null);
  const [testError, setTestError] = useState("");
  const [savingVoice, setSavingVoice] = useState(false);
  const [testPassed, setTestPassed] = useState(false);
  const [testAudioB64, setTestAudioB64] = useState<string | null>(null);

  // Fetch voices and enrich with fallback preview URLs
  useEffect(() => {
    fetch("/api/voices")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Failed"))))
      .then((data: { voices: VoiceData[]; source: string; total: number }) => {
        const enriched = data.voices.map((v) => ({
          ...v,
          preview_url: v.preview_url || CURATED_PREVIEW_URLS[v.voice_id] || null,
        }));
        setVoices(enriched);
        setSource(data.source);
      })
      .catch(() => setVoices([]))
      .finally(() => setLoading(false));
  }, []);

  // Play/stop preview
  const togglePreview = useCallback((voice: VoiceData) => {
    if (playingId === voice.voice_id) {
      audioRef.current?.pause();
      audioRef.current = null;
      setPlayingId(null);
      return;
    }
    audioRef.current?.pause();
    if (!voice.preview_url) return;
    const audio = new Audio(voice.preview_url);
    audio.onended = () => { setPlayingId(null); audioRef.current = null; };
    audio.onerror = () => { setPlayingId(null); audioRef.current = null; };
    audioRef.current = audio;
    setPlayingId(voice.voice_id);
    audio.play().catch(() => { setPlayingId(null); audioRef.current = null; });
  }, [playingId]);

  useEffect(() => {
    return () => { audioRef.current?.pause(); };
  }, []);

  // Filter
  const filtered = voices.filter((v) => {
    const q = search.toLowerCase();
    const matchesSearch = !q
      || v.name.toLowerCase().includes(q)
      || v.description.toLowerCase().includes(q)
      || (v.labels.accent || "").toLowerCase().includes(q)
      || v.best_for_regions.some((r) => r.replace(/_/g, " ").includes(q));
    const matchesGender = genderFilter === "All" || (v.labels.gender || "").toLowerCase() === genderFilter.toLowerCase();
    const matchesAccent = accentFilter === "All" || (v.labels.accent || "").toLowerCase() === accentFilter.toLowerCase();
    return matchesSearch && matchesGender && matchesAccent;
  });

  const selectVoice = useCallback((voice: VoiceData) => {
    const sv: SelectedVoice = {
      voice_id: voice.voice_id,
      name: voice.name,
      description: voice.description,
      labels: voice.labels,
      preview_url: voice.preview_url,
      best_for_regions: voice.best_for_regions,
    };
    setSelectedVoice(sv);
  }, [setSelectedVoice]);

  // Test a custom voice ID
  const testCustomVoice = useCallback(async () => {
    if (!customVoiceId.trim()) return;
    setTestingVoice(true);
    setTestError("");
    setTestAudioUrl(null);
    setTestPassed(false);
    setTestAudioB64(null);
    try {
      const res = await fetch("/api/voices/test", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ voice_id: customVoiceId.trim() }),
      });
      const data = await res.json();
      if (!res.ok) {
        setTestError(data.error || "Test failed");
        return;
      }
      const url = `data:audio/mpeg;base64,${data.audio_base64}`;
      setTestAudioUrl(url);
      setTestAudioB64(data.audio_base64);
      setTestPassed(true);
      // Auto-play the test
      const audio = new Audio(url);
      audioRef.current?.pause();
      audioRef.current = audio;
      audio.onended = () => { audioRef.current = null; };
      audio.play().catch(() => {});
    } catch {
      setTestError("Network error — check your connection");
    } finally {
      setTestingVoice(false);
    }
  }, [customVoiceId]);

  // Save a tested custom voice permanently
  const saveCustomVoice = useCallback(async () => {
    if (!customVoiceId.trim() || !customName.trim()) return;
    setSavingVoice(true);
    try {
      const res = await fetch("/api/voices/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          voice_id: customVoiceId.trim(),
          name: customName.trim(),
          description: customDesc.trim(),
          gender: customGender,
          accent: customAccent,
          audio_base64: testAudioB64,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        setTestError(data.error || "Save failed");
        return;
      }
      // Refresh voice list
      const listRes = await fetch("/api/voices");
      if (listRes.ok) {
        const listData = await listRes.json();
        const enriched = listData.voices.map((v: VoiceData) => ({
          ...v,
          preview_url: v.preview_url || CURATED_PREVIEW_URLS[v.voice_id] || null,
        }));
        setVoices(enriched);
        setSource(listData.source);
      }
      // Reset form
      setCustomVoiceId("");
      setCustomName("");
      setCustomGender("");
      setCustomAccent("");
      setCustomDesc("");
      setTestAudioUrl(null);
      setTestAudioB64(null);
      setTestPassed(false);
      setShowAddVoice(false);
    } catch {
      setTestError("Network error");
    } finally {
      setSavingVoice(false);
    }
  }, [customVoiceId, customName, customDesc, customGender, customAccent, testAudioB64]);

  // Delete a custom voice
  const deleteCustomVoice = useCallback(async (voiceId: string) => {
    try {
      await fetch(`/api/voices/${voiceId}`, { method: "DELETE" });
      setVoices((prev) => prev.filter((v) => v.voice_id !== voiceId));
      _voices_cache_bust();
    } catch { /* ignore */ }
  }, []);
  const _voices_cache_bust = () => {
    // Force re-fetch on next load
    fetch("/api/voices").then(r => r.json()).then(data => {
      const enriched = data.voices.map((v: VoiceData) => ({
        ...v,
        preview_url: v.preview_url || CURATED_PREVIEW_URLS[v.voice_id] || null,
      }));
      setVoices(enriched);
    }).catch(() => {});
  };

  const FilterPill = ({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) => (
    <button
      onClick={onClick}
      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all whitespace-nowrap ${
        active
          ? "bg-[var(--accent)] text-white shadow-sm"
          : "text-[var(--text-secondary)] hover:text-[var(--accent)] hover:bg-[var(--accent-subtle)]"
      }`}
    >
      {label}
    </button>
  );

  return (
    <div className="min-h-screen bg-[var(--background)] p-6 pb-20">
      <div className="max-w-5xl mx-auto space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-[var(--accent-subtle)]">
              <Mic className="w-5 h-5 text-[var(--accent)]" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-[var(--text-primary)]">Voice Library</h1>
              <p className="text-xs text-[var(--text-tertiary)]">
                Preview and select voices for your campaigns
              </p>
            </div>
          </div>
          {source && (
            <span className="text-[10px] px-2.5 py-1 rounded-full bg-[var(--accent-subtle)] text-[var(--accent)] font-medium">
              {source === "api" ? "ElevenLabs API" : "Curated"} &middot; {voices.length} voices
            </span>
          )}
        </div>

        {/* Search + Filters — stacked clean layout */}
        <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-4 space-y-3">
          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search voices..."
              className="w-full pl-10 pr-4 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50"
            />
          </div>
          {/* Filter rows */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider font-medium">Gender</span>
              {(["All", "Female", "Male"] as const).map((g) => (
                <FilterPill key={g} label={g} active={genderFilter === g} onClick={() => setGenderFilter(g)} />
              ))}
            </div>
            <div className="w-px h-5 bg-[var(--card-border)] hidden sm:block" />
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[10px] text-[var(--text-tertiary)] uppercase tracking-wider font-medium">Accent</span>
              {["All", ...Array.from(new Set(voices.map((v) => v.labels.accent).filter(Boolean))).sort()].map((a) => (
                <FilterPill key={a!} label={a!} active={accentFilter === a} onClick={() => setAccentFilter(a!)} />
              ))}
            </div>
          </div>
        </div>

        {/* Add Custom Voice */}
        <div className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] overflow-hidden">
          <button
            onClick={() => setShowAddVoice(!showAddVoice)}
            className="w-full flex items-center justify-between p-4 hover:bg-[var(--input-bg)] transition-colors"
          >
            <div className="flex items-center gap-2">
              <Plus className="w-4 h-4 text-[var(--accent)]" />
              <span className="text-sm font-semibold text-[var(--text-primary)]">Add Custom Voice</span>
              <span className="text-[10px] text-[var(--text-tertiary)]">Paste any voice ID from elevenlabs.io</span>
            </div>
            <ChevronDown className={`w-4 h-4 text-[var(--text-tertiary)] transition-transform ${showAddVoice ? "rotate-180" : ""}`} />
          </button>

          {showAddVoice && (
            <div className="p-4 pt-0 space-y-3 border-t border-[var(--card-border)]">
              {/* Voice ID + Test */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={customVoiceId}
                  onChange={(e) => { setCustomVoiceId(e.target.value); setTestPassed(false); setTestError(""); setTestAudioUrl(null); setTestAudioB64(null); }}
                  placeholder="Paste ElevenLabs Voice ID (e.g., 1Z7Y8o9cvUeWq8oLKgMY)"
                  className="flex-1 px-3 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 font-mono"
                />
                <button
                  onClick={testCustomVoice}
                  disabled={!customVoiceId.trim() || testingVoice}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-[var(--accent)] text-white disabled:opacity-40 hover:opacity-90 transition-all flex items-center gap-1.5 whitespace-nowrap"
                >
                  {testingVoice ? <Loader2 className="w-3 h-3 animate-spin" /> : <Play className="w-3 h-3" />}
                  Test Voice
                </button>
              </div>

              {/* Test result */}
              {testError && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-red-500/10 border border-red-500/20">
                  <AlertCircle className="w-3.5 h-3.5 text-red-400 shrink-0" />
                  <span className="text-xs text-red-400">{testError}</span>
                </div>
              )}
              {testPassed && (
                <div className="flex items-center gap-2 p-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20">
                  <Check className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                  <span className="text-xs text-emerald-400">Voice works! Fill in details below to save it permanently.</span>
                  {testAudioUrl && (
                    <button
                      onClick={() => { const a = new Audio(testAudioUrl); a.play().catch(() => {}); }}
                      className="ml-auto text-[10px] text-emerald-400 hover:text-emerald-300 font-medium flex items-center gap-1"
                    >
                      <Volume2 className="w-3 h-3" /> Replay
                    </button>
                  )}
                </div>
              )}

              {/* Save form (only after test passes) */}
              {testPassed && (
                <div className="space-y-2 pt-1">
                  <input
                    type="text"
                    value={customName}
                    onChange={(e) => setCustomName(e.target.value)}
                    placeholder="Voice name (e.g., Priya, Amara) *"
                    className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50"
                  />
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={customGender}
                      onChange={(e) => setCustomGender(e.target.value)}
                      className="px-3 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]/50"
                    >
                      <option value="">Gender</option>
                      <option value="female">Female</option>
                      <option value="male">Male</option>
                      <option value="neutral">Neutral</option>
                    </select>
                    <input
                      type="text"
                      value={customAccent}
                      onChange={(e) => setCustomAccent(e.target.value)}
                      placeholder="Accent (e.g., Indian, British)"
                      className="px-3 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50"
                    />
                  </div>
                  <input
                    type="text"
                    value={customDesc}
                    onChange={(e) => setCustomDesc(e.target.value)}
                    placeholder="Short description (optional)"
                    className="w-full px-3 py-2 text-sm rounded-xl bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50"
                  />
                  <button
                    onClick={saveCustomVoice}
                    disabled={!customName.trim() || savingVoice}
                    className="w-full py-2.5 rounded-xl text-xs font-semibold bg-emerald-500 text-white disabled:opacity-40 hover:bg-emerald-600 transition-all flex items-center justify-center gap-1.5"
                  >
                    {savingVoice ? <Loader2 className="w-3 h-3 animate-spin" /> : <Save className="w-3 h-3" />}
                    Save to Voice Library
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Voice Grid */}
        {loading ? (
          <div className="flex justify-center py-20">
            <Loader2 className="w-6 h-6 animate-spin text-[var(--accent)]" />
          </div>
        ) : filtered.length === 0 ? (
          <div className="text-center py-20">
            <p className="text-sm text-[var(--text-tertiary)]">No voices match your filters</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {filtered.map((voice) => {
              const isSelected = selectedVoice?.voice_id === voice.voice_id;
              const isPlaying = playingId === voice.voice_id;
              const hasPreview = !!voice.preview_url;
              return (
                <div
                  key={voice.voice_id}
                  className={`group rounded-2xl border p-4 transition-all ${
                    isSelected
                      ? "border-[var(--accent)] bg-[var(--accent-subtle)] shadow-md"
                      : "border-[var(--card-border)] bg-[var(--card)] hover:border-[var(--accent)]/30 hover:shadow-sm"
                  }`}
                >
                  {/* Top: Name + Play */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex items-center gap-2 min-w-0">
                      <h3 className="text-sm font-bold text-[var(--text-primary)] truncate">{voice.name}</h3>
                      {isSelected && <Check className="w-3.5 h-3.5 text-[var(--accent)] shrink-0" />}
                    </div>
                    <button
                      onClick={() => togglePreview(voice)}
                      disabled={!hasPreview}
                      className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 transition-all ${
                        isPlaying
                          ? "bg-[var(--accent)] text-white shadow-lg scale-105"
                          : hasPreview
                            ? "bg-[var(--input-bg)] text-[var(--text-tertiary)] hover:text-[var(--accent)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)]"
                            : "bg-[var(--input-bg)] text-[var(--text-tertiary)] opacity-30 cursor-not-allowed"
                      }`}
                      title={hasPreview ? (isPlaying ? "Stop" : "Preview") : "No preview available"}
                    >
                      {isPlaying ? <Volume2 className="w-3.5 h-3.5 animate-pulse" /> : <Play className="w-3.5 h-3.5 ml-0.5" />}
                    </button>
                  </div>

                  {/* Tags */}
                  <div className="flex flex-wrap gap-1 mb-2">
                    {voice.labels.gender && (
                      <span className={`px-1.5 py-0.5 rounded text-[9px] font-semibold ${
                        voice.labels.gender === "female"
                          ? "bg-pink-500/10 text-pink-500"
                          : "bg-blue-500/10 text-blue-500"
                      }`}>
                        {voice.labels.gender}
                      </span>
                    )}
                    {voice.labels.accent && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] font-medium bg-[var(--input-bg)] text-[var(--text-secondary)]">
                        {voice.labels.accent}
                      </span>
                    )}
                    {voice.labels.age && (
                      <span className="px-1.5 py-0.5 rounded text-[9px] text-[var(--text-tertiary)]">
                        {voice.labels.age}
                      </span>
                    )}
                  </div>

                  {/* Description */}
                  <p className="text-[11px] text-[var(--text-tertiary)] leading-relaxed line-clamp-2 mb-2.5">
                    {voice.description || "No description available"}
                  </p>

                  {/* Region tags */}
                  {voice.best_for_regions.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                      {voice.best_for_regions.map((r) => (
                        <span key={r} className="px-1.5 py-0.5 rounded text-[8px] font-medium bg-emerald-500/8 text-emerald-500 capitalize">
                          {r.replace(/_/g, " ")}
                        </span>
                      ))}
                    </div>
                  )}

                  {/* Select + Delete buttons */}
                  <div className="flex gap-1.5">
                    <button
                      onClick={() => isSelected ? setSelectedVoice(null) : selectVoice(voice)}
                      className={`flex-1 py-2 rounded-xl text-[11px] font-semibold transition-all ${
                        isSelected
                          ? "bg-[var(--accent)] text-white"
                          : "bg-[var(--input-bg)] text-[var(--text-secondary)] border border-[var(--card-border)] hover:border-[var(--accent)] hover:text-[var(--accent)]"
                      }`}
                    >
                      {isSelected ? "Selected \u2713" : "Use This Voice"}
                    </button>
                    {voice.category === "custom" && (
                      <button
                        onClick={() => deleteCustomVoice(voice.voice_id)}
                        className="px-2.5 py-2 rounded-xl text-[11px] bg-[var(--input-bg)] text-red-400 border border-[var(--card-border)] hover:border-red-500/30 hover:bg-red-500/10 transition-all"
                        title="Remove from library"
                      >
                        <Trash2 className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* Sticky bottom bar */}
        {selectedVoice && (
          <div className="fixed bottom-0 left-0 right-0 z-50 bg-[var(--card)]/95 backdrop-blur-xl border-t border-[var(--card-border)] px-6 py-3">
            <div className="max-w-5xl mx-auto flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-[var(--accent)] text-white flex items-center justify-center">
                  <Check className="w-4 h-4" />
                </div>
                <div>
                  <span className="text-sm font-semibold text-[var(--text-primary)]">{selectedVoice.name}</span>
                  <span className="text-xs text-[var(--text-tertiary)] ml-2">
                    {selectedVoice.labels?.accent} &middot; {selectedVoice.labels?.gender}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedVoice(null)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium text-red-400 hover:bg-red-500/10 border border-red-500/20 transition-colors"
              >
                <X className="w-3 h-3" />
                Clear Selection
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
