"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Loader2, Users, Shield, UserPlus, StopCircle, RefreshCw } from "lucide-react";

interface User {
    id: string;
    username: string;
    email: string;
    role: string;
    team: string;
    is_active: boolean;
    created_at: string;
}

export default function AdminPage() {
    const router = useRouter();
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [showCreateForm, setShowCreateForm] = useState(false);
    const [creating, setCreating] = useState(false);
    const [formData, setFormData] = useState({
        username: "",
        email: "",
        password: "",
        role: "member",
        team: "Core"
    });

    const fetchUsers = async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/admin/users");
            if (res.status === 401 || res.status === 403) {
                router.push("/dashboard");
                return;
            }
            if (!res.ok) throw new Error("Failed to fetch users");
            const data = await res.json();
            setUsers(data.users || []);
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchUsers();
    }, []);

    const handleCreateUser = async (e: React.FormEvent) => {
        e.preventDefault();
        setCreating(true);
        setError("");
        try {
            const res = await fetch("/api/admin/users", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(formData),
            });
            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || "Failed to create user");
            }
            setShowCreateForm(false);
            setFormData({ username: "", email: "", password: "", role: "member", team: "Core" });
            fetchUsers();
        } catch (err: any) {
            setError(err.message);
        } finally {
            setCreating(false);
        }
    };

    const toggleUserStatus = async (userId: string, currentStatus: boolean) => {
        try {
            const res = await fetch(`/api/admin/users/${userId}`, {
                method: "PUT",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !currentStatus }),
            });
            if (!res.ok) throw new Error("Failed to update user");
            fetchUsers();
        } catch (err: any) {
            alert(err.message);
        }
    };

    if (loading && users.length === 0) {
        return (
            <div className="flex h-[50vh] items-center justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-[var(--accent)]" />
            </div>
        );
    }

    return (
        <div className="p-6 max-w-6xl mx-auto space-y-6">
            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold flex items-center gap-2">
                        <Shield className="w-6 h-6 text-[var(--warning)]" />
                        Admin Panel
                    </h1>
                    <p className="text-[var(--text-secondary)] mt-1 text-sm">Manage users, teams, and access control.</p>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={fetchUsers}
                        className="flex items-center gap-2 px-3 py-2 rounded-xl bg-[var(--card)] hover:bg-[var(--accent-subtle)] border border-[var(--card-border)] text-sm transition-colors"
                    >
                        <RefreshCw className="w-4 h-4" />
                    </button>
                    <button
                        onClick={() => setShowCreateForm(!showCreateForm)}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-white shadow-sm transition-all text-sm"
                        style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
                    >
                        <UserPlus className="w-4 h-4" />
                        {showCreateForm ? "Cancel" : "Add User"}
                    </button>
                </div>
            </div>

            {error && (
                <div className="bg-[var(--error)]/10 text-[var(--error)] border border-[var(--error)]/20 px-4 py-3 rounded-xl text-sm">
                    {error}
                </div>
            )}

            {showCreateForm && (
                <form onSubmit={handleCreateUser} className="bg-[var(--card)] border border-[var(--card-border)] rounded-2xl p-6 shadow-sm space-y-4">
                    <h2 className="text-lg font-semibold border-b border-[var(--card-border)] pb-2 mb-4">Create New User</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-[var(--text-secondary)] mb-1">Username</label>
                            <input
                                required type="text"
                                value={formData.username}
                                onChange={e => setFormData({ ...formData, username: e.target.value })}
                                className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-[var(--text-secondary)] mb-1">Email</label>
                            <input
                                required type="email"
                                value={formData.email}
                                onChange={e => setFormData({ ...formData, email: e.target.value })}
                                className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-[var(--text-secondary)] mb-1">Password</label>
                            <input
                                required type="password" minLength={8}
                                value={formData.password}
                                onChange={e => setFormData({ ...formData, password: e.target.value })}
                                className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className="block text-sm text-[var(--text-secondary)] mb-1">Role</label>
                                <select
                                    value={formData.role}
                                    onChange={e => setFormData({ ...formData, role: e.target.value })}
                                    className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                                >
                                                    <option value="member">Member</option>
                                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm text-[var(--text-secondary)] mb-1">Team</label>
                                <input
                                    required type="text"
                                    value={formData.team}
                                    onChange={e => setFormData({ ...formData, team: e.target.value })}
                                    className="w-full bg-[var(--input-bg)] border border-[var(--card-border)] rounded-xl px-3 py-2 text-sm focus:outline-none focus:border-[var(--accent)]"
                                />
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-end pt-2">
                        <button
                            type="submit"
                            disabled={creating}
                            className="px-6 py-2 rounded-xl font-medium text-white shadow-sm transition-all text-sm flex items-center gap-2"
                            style={{ background: `linear-gradient(135deg, var(--gradient-from), var(--gradient-to))` }}
                        >
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
                                        <span className={`inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border ${user.role === 'admin'
                                                ? 'bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20'
                                                : 'bg-[var(--accent)]/10 text-[var(--accent)] border-[var(--accent)]/20'
                                            }`}>
                                            {user.role}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 text-[var(--text-secondary)]">{user.team}</td>
                                    <td className="px-6 py-4">
                                        {user.is_active ? (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-500 text-xs font-medium border border-green-500/20">
                                                <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span> Active
                                            </span>
                                        ) : (
                                            <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[var(--error)]/10 text-[var(--error)] text-xs font-medium border border-[var(--error)]/20">
                                                <span className="w-1.5 h-1.5 rounded-full bg-[var(--error)]"></span> Inactive
                                            </span>
                                        )}
                                    </td>
                                    <td className="px-6 py-4 text-right">
                                        <button
                                            onClick={() => toggleUserStatus(user.id, user.is_active)}
                                            className="text-xs font-medium px-3 py-1.5 rounded-lg border border-[var(--card-border)] hover:bg-[var(--card-border)] transition-colors"
                                        >
                                            {user.is_active ? 'Deactivate' : 'Activate'}
                                        </button>
                                    </td>
                                </tr>
                            ))}
                            {users.length === 0 && (
                                <tr>
                                    <td colSpan={5} className="px-6 py-8 text-center text-[var(--text-tertiary)] text-sm">
                                        <Users className="w-8 h-8 mx-auto mb-2 opacity-50" />
                                        No users found.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
