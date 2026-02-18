"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Trash2, MessageCircle } from "lucide-react";
import type { Comment } from "@/lib/types";

interface CommentThreadProps {
    comments: Comment[];
    onAddComment: (text: string) => void;
    onDeleteComment?: (commentId: string) => void;
    currentUser?: string;
    typingUser?: string | null;
}

export default function CommentThread({
    comments,
    onAddComment,
    onDeleteComment,
    currentUser = "anonymous",
    typingUser,
}: CommentThreadProps) {
    const [newComment, setNewComment] = useState("");
    const scrollRef = useRef<HTMLDivElement>(null);

    // Auto-scroll to bottom when new comments arrive
    useEffect(() => {
        if (scrollRef.current) {
            scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
        }
    }, [comments.length]);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        const text = newComment.trim();
        if (!text) return;
        onAddComment(text);
        setNewComment("");
    };

    const formatTime = (iso: string) => {
        try {
            const d = new Date(iso);
            return d.toLocaleTimeString("en-US", {
                hour: "2-digit",
                minute: "2-digit",
            });
        } catch {
            return "";
        }
    };

    const formatDate = (iso: string) => {
        try {
            const d = new Date(iso);
            const now = new Date();
            if (d.toDateString() === now.toDateString()) return "Today";
            const yesterday = new Date(now);
            yesterday.setDate(yesterday.getDate() - 1);
            if (d.toDateString() === yesterday.toDateString()) return "Yesterday";
            return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
        } catch {
            return "";
        }
    };

    // Group comments by date
    const groupedComments = comments.reduce<Record<string, Comment[]>>(
        (acc, c) => {
            const dateKey = formatDate(c.created_at);
            if (!acc[dateKey]) acc[dateKey] = [];
            acc[dateKey].push(c);
            return acc;
        },
        {}
    );

    return (
        <div className="flex flex-col h-full">
            <div className="flex items-center gap-2 mb-3">
                <MessageCircle className="w-4 h-4 text-brand-400" />
                <h4 className="text-sm font-medium text-gray-300">
                    Comments
                    {comments.length > 0 && (
                        <span className="ml-1.5 text-xs text-gray-500">
                            ({comments.length})
                        </span>
                    )}
                </h4>
            </div>

            {/* Comment list */}
            <div
                ref={scrollRef}
                className="flex-1 overflow-y-auto space-y-1 max-h-[300px] pr-1 mb-3"
            >
                {comments.length === 0 ? (
                    <p className="text-xs text-gray-600 text-center py-6">
                        No comments yet. Start the conversation!
                    </p>
                ) : (
                    Object.entries(groupedComments).map(([date, dateComments]) => (
                        <div key={date}>
                            <div className="flex items-center gap-2 my-2">
                                <div className="flex-1 h-px bg-gray-800" />
                                <span className="text-[10px] text-gray-600 uppercase tracking-wider">
                                    {date}
                                </span>
                                <div className="flex-1 h-px bg-gray-800" />
                            </div>
                            {dateComments.map((comment) => (
                                <div
                                    key={comment.id}
                                    className="group flex items-start gap-2 py-1.5 px-2 rounded-lg hover:bg-white/[0.02] transition-colors"
                                >
                                    <div
                                        className="w-6 h-6 rounded-full flex items-center justify-center text-[9px] font-bold text-white flex-shrink-0 mt-0.5"
                                        style={{
                                            backgroundColor:
                                                comment.username === currentUser
                                                    ? "#5c7cfa"
                                                    : "#845ef7",
                                        }}
                                    >
                                        {comment.username.charAt(0).toUpperCase()}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-1.5">
                                            <span className="text-xs font-medium text-gray-300">
                                                {comment.username}
                                            </span>
                                            <span className="text-[10px] text-gray-600">
                                                {formatTime(comment.created_at)}
                                            </span>
                                        </div>
                                        <p className="text-xs text-gray-400 mt-0.5 break-words">
                                            {comment.text}
                                        </p>
                                    </div>
                                    {onDeleteComment &&
                                        comment.username === currentUser && (
                                            <button
                                                onClick={() => onDeleteComment(comment.id)}
                                                className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-[var(--error)]/10 text-gray-600 hover:text-[var(--error)] transition-all flex-shrink-0"
                                                title="Delete comment"
                                            >
                                                <Trash2 className="w-3 h-3" />
                                            </button>
                                        )}
                                </div>
                            ))}
                        </div>
                    ))
                )}

                {/* Typing indicator */}
                {typingUser && (
                    <div className="flex items-center gap-2 px-2 py-1">
                        <div className="flex gap-1">
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:0ms]" />
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:150ms]" />
                            <span className="w-1.5 h-1.5 rounded-full bg-gray-500 animate-bounce [animation-delay:300ms]" />
                        </div>
                        <span className="text-[10px] text-gray-500">
                            {typingUser} is typing...
                        </span>
                    </div>
                )}
            </div>

            {/* Input */}
            <form onSubmit={handleSubmit} className="flex items-center gap-2">
                <input
                    type="text"
                    value={newComment}
                    onChange={(e) => setNewComment(e.target.value)}
                    placeholder="Add a comment..."
                    className="flex-1 px-3 py-2 rounded-xl bg-[var(--background)] border border-[var(--card-border)] text-xs text-white placeholder-gray-600 focus:outline-none focus:border-brand-500/50 focus:ring-1 focus:ring-brand-500/20 transition-colors"
                />
                <button
                    type="submit"
                    disabled={!newComment.trim()}
                    className="p-2 rounded-xl bg-brand-600 text-white hover:bg-brand-500 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                >
                    <Send className="w-3.5 h-3.5" />
                </button>
            </form>
        </div>
    );
}
