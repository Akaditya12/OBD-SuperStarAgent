"use client";

import { useEffect, useState } from "react";
import {
    FolderOpen,
    Layers,
    Clock,
    Sparkles,
} from "lucide-react";

interface StatsCardsProps {
    campaignCount: number;
    scriptCount: number;
    audioCount: number;
    lastGeneratedAt?: string | null;
}

function AnimatedNumber({ value }: { value: number }) {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        if (value === 0) { setDisplay(0); return; }
        const duration = 700;
        const steps = 24;
        const increment = value / steps;
        let current = 0;
        const timer = setInterval(() => {
            current += increment;
            if (current >= value) {
                setDisplay(value);
                clearInterval(timer);
            } else {
                setDisplay(Math.floor(current));
            }
        }, duration / steps);
        return () => clearInterval(timer);
    }, [value]);

    return <>{display}</>;
}

function formatRelativeTime(iso: string): string {
    const diff = (Date.now() - new Date(iso).getTime()) / 1000;
    if (diff < 60) return "just now";
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return `${Math.floor(diff / 86400)}d ago`;
}

export default function StatsCards({
    campaignCount,
    scriptCount,
    audioCount,
    lastGeneratedAt,
}: StatsCardsProps) {
    return (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* Campaigns */}
            <div className="group relative p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--accent)]/30 transition-all duration-300 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/8 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2.5 rounded-xl bg-[var(--accent)]/10">
                            <FolderOpen className="w-5 h-5 text-[var(--accent)]" />
                        </div>
                        <Sparkles className="w-3.5 h-3.5 text-[var(--text-tertiary)] group-hover:text-[var(--accent)] transition-colors" />
                    </div>
                    <div className="text-3xl font-bold text-[var(--text-primary)] tabular-nums tracking-tight">
                        <AnimatedNumber value={campaignCount} />
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1 font-medium">Campaigns</p>
                </div>
            </div>

            {/* Content Assets -- combined scripts + audio */}
            <div className="group relative p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-emerald-500/30 transition-all duration-300 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/8 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2.5 rounded-xl bg-emerald-500/10">
                            <Layers className="w-5 h-5 text-emerald-500" />
                        </div>
                        <div className="flex items-center gap-1.5">
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 font-medium">
                                {scriptCount} scripts
                            </span>
                            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-amber-500/10 text-amber-500 font-medium">
                                {audioCount} audio
                            </span>
                        </div>
                    </div>
                    <div className="text-3xl font-bold text-[var(--text-primary)] tabular-nums tracking-tight">
                        <AnimatedNumber value={scriptCount + audioCount} />
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1 font-medium">Content Assets</p>
                </div>
            </div>

            {/* Last Generated */}
            <div className="group relative p-5 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-purple-500/30 transition-all duration-300 overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-500/8 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
                <div className="relative">
                    <div className="flex items-center justify-between mb-4">
                        <div className="p-2.5 rounded-xl bg-purple-500/10">
                            <Clock className="w-5 h-5 text-purple-500" />
                        </div>
                        {lastGeneratedAt && (
                            <span className="flex items-center gap-1 text-[10px] text-purple-400 font-medium">
                                <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
                                recent
                            </span>
                        )}
                    </div>
                    <div className="text-lg font-bold text-[var(--text-primary)] tracking-tight">
                        {lastGeneratedAt
                            ? formatRelativeTime(lastGeneratedAt)
                            : <span className="text-[var(--text-tertiary)] text-sm font-normal">No campaigns yet</span>
                        }
                    </div>
                    <p className="text-xs text-[var(--text-tertiary)] mt-1 font-medium">Last Generated</p>
                </div>
            </div>
        </div>
    );
}
