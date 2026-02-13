"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Zap,
  LayoutDashboard,
  ArrowLeft,
  Trash2,
  ChevronDown,
  ChevronUp,
  Globe,
  Radio,
  Calendar,
  User,
  FileText,
  Volume2,
  Loader2,
  FolderOpen,
} from "lucide-react";
import type {
  Campaign,
  CampaignDetail,
  PipelineResult,
  VoiceSelection,
} from "@/lib/types";
import ScriptReview from "@/components/ScriptReview";
import VoiceInfoPanel from "@/components/VoiceInfoPanel";
import AudioPlayer from "@/components/AudioPlayer";

export default function DashboardPage() {
  const router = useRouter();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CampaignDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Auth check
  useEffect(() => {
    fetch("/api/auth/me")
      .then((res) => res.json())
      .then((data) => {
        if (!data.authenticated) {
          router.push("/login");
        }
      })
      .catch(() => {
        // Local dev -- allow
      });
  }, [router]);

  // Load campaigns
  const loadCampaigns = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch("/api/campaigns");
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || []);
      }
    } catch {
      // Silently fail
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [loadCampaigns]);

  // Expand/collapse a campaign
  const toggleExpand = async (id: string) => {
    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      return;
    }

    setExpandedId(id);
    setDetailLoading(true);
    setDetail(null);

    try {
      const res = await fetch(`/api/campaigns/${id}`);
      if (res.ok) {
        const data: CampaignDetail = await res.json();
        setDetail(data);
      }
    } catch {
      // Silently fail
    } finally {
      setDetailLoading(false);
    }
  };

  // Delete a campaign
  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete campaign "${name}"? This cannot be undone.`)) return;

    try {
      const res = await fetch(`/api/campaigns/${id}`, { method: "DELETE" });
      if (res.ok) {
        setCampaigns((prev) => prev.filter((c) => c.id !== id));
        if (expandedId === id) {
          setExpandedId(null);
          setDetail(null);
        }
      }
    } catch {
      // Silently fail
    }
  };

  // Format date
  const formatDate = (iso: string) => {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  // Extract result data for detail view
  const resultData = detail?.result as PipelineResult | undefined;
  const scripts = resultData?.final_scripts?.scripts || [];
  const bestVariantId = resultData?.evaluation_round_1?.consensus?.best_variant_id;
  const audioFiles = resultData?.audio?.audio_files || [];
  const sessionId = resultData?.session_id || detail?.id || "";
  const voiceUsed = resultData?.audio?.voice_used;
  const voiceSelection = resultData?.voice_selection as VoiceSelection | undefined;

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-[var(--card-border)] bg-[var(--card)]/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-5xl mx-auto px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Link href="/">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-600 flex items-center justify-center">
                <Zap className="w-5 h-5 text-white" />
              </div>
            </Link>
            <div>
              <h1 className="text-lg font-bold text-white flex items-center gap-2">
                <LayoutDashboard className="w-4 h-4 text-brand-400" />
                Campaign Dashboard
              </h1>
              <p className="text-xs text-[var(--muted)]">
                {campaigns.length} saved campaign{campaigns.length !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <Link
            href="/"
            className="flex items-center gap-2 px-4 py-2 rounded-xl border border-[var(--card-border)] text-sm text-gray-400 hover:text-white hover:border-brand-500/30 transition-all"
          >
            <ArrowLeft className="w-4 h-4" />
            New Campaign
          </Link>
        </div>
      </header>

      <main className="max-w-5xl mx-auto px-6 py-8">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 text-brand-500 animate-spin" />
          </div>
        ) : campaigns.length === 0 ? (
          <div className="text-center py-20">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-[var(--card)] border border-[var(--card-border)] flex items-center justify-center mb-4">
              <FolderOpen className="w-8 h-8 text-gray-500" />
            </div>
            <h2 className="text-xl font-bold text-white mb-2">No campaigns yet</h2>
            <p className="text-gray-400 mb-6">
              Generate a campaign and save it to see it here.
            </p>
            <Link
              href="/"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-brand-600 text-white font-medium hover:bg-brand-500 transition-colors"
            >
              Generate Campaign
            </Link>
          </div>
        ) : (
          <div className="space-y-3">
            {campaigns.map((campaign) => (
              <div
                key={campaign.id}
                className="rounded-2xl bg-[var(--card)] border border-[var(--card-border)] overflow-hidden"
              >
                {/* Campaign Row */}
                <div
                  className="flex items-center justify-between px-6 py-4 cursor-pointer hover:bg-white/[0.02] transition-colors"
                  onClick={() => toggleExpand(campaign.id)}
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="shrink-0">
                      {expandedId === campaign.id ? (
                        <ChevronUp className="w-4 h-4 text-gray-500" />
                      ) : (
                        <ChevronDown className="w-4 h-4 text-gray-500" />
                      )}
                    </div>
                    <div className="min-w-0">
                      <h3 className="text-sm font-semibold text-white truncate">
                        {campaign.name}
                      </h3>
                      <div className="flex items-center gap-3 mt-1 text-xs text-[var(--muted)]">
                        <span className="flex items-center gap-1">
                          <Globe className="w-3 h-3" />
                          {campaign.country}
                        </span>
                        <span className="flex items-center gap-1">
                          <Radio className="w-3 h-3" />
                          {campaign.telco}
                        </span>
                        <span className="flex items-center gap-1">
                          <FileText className="w-3 h-3" />
                          {campaign.script_count} scripts
                        </span>
                        {campaign.has_audio && (
                          <span className="flex items-center gap-1 text-brand-400">
                            <Volume2 className="w-3 h-3" />
                            Audio
                          </span>
                        )}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-4 shrink-0">
                    <div className="text-right hidden sm:block">
                      <p className="text-xs text-[var(--muted)] flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {campaign.created_by}
                      </p>
                      <p className="text-xs text-[var(--muted)] flex items-center gap-1 mt-0.5">
                        <Calendar className="w-3 h-3" />
                        {formatDate(campaign.created_at)}
                      </p>
                    </div>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDelete(campaign.id, campaign.name);
                      }}
                      className="p-2 rounded-lg hover:bg-[var(--error)]/10 text-gray-500 hover:text-[var(--error)] transition-colors"
                      title="Delete campaign"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>

                {/* Expanded Detail */}
                {expandedId === campaign.id && (
                  <div className="border-t border-[var(--card-border)] px-6 py-6">
                    {detailLoading ? (
                      <div className="flex items-center justify-center py-10">
                        <Loader2 className="w-6 h-6 text-brand-500 animate-spin" />
                      </div>
                    ) : detail && resultData ? (
                      <div className="space-y-6">
                        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                          {/* Scripts */}
                          <div className="p-4 rounded-xl bg-[var(--background)] border border-[var(--card-border)]">
                            <ScriptReview
                              scripts={scripts}
                              bestVariantId={bestVariantId}
                              sessionId={sessionId}
                            />
                          </div>

                          {/* Voice & Audio */}
                          <div className="space-y-4">
                            {voiceSelection && (
                              <div className="p-4 rounded-xl bg-[var(--background)] border border-[var(--card-border)]">
                                <VoiceInfoPanel voiceSelection={voiceSelection} />
                              </div>
                            )}
                            {audioFiles.length > 0 && (
                              <div className="p-4 rounded-xl bg-[var(--background)] border border-[var(--card-border)]">
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
                          </div>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-[var(--muted)] text-center py-4">
                        Failed to load campaign details.
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
