"use client";

import { useState, useEffect } from "react";
import { Search, Loader2, Globe, Radio, ChevronDown } from "lucide-react";
import type { Campaign, CampaignDetail, AudioFile } from "@/lib/types";

interface CampaignSelectorProps {
  onCampaignReady: (detail: CampaignDetail, variantId: number) => void;
  disabled: boolean;
  currentNodeId?: string;
  initialCampaignId?: string;
}

export default function CampaignSelector({ onCampaignReady, disabled, currentNodeId, initialCampaignId }: CampaignSelectorProps) {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CampaignDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [selectedVariant, setSelectedVariant] = useState<number>(1);

  // Fetch campaigns with audio
  useEffect(() => {
    fetch("/api/campaigns")
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Failed"))))
      .then((data: { campaigns?: Campaign[] }) => {
        const withAudio = (data.campaigns || []).filter((c) => c.has_audio);
        setCampaigns(withAudio);
        // Auto-select from deep-link
        if (initialCampaignId && withAudio.some((c) => c.id === initialCampaignId)) {
          setSelectedId(initialCampaignId);
        }
      })
      .catch(() => setCampaigns([]))
      .finally(() => setLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Fetch detail when campaign selected
  useEffect(() => {
    if (!selectedId) { setDetail(null); return; }
    setDetailLoading(true);
    fetch(`/api/campaigns/${selectedId}`)
      .then((r) => (r.ok ? r.json() : Promise.reject(new Error("Failed"))))
      .then((d: CampaignDetail) => {
        setDetail(d);
        // Auto-select first variant
        const audioFiles: AudioFile[] = d.result?.audio?.audio_files || [];
        const variants = [...new Set(audioFiles.map((af) => af.variant_id))].sort();
        const first = variants[0] ?? 1;
        setSelectedVariant(first);
        onCampaignReady(d, first);
      })
      .catch(() => setDetail(null))
      .finally(() => setDetailLoading(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId]);

  // Notify parent when variant changes
  useEffect(() => {
    if (detail) onCampaignReady(detail, selectedVariant);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVariant]);

  const filtered = campaigns.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.country.toLowerCase().includes(search.toLowerCase()) ||
    c.telco.toLowerCase().includes(search.toLowerCase())
  );

  const audioFiles: AudioFile[] = detail?.result?.audio?.audio_files || [];
  const variants = [...new Set(audioFiles.filter((af) => !af.error).map((af) => af.variant_id))].sort();
  const scripts = detail?.result?.final_scripts?.scripts
    || detail?.result?.revised_scripts_round_1?.scripts
    || detail?.result?.initial_scripts?.scripts
    || [];

  return (
    <div className="flex flex-col gap-3 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] p-4 overflow-hidden">
      <h3 className="text-sm font-semibold text-[var(--text-primary)]">Select Campaign</h3>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[var(--text-tertiary)]" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search campaigns..."
          className="w-full pl-8 pr-3 py-2 text-xs rounded-lg bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] placeholder:text-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50"
        />
      </div>

      {/* Campaign list */}
      <div className="flex flex-col gap-1.5 max-h-[240px] overflow-y-auto">
        {loading ? (
          <div className="flex justify-center py-6">
            <Loader2 className="w-4 h-4 animate-spin text-[var(--accent)]" />
          </div>
        ) : filtered.length === 0 ? (
          <p className="text-[10px] text-[var(--text-tertiary)] text-center py-4">
            {campaigns.length === 0 ? "No campaigns with audio found" : "No matches"}
          </p>
        ) : (
          filtered.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedId(c.id)}
              disabled={disabled}
              className={`
                text-left p-2.5 rounded-xl border transition-all
                ${selectedId === c.id
                  ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                  : "border-[var(--card-border)] bg-[var(--input-bg)] hover:border-[var(--accent)]/30"
                }
                ${disabled ? "opacity-50 cursor-not-allowed" : ""}
              `}
            >
              <p className="text-xs font-semibold text-[var(--text-primary)] truncate">{c.name}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                  <Globe className="w-2.5 h-2.5" /> {c.country}
                </span>
                <span className="flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                  <Radio className="w-2.5 h-2.5" /> {c.telco}
                </span>
              </div>
            </button>
          ))
        )}
      </div>

      {/* Variant selector */}
      {detail && variants.length > 0 && (
        <div className="border-t border-[var(--card-border)] pt-3 space-y-2">
          <label className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-medium">
            Variant
          </label>
          <div className="relative">
            <select
              value={selectedVariant}
              onChange={(e) => setSelectedVariant(Number(e.target.value))}
              disabled={disabled}
              className="w-full appearance-none pl-3 pr-8 py-2 text-xs rounded-lg bg-[var(--input-bg)] border border-[var(--card-border)] text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)]/50"
            >
              {variants.map((vid) => {
                const script = scripts.find((s) => s.variant_id === vid);
                return (
                  <option key={vid} value={vid}>
                    V{vid}{script?.theme ? ` — ${script.theme}` : ""}
                  </option>
                );
              })}
            </select>
            <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-3 h-3 text-[var(--text-tertiary)] pointer-events-none" />
          </div>

          {/* Audio segments info */}
          {(() => {
            const variantAudio = audioFiles.filter((af) => af.variant_id === selectedVariant && !af.error);
            return (
              <div className="space-y-1">
                <p className="text-[10px] text-[var(--text-tertiary)]">
                  {variantAudio.length} audio segment{variantAudio.length !== 1 ? "s" : ""}
                </p>
                <div className="flex flex-wrap gap-1">
                  {variantAudio.map((af, i) => {
                    const segId = af.type.replace("step_", "");
                    const isActive = currentNodeId != null && (segId === currentNodeId || af.type === currentNodeId);
                    return (
                      <span
                        key={i}
                        className={`px-1.5 py-0.5 rounded text-[9px] font-medium flex items-center gap-1 transition-colors ${
                          isActive
                            ? "bg-[var(--accent)] text-white"
                            : "bg-[var(--accent-subtle)] text-[var(--accent)]"
                        }`}
                      >
                        {isActive && <span className="w-1.5 h-1.5 rounded-full bg-white animate-pulse" />}
                        {segId.replace(/^\w/, (c) => c.toUpperCase())}
                      </span>
                    );
                  })}
                </div>
              </div>
            );
          })()}
        </div>
      )}

      {detailLoading && (
        <div className="flex items-center gap-2 text-[10px] text-[var(--text-tertiary)]">
          <Loader2 className="w-3 h-3 animate-spin" /> Loading campaign...
        </div>
      )}
    </div>
  );
}
