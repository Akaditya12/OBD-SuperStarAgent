"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Trash2,
  Globe,
  Building2,
  ChevronDown,
  Play,
  Download,
  FileText,
  Search,
  Loader2,
  Calendar,
} from "lucide-react";
import StatsCards from "@/components/StatsCards";
import CommentThread from "@/components/CommentThread";
import ActivityFeed from "@/components/ActivityFeed";
import { useToast } from "@/components/ToastProvider";
import type {
  Campaign,
  CampaignDetail,
  Comment,
  PresenceUser,
  CollaborationEvent,
  Script,
  AudioFile,
} from "@/lib/types";

export default function DashboardPage() {
  const router = useRouter();
  const { toast } = useToast();

  const [authChecked, setAuthChecked] = useState(false);
  const [username, setUsername] = useState("user");

  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<CampaignDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  // Collaboration state
  const [comments, setComments] = useState<Comment[]>([]);
  const [presenceUsers, setPresenceUsers] = useState<PresenceUser[]>([]);
  const [activityEvents, setActivityEvents] = useState<CollaborationEvent[]>([]);
  const [typingUser, setTypingUser] = useState<string | null>(null);
  const collabWsRef = useRef<WebSocket | null>(null);

  // Audio
  const [playingAudio, setPlayingAudio] = useState<string | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

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
      .catch(() => setAuthChecked(true));
  }, [router]);

  // ── Load campaigns ──
  const loadCampaigns = useCallback(async () => {
    try {
      const res = await fetch("/api/campaigns");
      if (res.ok) {
        const data = await res.json();
        setCampaigns(data.campaigns || []);
      }
    } catch {
      // silent
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCampaigns();
  }, [loadCampaigns]);

  // ── Load activity feed ──
  useEffect(() => {
    const fetchActivity = async () => {
      try {
        const res = await fetch("/api/activity?limit=15");
        if (res.ok) {
          const data = await res.json();
          setActivityEvents(data.events || []);
        }
      } catch { /* silent */ }
    };
    fetchActivity();
    const interval = setInterval(fetchActivity, 15000);
    return () => clearInterval(interval);
  }, []);

  // ── Toggle expand / collaboration WS ──
  const toggleExpand = async (id: string) => {
    // Disconnect previous WS
    if (collabWsRef.current) {
      collabWsRef.current.close();
      collabWsRef.current = null;
    }

    if (expandedId === id) {
      setExpandedId(null);
      setDetail(null);
      setComments([]);
      setPresenceUsers([]);
      return;
    }

    setExpandedId(id);
    setDetailLoading(true);
    setDetail(null);
    setComments([]);
    setPresenceUsers([]);

    try {
      const res = await fetch(`/api/campaigns/${id}`);
      if (res.ok) {
        const data: CampaignDetail = await res.json();
        setDetail(data);
      }
    } catch { /* silent */ }
    finally {
      setDetailLoading(false);
    }

    // Connect collaboration WebSocket
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/collaborate/${id}`;
    const ws = new WebSocket(wsUrl);
    collabWsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "init") {
          setPresenceUsers(data.users || []);
          setComments(data.comments || []);
        } else if (data.type === "user_joined") {
          setPresenceUsers((prev) => [...prev, data.user]);
        } else if (data.type === "user_left") {
          setPresenceUsers((prev) =>
            prev.filter((u) => u.username !== data.username)
          );
        } else if (data.type === "comment_added") {
          setComments((prev) => [...prev, data.comment]);
        } else if (data.type === "comment_deleted") {
          setComments((prev) =>
            prev.filter((c) => c.id !== data.comment_id)
          );
        } else if (data.type === "typing") {
          setTypingUser(data.username);
          setTimeout(() => setTypingUser(null), 3000);
        } else if (data.type === "activity") {
          setActivityEvents((prev) => [data.event, ...prev].slice(0, 15));
        }
      } catch { /* ignore */ }
    };
  };

  // ── Comments ──
  const handleAddComment = async (text: string) => {
    if (!expandedId) return;
    try {
      await fetch(`/api/campaigns/${expandedId}/comments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, username }),
      });
    } catch {
      toast("error", "Failed to add comment");
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!expandedId) return;
    try {
      await fetch(`/api/campaigns/${expandedId}/comments/${commentId}`, {
        method: "DELETE",
      });
    } catch {
      toast("error", "Failed to delete comment");
    }
  };

  // ── Delete campaign ──
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
        toast("success", `Campaign "${name}" deleted`);
      }
    } catch {
      toast("error", "Failed to delete campaign");
    }
  };

  // ── Audio ──
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

  // ── Cleanup ──
  useEffect(() => {
    return () => {
      if (collabWsRef.current) collabWsRef.current.close();
    };
  }, []);

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Filter campaigns
  const filtered = searchQuery
    ? campaigns.filter(
      (c) =>
        c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.country?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.telco?.toLowerCase().includes(searchQuery.toLowerCase())
    )
    : campaigns;

  // Stats
  const totalScripts = campaigns.reduce((s, c) => s + (c.script_count || 0), 0);
  const totalAudio = campaigns.reduce(
    (s, c) => s + (c.has_audio ? c.script_count || 1 : 0),
    0
  );

  const scripts =
    detail?.result?.final_scripts?.scripts ||
    detail?.result?.revised_scripts_round_1?.scripts ||
    detail?.result?.initial_scripts?.scripts ||
    [];
  const audioFiles = (detail?.result?.audio?.audio_files || []).filter(
    (af: AudioFile) => af.file_name && !af.error
  );

  // Group audio files by variant for smart pairing
  const audioByVariant: Record<number, AudioFile[]> = {};
  for (const af of audioFiles) {
    const vid = af.variant_id ?? 0;
    if (!audioByVariant[vid]) audioByVariant[vid] = [];
    audioByVariant[vid].push(af);
  }

  return (
    <div className="min-h-screen px-4 sm:px-6 lg:px-8 py-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8 flex items-end justify-between">
          <div>
            <h1 className="text-2xl font-bold text-[var(--text-primary)] tracking-tight">Dashboard</h1>
            <p className="text-sm text-[var(--text-tertiary)] mt-0.5">
              Manage campaigns and track team activity
            </p>
          </div>
          <button
            onClick={() => router.push("/")}
            className="px-4 py-2 text-xs font-medium rounded-xl bg-[var(--accent)] text-white hover:opacity-90 transition-opacity"
          >
            + New Campaign
          </button>
        </div>

        {/* Stats */}
        <div className="mb-8">
          <StatsCards
            campaignCount={campaigns.length}
            scriptCount={totalScripts}
            audioCount={totalAudio}
            lastGeneratedAt={campaigns.length > 0 ? campaigns[0].created_at : null}
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Campaigns (2/3 width) */}
          <div className="lg:col-span-2 space-y-4">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-[var(--text-tertiary)]" />
              <input
                type="text"
                placeholder="Search campaigns..."
                className="w-full pl-10 pr-4 py-3 rounded-xl bg-[var(--card)] border border-[var(--card-border)] text-sm text-[var(--text-primary)] placeholder-[var(--text-tertiary)] focus:outline-none focus:border-[var(--accent)]/50 focus:ring-2 focus:ring-[var(--accent)]/10 transition-all"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Campaign list */}
            {loading ? (
              <div className="flex items-center justify-center py-16">
                <Loader2 className="w-6 h-6 text-[var(--accent)] animate-spin" />
              </div>
            ) : filtered.length === 0 ? (
              <div className="text-center py-16">
                <div className="w-12 h-12 mx-auto mb-3 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] flex items-center justify-center">
                  <FileText className="w-5 h-5 text-[var(--text-tertiary)]" />
                </div>
                <p className="text-sm text-[var(--text-tertiary)]">
                  {searchQuery
                    ? "No campaigns match your search"
                    : "No campaigns yet. Create one to get started."}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filtered.map((campaign) => (
                  <div
                    key={campaign.id}
                    className={`rounded-2xl bg-[var(--card)] border overflow-hidden transition-all duration-200 group ${expandedId === campaign.id
                      ? "border-[var(--accent)]/30 shadow-lg shadow-[var(--accent)]/5"
                      : "border-[var(--card-border)] hover:border-[var(--card-border-hover)]"
                      }`}
                  >
                    {/* Header row */}
                    <div
                      role="button"
                      tabIndex={0}
                      className="w-full flex items-center justify-between px-5 py-4 text-left cursor-pointer select-none"
                      onClick={() => toggleExpand(campaign.id)}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          toggleExpand(campaign.id);
                        }
                      }}
                    >
                        <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2.5 mb-1.5">
                          <h3 className="text-sm font-semibold text-[var(--text-primary)] truncate">
                            {campaign.name}
                          </h3>
                        </div>
                        <div className="flex items-center gap-2 flex-wrap">
                          {campaign.country && (
                            <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-[var(--accent)]/8 text-[var(--accent)] font-medium">
                              <Globe className="w-2.5 h-2.5" />
                              {campaign.country}
                            </span>
                          )}
                          {campaign.telco && (
                            <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-purple-500/8 text-purple-500 font-medium">
                              <Building2 className="w-2.5 h-2.5" />
                              {campaign.telco}
                            </span>
                          )}
                          <span className="inline-flex items-center gap-1 text-[10px] text-[var(--text-tertiary)]">
                            <Calendar className="w-2.5 h-2.5" />
                            {new Date(campaign.created_at).toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" })}
                          </span>
                          <span className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/8 text-emerald-500 font-medium">
                            {campaign.script_count} variants
                          </span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 ml-3">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleDelete(campaign.id, campaign.name);
                          }}
                          className="p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--error)] hover:bg-[var(--error)]/10 transition-colors opacity-0 group-hover:opacity-100"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                        <div className={`p-1 rounded-lg transition-transform duration-200 ${expandedId === campaign.id ? "rotate-180" : ""}`}>
                          <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />
                        </div>
                      </div>
                    </div>

                    {/* Expanded detail */}
                    {expandedId === campaign.id && (
                      <div className="px-5 pb-5 border-t border-[var(--card-border)]">
                        {detailLoading ? (
                          <div className="flex items-center justify-center py-10">
                            <Loader2 className="w-5 h-5 text-[var(--accent)] animate-spin" />
                          </div>
                        ) : detail ? (
                          <div className="space-y-3 mt-4">
                            {/* Global session actions */}
                            <div className="flex items-center justify-between pb-3 border-b border-[var(--card-border)] mb-4">
                              <h4 className="text-[10px] uppercase tracking-wider text-[var(--text-tertiary)] font-semibold">
                                Campaign Assets
                              </h4>
                              <div className="flex items-center gap-2">
                                <a
                                  href={`/api/sessions/${campaign.id}/scripts?fmt=text`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] transition-colors"
                                >
                                  <Download className="w-2.5 h-2.5" />
                                  Scripts (Text)
                                </a>
                                <a
                                  href={`/api/sessions/${campaign.id}/scripts?fmt=json`}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] transition-colors"
                                >
                                  <Download className="w-2.5 h-2.5" />
                                  Scripts (JSON)
                                </a>
                              </div>
                            </div>

                            {/* Script + Audio paired cards */}
                            {scripts.length > 0 && (
                              <div className="space-y-2.5">
                                {scripts.map((script: Script, idx: number) => {
                                  const vid = script.variant_id || idx + 1;
                                  const variantAudio = audioByVariant[vid] || [];
                                  const audioSessionId = detail?.result?.audio?.session_id || detail?.result?.session_id || "";

                                  return (
                                    <div
                                      key={idx}
                                      className="p-4 rounded-xl bg-[var(--background)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-colors"
                                    >
                                      {/* Variant header */}
                                      <div className="flex items-center justify-between mb-2.5">
                                        <div className="flex items-center gap-2">
                                          <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-[var(--accent)]/10 text-[var(--accent)]">
                                            V{vid}
                                          </span>
                                          <a
                                            href={`/api/sessions/${campaign.id}/scripts?fmt=text&variant_id=${vid}`}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            title="Download this script variant"
                                            className="p-1 rounded-md text-[var(--text-tertiary)] hover:text-[var(--accent)] hover:bg-[var(--accent-subtle)] transition-all"
                                          >
                                            <Download className="w-3 h-3" />
                                          </a>
                                          {script.theme && (
                                            <span className="text-xs font-medium text-[var(--text-secondary)]">
                                              {script.theme}
                                            </span>
                                          )}
                                        </div>
                                        <span className="text-[10px] text-[var(--text-tertiary)]">
                                          {script.word_count || "?"} words &middot; ~{script.estimated_duration_seconds || "?"}s
                                        </span>
                                      </div>

                                      {/* Script text */}
                                      {script.full_script && (
                                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed mb-3 whitespace-pre-wrap max-h-[150px] overflow-y-auto p-2 rounded-lg bg-[var(--input-bg)]/50 border border-[var(--card-border)]/50">
                                          {script.full_script}
                                        </p>
                                      )}

                                      {/* Audio controls inline */}
                                      {variantAudio.length > 0 && (
                                        <div className="flex items-center gap-2 flex-wrap pt-2 border-t border-[var(--card-border)]">
                                          {variantAudio.map((af: AudioFile, ai: number) => {
                                            const audioUrl = af.public_url || `/api/audio/${audioSessionId}/${af.file_name}`;
                                            const label = af.file_name?.replace(/\.(mp3|wav)$/, "").replace(`variant_${vid}_`, "") || `audio_${ai}`;
                                            const isPlaying = playingAudio === audioUrl;
                                            return (
                                              <div key={ai} className="flex items-center gap-1.5">
                                                <button
                                                  onClick={() => toggleAudio(audioUrl)}
                                                  className={`inline-flex items-center gap-1 px-2 py-1 rounded-lg text-[10px] font-medium transition-all ${isPlaying
                                                    ? "bg-[var(--accent)] text-white shadow-sm"
                                                    : "bg-[var(--card)] border border-[var(--card-border)] text-[var(--text-secondary)] hover:border-[var(--accent)]/30"
                                                    }`}
                                                >
                                                  <Play className={`w-2.5 h-2.5 ${isPlaying ? "animate-pulse" : ""}`} />
                                                  {label}
                                                </button>
                                                <a
                                                  href={audioUrl}
                                                  download
                                                  className="p-1 rounded text-[var(--text-tertiary)] hover:text-[var(--accent)] transition-colors"
                                                >
                                                  <Download className="w-2.5 h-2.5" />
                                                </a>
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

                            {/* Comments */}
                            <div className="pt-3 border-t border-[var(--card-border)]">
                              <CommentThread
                                comments={comments}
                                onAddComment={handleAddComment}
                                onDeleteComment={handleDeleteComment}
                                currentUser={username}
                                typingUser={typingUser}
                              />
                            </div>
                          </div>
                        ) : (
                          <p className="text-xs text-[var(--text-tertiary)] py-6 text-center">
                            Failed to load campaign details.
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Sidebar: Online + Activity Feed (1/3 width) */}
          <div className="space-y-4 sticky top-8">
            {/* Online Users */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
                <h3 className="text-sm font-medium text-[var(--text-secondary)]">Online Now</h3>
              </div>
              {presenceUsers.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] py-2">No team members online</p>
              ) : (
                <div className="space-y-2">
                  {presenceUsers.map((user) => (
                    <div key={user.username} className="flex items-center gap-2.5">
                      <div
                        className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white flex-shrink-0"
                        style={{ backgroundColor: user.color || "#5c7cfa" }}
                      >
                        {user.username.charAt(0).toUpperCase()}
                      </div>
                      <span className="text-xs text-[var(--text-primary)] font-medium truncate">{user.username}</span>
                      <span className="w-1.5 h-1.5 rounded-full bg-[var(--success)] flex-shrink-0 ml-auto" />
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Activity Feed */}
            <div className="p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)]">
              <ActivityFeed events={activityEvents} maxItems={15} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
