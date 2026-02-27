"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
    Loader2, Users, Shield, UserPlus, RefreshCw,
    Settings, Save, RotateCcw, Mic2, FileText, Volume2,
    Bot, ChevronDown, ChevronUp, Undo2,
} from "lucide-react";

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    team: string;
    is_active: boolean;
    created_at: string;
}

interface PipelineConfig {
    max_script_words: number;
    num_script_variants: number;
    eval_feedback_rounds: number;
    num_hook_voices: number;
    elevenlabs_tts_model: string;
    elevenlabs_output_format: string;
    voice_stability: number;
    voice_similarity_boost: number;
    voice_style: number;
    bgm_volume_db: number;
    bgm_default_style: string;
    default_tts_engine: string;
}

const DEFAULTS: PipelineConfig = {
    max_script_words: 75,
    num_script_variants: 5,
    eval_feedback_rounds: 1,
    num_hook_voices: 3,
    elevenlabs_tts_model: "eleven_multilingual_v2",
    elevenlabs_output_format: "mp3_44100_192",
    voice_stability: 0.35,
    voice_similarity_boost: 0.80,
    voice_style: 0.45,
    bgm_volume_db: -26,
    bgm_default_style: "upbeat",
    default_tts_engine: "elevenlabs",
};

interface AgentConfig {
    key: string;
    label: string;
    description: string;
    default_prompt: string;
    custom_prompt: string;
    is_customized: boolean;
}

type Tab = "users" | "pipeline" | "agents";

export default function AdminPage() {
    const router = useRouter();
    const [tab, setTab] = useState<Tab>("users");

    // ── User Management State ──
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creating, setCreating] = useState(false);
    const [formData, setFormData] = useState({
        username: "", email: "", password: "", role: "member", team: "Core",
    });

    // ── Pipeline Config State ──
    const [config, setConfig] = useState<PipelineConfig>(DEFAULTS);
    const [configLoading, setConfigLoading] = useState(false);
    const [configSaving, setConfigSaving] = useState(false);
    const [configDirty, setConfigDirty] = useState(false);
    const [configMsg, setConfigMsg] = useState("");

    // ── Agent Prompts State ──
    const [agents, setAgents] = useState<AgentConfig[]>([]);
    const [agentsLoading, setAgentsLoading] = useState(false);
    const [expandedAgent, setExpandedAgent] = useState<string | null>(null);
    const [editedPrompts, setEditedPrompts] = useState<Record<string, string>>({});
    const [savingAgent, setSavingAgent] = useState<string | null>(null);
    const [agentMsg, setAgentMsg] = useState<Record<string, string>>({});

    const fetchUsers = async (retries = 2) => {
        setLoading(true);
        setError("");
        for (let attempt = 0; attempt <= retries; attempt++) {
            try {
                const res = await fetch("/api/admin/users");
                if (res.status === 401 || res.status === 403) { router.push("/dashboard"); return; }
                if (!res.ok) throw new Error("Failed to fetch users");
                const data = await res.json();
                setUsers(data.users || []);
                setLoading(false);
                return;
            } catch (err: any) {
                if (attempt === retries) {
                    setError(err.message);
                } else {
                    await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
                }
            }
        }
        setLoading(false);
    };

    const fetchConfig = async () => {
        setConfigLoading(true);
        try {
            const res = await fetch("/api/admin/config");
            if (res.ok) {
                const data = await res.json();
                setConfig({ ...DEFAULTS, ...data });
            }
        } catch { /* ignore */ }
        finally { setConfigLoading(false); }
    };

    const fetchAgents = async () => {
        setAgentsLoading(true);
        try {
            const res = await fetch("/api/admin/agents");
            if (res.ok) {
                const data = await res.json();
                setAgents(data.agents || []);
                const edits: Record<string, string> = {};
                for (const a of data.agents || []) {
                    edits[a.key] = a.is_customized ? a.custom_prompt : a.default_prompt;
                }
                setEditedPrompts(edits);
            }
        } catch { /* ignore */ }
        finally { setAgentsLoading(false); }
    };

    const saveAgentPrompt = async (agentKey: string) => {
        setSavingAgent(agentKey);
        setAgentMsg({});
        try {
            const res = await fetch(`/api/admin/agents/${agentKey}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: editedPrompts[agentKey] || "" }),
            });
            if (!res.ok) {
                const data = await res.json().catch(() => ({}));
                throw new Error(data.error || `HTTP ${res.status}`);
            }
            setAgentMsg({ [agentKey]: "Saved successfully" });
            fetchAgents();
            setTimeout(() => setAgentMsg({}), 4000);
        } catch (err: any) { setAgentMsg({ [agentKey]: `Error: ${err.message}` }); }
        finally { setSavingAgent(null); }
    };

    const resetAgentPrompt = async (agentKey: string) => {
        setSavingAgent(agentKey);
        try {
            await fetch(`/api/admin/agents/${agentKey}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: "" }),
            });
            setAgentMsg({ [agentKey]: "Reset to default" });
            fetchAgents();
            setTimeout(() => setAgentMsg({}), 3000);
        } catch { /* ignore */ }
        finally { setSavingAgent(null); }
    };

    useEffect(() => { fetchUsers(); fetchConfig(); fetchAgents(); }, []);

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true); setError("");
        try {
            const res = await fetch("/api/admin/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            if (!res.ok) { const data = await res.json(); throw new Error(data.error || "Failed to create user"); }
            setShowCreateForm(false);
            setFormData({ username: "", email: "", password: "", role: "member", team: "Core" });
            fetchUsers();
        } catch (err: any) { setError(err.message); }
        finally { setCreating(false); }
    };

    const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
        setError("");
        try {
            const res = await fetch(`/api/admin/users/${userId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !currentStatus }),
            });
            if (!res.ok) throw new Error("Failed to update user");
            fetchUsers();
        } catch (err: any) { setError(err.message); }
    };

    const updateConfig = (key: keyof PipelineConfig, value: number | string) => {
        setConfig((prev) => ({ ...prev, [key]: value }));
        setConfigDirty(true);
        setConfigMsg("");
    };

    const saveConfig = async () => {
        setConfigSaving(true); setConfigMsg("");
        try {
            const res = await fetch("/api/admin/config", {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(config),
            });
            if (!res.ok) throw new Error("Failed to save");
            const data = await res.json();
            setConfig({ ...DEFAULTS, ...data });
            setConfigDirty(false);
            setConfigMsg("Settings saved successfully");
            setTimeout(() => setConfigMsg(""), 3000);
        } catch (err: any) { setConfigMsg(`Error: ${err.message}`); }
        finally { setConfigSaving(false); }
    };

    const resetConfig = () => {
        setConfig(DEFAULTS);
        setConfigDirty(true);
        setConfigMsg("");
    };

    if (loading && users.length === 0 && tab === "users") {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
            </div>
        );
    }

    const inputCls = "w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]";
    const labelCls = "block text-sm text-[var(--text-secondary)] mb-1";

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Shield className="w-6 h-6 text-[var(--warning)]" />
                        Admin Panel
                    </h1>
                    <p className="text-[var(--text-secondary)] mt-1 text-sm">Manage users, teams, and pipeline settings.</p>
                </div>
                <div className="flex gap-2">
                    {tab === "users" && (
                        <>
                            <button onClick={fetchUsers} className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[var(--card)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] text-sm transition-colors">
                                <RefreshCw className="w-4 h-4" />
                            </button>
                            <button onClick={() => setShowCreateForm(!showCreateForm)} className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-white shadow-sm transition-all text-sm" style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}>
                                <UserPlus className="w-4 h-4" />
                                {showCreateForm ? "Cancel" : "Add User"}
                            </button>
                        </>
                    )}
                </div>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 p-1 bg-[var(--card)] border border-[var(--card-border)] rounded-xl w-fit">
                <button onClick={() => setTab("users")} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === "users" ? "bg-[var(--accent)] text-white shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                    <Users className="w-4 h-4" /> Users
                </button>
                <button onClick={() => setTab("pipeline")} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === "pipeline" ? "bg-[var(--accent)] text-white shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                    <Settings className="w-4 h-4" /> Pipeline Settings
                </button>
                <button onClick={() => setTab("agents")} className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${tab === "agents" ? "bg-[var(--accent)] text-white shadow-sm" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                    <Bot className="w-4 h-4" /> Agent Prompts
                </button>
            </div>

            {error && (
                <div className="bg-[var(--error)]/10 text-[var(--error)] border border-[var(--error)]/20 px-4 py-3 rounded-xl text-sm flex items-center justify-between">
                    <span>{error}</span>
                    <button onClick={() => { setError(""); fetchUsers(); }} className="ml-3 flex items-center gap-1 text-xs font-medium px-2 py-1 rounded-lg border border-[var(--error)]/20 hover:bg-[var(--error)]/10 transition-colors">
                        <RefreshCw className="w-3 h-3" /> Retry
                    </button>
                </div>
            )}

            {/* ═══════ Users Tab ═══════ */}
            {tab === "users" && (
                <>
                    {showCreateForm && (
                        <form onSubmit={handleCreateUser} className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm space-y-4">
                            <h2 className="text-lg font-semibold border-b border-[var(--card-border)] pb-2 mb-4">Create New User</h2>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className={labelCls}>Username</label>
                                    <input required type="text" value={formData.username} onChange={e => setFormData({ ...formData, username: e.target.value })} className={inputCls} />
                                </div>
                                <div>
                                    <label className={labelCls}>Email</label>
                                    <input required type="email" value={formData.email} onChange={e => setFormData({ ...formData, email: e.target.value })} className={inputCls} />
                                </div>
                                <div>
                                    <label className={labelCls}>Password</label>
                                    <input required type="password" minLength={8} value={formData.password} onChange={e => setFormData({ ...formData, password: e.target.value })} className={inputCls} />
                                </div>
                                <div className="grid grid-cols-2 gap-2">
                                    <div>
                                        <label className={labelCls}>Role</label>
                                        <select value={formData.role} onChange={e => setFormData({ ...formData, role: e.target.value })} className={inputCls}>
                                            <option value="member">Member</option>
                                            <option value="admin">Admin</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Team</label>
                                        <input required type="text" value={formData.team} onChange={e => setFormData({ ...formData, team: e.target.value })} className={inputCls} />
                                    </div>
                                </div>
                            </div>
                            <div className="flex justify-end pt-2">
                                <button type="submit" disabled={creating} className="px-6 py-2 rounded-xl font-medium text-white shadow-sm transition-all text-sm flex items-center gap-2" style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}>
                                    {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
                                    {creating ? "Creating..." : "Create User"}
                                </button>
                            </div>
                        </form>
                    )}

                    <div className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl overflow-hidden shadow-sm">
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-[var(--accent-subtle)]/50 text-[var(--text-secondary)]">
                                    <tr>
                                        <th className="px-6 py-4 font-medium">User</th>
                                        <th className="px-6 py-4 font-medium">Role</th>
                                        <th className="px-6 py-4 font-medium">Team</th>
                                        <th className="px-6 py-4 font-medium">Status</th>
                                        <th className="px-6 py-4 font-medium text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-[var(--card-border)]">
                                    {users.map((user) => (
                                        <tr key={user.id} className="hover:bg-[var(--accent-subtle)]/30 transition-colors">
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-8 h-8 rounded-full bg-[var(--accent-subtle)] flex items-center justify-center text-[var(--accent)] font-semibold shrink-0">
                                                        {user.username.charAt(0).toUpperCase()}
                                                    </div>
                                                    <div>
                                                        <div className="font-medium text-[var(--text-primary)]">{user.username}</div>
                                                        <div className="text-xs text-[var(--text-tertiary)]">{user.email}</div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4">
                                                <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${user.role === "admin" ? "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20" : "bg-[var(--accent)]/10 text-[var(--accent)] border-[var(--accent)]/20"}`}>
                                                    {user.role}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 text-[var(--text-secondary)]">{user.team}</td>
                                            <td className="px-6 py-4">
                                                {user.is_active ? (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-medium border border-green-500/20">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-green-500" /> Active
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--error)]/10 text-[var(--error)] text-xs font-medium border border-[var(--error)]/20">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-[var(--error)]" /> Inactive
                                                    </span>
                                                )}
                                            </td>
                                            <td className="px-6 py-4 text-right">
                                                <button onClick={() => toggleUserStatus(user.id, user.is_active)} className="text-xs font-medium px-3 py-1.5 rounded-lg border border-[var(--card-border)] hover:bg-[var(--card-border)] transition-colors">
                                                    {user.is_active ? "Deactivate" : "Activate"}
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                    {users.length === 0 && (
                                        <tr>
                                            <td colSpan={5} className="px-6 py-8 text-center text-[var(--text-tertiary)] text-sm">
                                                <Users className="w-8 h-8 mx-auto mb-2 opacity-50" /> No users found.
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </>
            )}

            {/* ═══════ Pipeline Settings Tab ═══════ */}
            {tab === "pipeline" && (
                <div className="space-y-6">
                    {configLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 animate-spin text-[var(--accent)]" />
                        </div>
                    ) : (
                        <>
                            {/* Script Generation */}
                            <section className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm">
                                <div className="flex items-center gap-2 mb-5">
                                    <FileText className="w-5 h-5 text-[var(--accent)]" />
                                    <h2 className="text-base font-semibold">Script Generation</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <label className={labelCls}>Max Words per Script</label>
                                        <div className="flex items-center gap-3">
                                            <input type="range" min={40} max={150} step={5} value={config.max_script_words} onChange={(e) => updateConfig("max_script_words", Number(e.target.value))} className="flex-1 accent-[var(--accent)]" />
                                            <span className="text-sm font-mono w-10 text-right text-[var(--text-primary)]">{config.max_script_words}</span>
                                        </div>
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">~{Math.round(config.max_script_words / 2.5)}s at normal pace</p>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Number of Variants</label>
                                        <div className="flex gap-2">
                                            {[3, 5, 7].map((n) => (
                                                <button key={n} type="button" onClick={() => updateConfig("num_script_variants", n)} className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${config.num_script_variants === n ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]" : "border-[var(--card-border)] text-[var(--text-secondary)] hover:border-[var(--card-border-hover)]"}`}>
                                                    {n}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Evaluation Rounds</label>
                                        <div className="flex gap-2">
                                            {[0, 1, 2].map((n) => (
                                                <button key={n} type="button" onClick={() => updateConfig("eval_feedback_rounds", n)} className={`flex-1 py-2 rounded-xl text-sm font-medium border transition-all ${config.eval_feedback_rounds === n ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]" : "border-[var(--card-border)] text-[var(--text-secondary)] hover:border-[var(--card-border-hover)]"}`}>
                                                    {n === 0 ? "None" : n}
                                                </button>
                                            ))}
                                        </div>
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">0 = skip evaluation, generate faster</p>
                                    </div>
                                </div>
                            </section>

                            {/* Voice & TTS */}
                            <section className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm">
                                <div className="flex items-center gap-2 mb-5">
                                    <Mic2 className="w-5 h-5 text-[var(--accent)]" />
                                    <h2 className="text-base font-semibold">Voice &amp; TTS Engine</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <label className={labelCls}>Default TTS Engine</label>
                                        <div className="flex gap-2">
                                            {(["elevenlabs", "murf", "edge-tts"] as const).map((eng) => (
                                                <button key={eng} type="button" onClick={() => updateConfig("default_tts_engine", eng)} className={`flex-1 py-2 rounded-xl text-xs font-medium border transition-all ${config.default_tts_engine === eng ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]" : "border-[var(--card-border)] text-[var(--text-secondary)] hover:border-[var(--card-border-hover)]"}`}>
                                                    {eng === "elevenlabs" ? "ElevenLabs" : eng === "murf" ? "Murf AI" : "Free TTS"}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <label className={labelCls}>ElevenLabs Model</label>
                                        <select value={config.elevenlabs_tts_model} onChange={(e) => updateConfig("elevenlabs_tts_model", e.target.value)} className={inputCls}>
                                            <option value="eleven_multilingual_v2">Multilingual V2 (recommended)</option>
                                            <option value="eleven_turbo_v2_5">Turbo V2.5 (faster)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Voice Options per Variant</label>
                                        <div className="flex gap-2">
                                            {[2, 3, 4].map((n) => (
                                                <button key={n} type="button" onClick={() => updateConfig("num_hook_voices", n)} className={`flex-1 py-2 rounded-xl text-xs font-medium border transition-all ${config.num_hook_voices === n ? "border-[var(--accent)] bg-[var(--accent-subtle)] text-[var(--accent)]" : "border-[var(--card-border)] text-[var(--text-secondary)] hover:border-[var(--card-border-hover)]"}`}>
                                                    {n}
                                                </button>
                                            ))}
                                        </div>
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Number of voice previews to generate</p>
                                    </div>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
                                    <div>
                                        <label className={labelCls}>Stability ({config.voice_stability.toFixed(2)})</label>
                                        <input type="range" min={0.1} max={0.9} step={0.05} value={config.voice_stability} onChange={(e) => updateConfig("voice_stability", Number(e.target.value))} className="w-full accent-[var(--accent)]" />
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Lower = more expressive, Higher = more consistent</p>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Similarity ({config.voice_similarity_boost.toFixed(2)})</label>
                                        <input type="range" min={0.3} max={1.0} step={0.05} value={config.voice_similarity_boost} onChange={(e) => updateConfig("voice_similarity_boost", Number(e.target.value))} className="w-full accent-[var(--accent)]" />
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Higher = closer to original voice character</p>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Style ({config.voice_style.toFixed(2)})</label>
                                        <input type="range" min={0.0} max={1.0} step={0.05} value={config.voice_style} onChange={(e) => updateConfig("voice_style", Number(e.target.value))} className="w-full accent-[var(--accent)]" />
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Higher = more emotional expressiveness</p>
                                    </div>
                                </div>
                            </section>

                            {/* Audio Production */}
                            <section className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm">
                                <div className="flex items-center gap-2 mb-5">
                                    <Volume2 className="w-5 h-5 text-[var(--accent)]" />
                                    <h2 className="text-base font-semibold">Audio Production</h2>
                                </div>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                                    <div>
                                        <label className={labelCls}>Output Format</label>
                                        <select value={config.elevenlabs_output_format} onChange={(e) => updateConfig("elevenlabs_output_format", e.target.value)} className={inputCls}>
                                            <option value="mp3_44100_192">MP3 192kbps (premium)</option>
                                            <option value="mp3_44100_128">MP3 128kbps (standard)</option>
                                            <option value="mp3_44100_64">MP3 64kbps (fast)</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className={labelCls}>BGM Volume ({config.bgm_volume_db} dB)</label>
                                        <input type="range" min={-40} max={-10} step={2} value={config.bgm_volume_db} onChange={(e) => updateConfig("bgm_volume_db", Number(e.target.value))} className="w-full accent-[var(--accent)]" />
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-1">Lower = quieter background music</p>
                                    </div>
                                    <div>
                                        <label className={labelCls}>Default BGM Style</label>
                                        <select value={config.bgm_default_style} onChange={(e) => updateConfig("bgm_default_style", e.target.value)} className={inputCls}>
                                            <option value="upbeat">Upbeat</option>
                                            <option value="corporate">Corporate</option>
                                            <option value="warm">Warm</option>
                                            <option value="energetic">Energetic</option>
                                            <option value="calm">Calm</option>
                                        </select>
                                    </div>
                                </div>
                            </section>

                            {/* Save / Reset */}
                            <div className="flex items-center justify-between">
                                <div className="text-sm">
                                    {configMsg && (
                                        <span className={configMsg.startsWith("Error") ? "text-[var(--error)]" : "text-[var(--success)]"}>
                                            {configMsg}
                                        </span>
                                    )}
                                </div>
                                <div className="flex gap-3">
                                    <button onClick={resetConfig} className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-medium border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--card)] transition-colors">
                                        <RotateCcw className="w-4 h-4" /> Reset to Defaults
                                    </button>
                                    <button onClick={saveConfig} disabled={!configDirty || configSaving} className="flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-medium text-white shadow-sm transition-all disabled:opacity-40" style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}>
                                        {configSaving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                                        {configSaving ? "Saving..." : "Save Settings"}
                                    </button>
                                </div>
                            </div>
                        </>
                    )}
                </div>
            )}

            {/* ═══════ Agent Prompts Tab ═══════ */}
            {tab === "agents" && (
                <div className="space-y-4">
                    <p className="text-sm text-[var(--text-secondary)]">
                        Edit the system prompt for each pipeline agent. Changes take effect on the next campaign generation.
                        Resetting removes the custom prompt and reverts to the code default.
                    </p>

                    {agentsLoading ? (
                        <div className="flex items-center justify-center py-12">
                            <Loader2 className="w-6 h-6 animate-spin text-[var(--accent)]" />
                        </div>
                    ) : (
                        agents.map((agent) => {
                            const isExpanded = expandedAgent === agent.key;
                            const currentPrompt = editedPrompts[agent.key] || "";
                            const isDirty = agent.is_customized
                                ? currentPrompt !== agent.custom_prompt
                                : currentPrompt !== agent.default_prompt;
                            const msg = agentMsg[agent.key];

                            return (
                                <div key={agent.key} className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl overflow-hidden shadow-sm">
                                    {/* Header */}
                                    <button
                                        onClick={() => setExpandedAgent(isExpanded ? null : agent.key)}
                                        className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-[var(--accent-subtle)]/30 transition-colors"
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className="w-8 h-8 rounded-lg bg-[var(--accent-subtle)] flex items-center justify-center">
                                                <Bot className="w-4 h-4 text-[var(--accent)]" />
                                            </div>
                                            <div>
                                                <div className="flex items-center gap-2">
                                                    <span className="text-sm font-semibold text-[var(--text-primary)]">{agent.label}</span>
                                                    {agent.is_customized && (
                                                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20 font-medium">
                                                            Customized
                                                        </span>
                                                    )}
                                                </div>
                                                <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{agent.description}</p>
                                            </div>
                                        </div>
                                        {isExpanded ? <ChevronUp className="w-4 h-4 text-[var(--text-tertiary)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-tertiary)]" />}
                                    </button>

                                    {/* Expanded Content */}
                                    {isExpanded && (
                                        <div className="px-6 pb-5 pt-1 border-t border-[var(--card-border)]">
                                            <textarea
                                                value={currentPrompt}
                                                onChange={(e) => setEditedPrompts((prev) => ({ ...prev, [agent.key]: e.target.value }))}
                                                rows={16}
                                                className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl p-4 text-xs font-mono leading-relaxed resize-y focus:outline-none focus:border-[var(--accent)] text-[var(--text-primary)]"
                                                spellCheck={false}
                                            />
                                            <div className="flex items-center justify-between mt-3">
                                                <div className="text-xs">
                                                    {msg && (
                                                        <span className={msg.startsWith("Error") ? "text-[var(--error)]" : "text-[var(--success)]"}>
                                                            {msg}
                                                        </span>
                                                    )}
                                                    <span className="text-[var(--text-tertiary)] ml-2">
                                                        {currentPrompt.length} chars
                                                    </span>
                                                </div>
                                                <div className="flex gap-2">
                                                    {(agent.is_customized || currentPrompt !== agent.default_prompt) && (
                                                        <button
                                                            onClick={() => {
                                                                if (agent.is_customized) {
                                                                    resetAgentPrompt(agent.key);
                                                                } else {
                                                                    setEditedPrompts((prev) => ({ ...prev, [agent.key]: agent.default_prompt }));
                                                                }
                                                            }}
                                                            disabled={savingAgent === agent.key}
                                                            className="flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium border border-[var(--card-border)] text-[var(--text-secondary)] hover:bg-[var(--card-border)] transition-colors disabled:opacity-40"
                                                        >
                                                            <Undo2 className="w-3.5 h-3.5" /> {agent.is_customized ? "Reset to Default" : "Undo Changes"}
                                                        </button>
                                                    )}
                                                    <button
                                                        onClick={() => saveAgentPrompt(agent.key)}
                                                        disabled={savingAgent === agent.key || !isDirty}
                                                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium text-white shadow-sm transition-all disabled:opacity-40"
                                                        style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
                                                    >
                                                        {savingAgent === agent.key ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />}
                                                        Save
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )}
                                </div>
                            );
                        })
                    )}
                </div>
            )}
        </div>
    );
}
