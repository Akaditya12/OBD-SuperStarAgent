"use client";

import { useEffect, useState } from "react";
import {
    MessageCircle,
    UserPlus,
    UserMinus,
    FolderPlus,
    Activity,
} from "lucide-react";
import type { CollaborationEvent } from "@/lib/types";

interface ActivityFeedProps {
    events?: CollaborationEvent[];
    maxItems?: number;
}

const EVENT_CONFIG: Record<
    string,
    { icon: React.ReactNode; color: string; label: string }
> = {
    campaign_created: {
        icon: <FolderPlus className="w-3.5 h-3.5" />,
        color: "text-[var(--success)]",
        label: "created a campaign",
    },
    comment_added: {
        icon: <MessageCircle className="w-3.5 h-3.5" />,
        color: "text-[var(--accent)]",
        label: "commented",
    },
    user_joined: {
        icon: <UserPlus className="w-3.5 h-3.5" />,
        color: "text-[var(--success)]",
        label: "came online",
    },
    user_left: {
        icon: <UserMinus className="w-3.5 h-3.5" />,
        color: "text-[var(--text-tertiary)]",
        label: "went offline",
    },
};

function timeAgo(timestamp: number): string {
    const seconds = Math.floor(Date.now() / 1000 - timestamp);
    if (seconds < 60) return "just now";
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
}

export default function ActivityFeed({
    events: externalEvents,
    maxItems = 15,
}: ActivityFeedProps) {
    const [events, setEvents] = useState<CollaborationEvent[]>(
        externalEvents || []
    );
    const [loading, setLoading] = useState(!externalEvents);

    // Fetch from API if no events provided externally
    useEffect(() => {
        if (externalEvents) {
            setEvents(externalEvents);
            return;
        }

        let cancelled = false;
        (async () => {
            try {
                const res = await fetch(`/api/activity?limit=${maxItems}`);
                if (res.ok && !cancelled) {
                    const data = await res.json();
                    setEvents(data.events || []);
                }
            } catch {
                // Silently fail
            } finally {
                if (!cancelled) setLoading(false);
            }
        })();
        return () => {
            cancelled = true;
        };
    }, [externalEvents, maxItems]);

    const displayEvents = events.slice(0, maxItems);

    return (
        <div>
            <div className="flex items-center gap-2 mb-4">
                <Activity className="w-4 h-4 text-[var(--accent)]" />
                <h3 className="text-sm font-medium text-[var(--text-secondary)]">Activity</h3>
            </div>

            {loading ? (
                <div className="space-y-3">
                    {[1, 2, 3].map((i) => (
                        <div key={i} className="flex items-center gap-3 animate-pulse">
                            <div className="w-6 h-6 rounded-full bg-[var(--input-bg)]" />
                            <div className="flex-1 h-3 rounded bg-[var(--input-bg)]" />
                        </div>
                    ))}
                </div>
            ) : displayEvents.length === 0 ? (
                <p className="text-xs text-[var(--text-tertiary)] text-center py-6">
                    No activity yet
                </p>
            ) : (
                <div className="space-y-0.5">
                    {displayEvents.map((event) => {
                        const config = EVENT_CONFIG[event.type] || {
                            icon: <Activity className="w-3.5 h-3.5" />,
                            color: "text-[var(--text-tertiary)]",
                            label: event.type,
                        };
                        return (
                            <div
                                key={event.id}
                                className="flex items-start gap-2.5 py-2 px-2 rounded-lg hover:bg-[var(--accent-subtle)]/30 transition-colors animate-fade-in"
                            >
                                <div
                                    className={`flex-shrink-0 mt-0.5 ${config.color}`}
                                >
                                    {config.icon}
                                </div>
                                <div className="flex-1 min-w-0">
                                    <p className="text-xs text-[var(--text-tertiary)]">
                                        <span className="font-medium text-[var(--text-secondary)]">
                                            {event.username}
                                        </span>{" "}
                                        {config.label}
                                        {event.campaign_name && (
                                            <>
                                                {" on "}
                                                <span className="font-medium text-[var(--text-secondary)]">
                                                    {event.campaign_name}
                                                </span>
                                            </>
                                        )}
                                    </p>
                                    {event.detail && (
                                        <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5 truncate">
                                            &ldquo;{event.detail}&rdquo;
                                        </p>
                                    )}
                                </div>
                                <span className="text-[10px] text-[var(--text-tertiary)] flex-shrink-0 mt-0.5">
                                    {timeAgo(event.timestamp)}
                                </span>
                            </div>
                        );
                    })}
                </div>
            )}
        </div>
    );
}
