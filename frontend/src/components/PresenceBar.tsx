"use client";

import type { PresenceUser } from "@/lib/types";

interface PresenceBarProps {
    users: PresenceUser[];
    maxVisible?: number;
}

export default function PresenceBar({ users, maxVisible = 5 }: PresenceBarProps) {
    if (users.length === 0) return null;

    const visible = users.slice(0, maxVisible);
    const overflow = users.length - maxVisible;

    return (
        <div className="flex items-center gap-1.5">
            <div className="flex -space-x-2">
                {visible.map((user) => (
                    <div
                        key={user.username}
                        className="relative group"
                        title={user.username}
                    >
                        <div
                            className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-bold text-white border-2 border-[var(--card)] ring-2 ring-transparent hover:ring-white/20 transition-all cursor-default"
                            style={{ backgroundColor: user.color || "#5c7cfa" }}
                        >
                            {user.username.charAt(0).toUpperCase()}
                        </div>
                        {/* Pulse for recently active (within last 30s) */}
                        {Date.now() / 1000 - user.last_active < 30 && (
                            <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 bg-[var(--success)] rounded-full border-2 border-[var(--card)] animate-pulse" />
                        )}
                        {/* Tooltip */}
                        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 rounded-lg bg-gray-900 text-xs text-white whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-50 border border-gray-700">
                            {user.username}
                            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-px border-4 border-transparent border-t-gray-900" />
                        </div>
                    </div>
                ))}
                {overflow > 0 && (
                    <div className="w-7 h-7 rounded-full flex items-center justify-center text-[10px] font-semibold text-gray-400 bg-gray-800 border-2 border-[var(--card)]">
                        +{overflow}
                    </div>
                )}
            </div>
            <span className="text-[10px] text-gray-500 ml-1">
                {users.length} online
            </span>
        </div>
    );
}
