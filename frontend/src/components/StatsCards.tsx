"use client";

import { useEffect, useState } from "react";
import {
    FolderOpen,
    FileText,
    Volume2,
    Users,
    TrendingUp,
} from "lucide-react";

interface StatItem {
    label: string;
    value: number;
    icon: React.ReactNode;
    color: string;
    gradient: string;
}

interface StatsCardsProps {
    campaignCount: number;
    scriptCount: number;
    audioCount: number;
    onlineUsers?: number;
}

function AnimatedNumber({ value }: { value: number }) {
    const [display, setDisplay] = useState(0);

    useEffect(() => {
        if (value === 0) {
            setDisplay(0);
            return;
        }
        const duration = 600;
        const steps = 20;
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

export default function StatsCards({
    campaignCount,
    scriptCount,
    audioCount,
    onlineUsers = 0,
}: StatsCardsProps) {
    const stats: StatItem[] = [
        {
            label: "Campaigns",
            value: campaignCount,
            icon: <FolderOpen className="w-5 h-5" />,
            color: "text-brand-400",
            gradient: "from-brand-500/20 to-brand-600/5",
        },
        {
            label: "Scripts",
            value: scriptCount,
            icon: <FileText className="w-5 h-5" />,
            color: "text-emerald-400",
            gradient: "from-emerald-500/20 to-emerald-600/5",
        },
        {
            label: "Audio Files",
            value: audioCount,
            icon: <Volume2 className="w-5 h-5" />,
            color: "text-amber-400",
            gradient: "from-amber-500/20 to-amber-600/5",
        },
        {
            label: "Team Online",
            value: onlineUsers,
            icon: <Users className="w-5 h-5" />,
            color: "text-purple-400",
            gradient: "from-purple-500/20 to-purple-600/5",
        },
    ];

    return (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat) => (
                <div
                    key={stat.label}
                    className="group relative p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-border)] hover:border-[var(--card-border-hover)] transition-all duration-300 overflow-hidden"
                >
                    {/* Gradient background */}
                    <div
                        className={`absolute inset-0 bg-gradient-to-br ${stat.gradient} opacity-0 group-hover:opacity-100 transition-opacity duration-500`}
                    />

                    <div className="relative">
                        <div className="flex items-center justify-between mb-3">
                            <div
                                className={`p-2 rounded-xl bg-white/[0.04] ${stat.color}`}
                            >
                                {stat.icon}
                            </div>
                            <TrendingUp className="w-3.5 h-3.5 text-gray-700 group-hover:text-gray-500 transition-colors" />
                        </div>
                        <div className="text-2xl font-bold text-[var(--text-primary)] tabular-nums">
                            <AnimatedNumber value={stat.value} />
                        </div>
                        <p className="text-xs text-[var(--text-tertiary)] mt-0.5">{stat.label}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}
