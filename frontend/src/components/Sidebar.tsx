"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    Home,
    LayoutDashboard,
    ChevronLeft,
    ChevronRight,
    Menu,
    X,
    Sparkles,
    Radio,
    Shield,
    Mic2,
    Phone,
    Package,
} from "lucide-react";
import ThemePicker from "./ThemePicker";
import BNGLogo from "./BNGLogo";

const NAV_ITEMS = [
    { href: "/", label: "Home", icon: Home },
    { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
];

const ADMIN_NAV_ITEM = { href: "/admin", label: "Admin Panel", icon: Shield };

const BNG_PRODUCT_LIST = [
    { id: "eva", label: "EVA", icon: Sparkles },
    { id: "smartconnect", label: "SmartConnect AI", icon: Radio },
    { id: "callsignature", label: "Call Signature", icon: Shield },
    { id: "magicvoice", label: "Magic Voice IVR", icon: Mic2 },
    { id: "magiccall", label: "Magic Call App", icon: Phone },
];

export default function Sidebar() {
    const pathname = usePathname();
    const [collapsed, setCollapsed] = useState(false);
    const [mobileOpen, setMobileOpen] = useState(false);
    const [userRole, setUserRole] = useState<string | null>(null);

    useEffect(() => {
        const fetchUser = async () => {
            try {
                const res = await fetch("/api/auth/me");
                const data = await res.json();
                if (data.authenticated) {
                    setUserRole(data.role);
                }
            } catch (err) {
                console.error("Failed to fetch user role", err);
            }
        };
        fetchUser();
    }, []);

    const navContent = (
        <div className="flex flex-col h-full">
            {/* Logo */}
            <div className="flex items-center gap-3 px-4 py-5 border-b border-[var(--card-border)]">
                <BNGLogo size={36} className="flex-shrink-0" />
                {!collapsed && (
                    <div className="animate-fade-in">
                        <h1 className="text-sm font-bold text-[var(--text-primary)] leading-tight">
                            OBD SuperStar
                        </h1>
                        <p className="text-[10px] text-[var(--text-tertiary)]">by Black &amp; Green</p>
                    </div>
                )}
            </div>

            {/* Nav items */}
            <nav className="px-3 py-4 space-y-1">
                {NAV_ITEMS.map((item) => {
                    const isActive = pathname === item.href;
                    const Icon = item.icon;
                    return (
                        <Link
                            key={item.href}
                            href={item.href}
                            onClick={() => setMobileOpen(false)}
                            className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group ${isActive
                                ? "bg-[var(--accent-subtle)] text-[var(--accent)] shadow-sm"
                                : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)]"
                                }`}
                            style={isActive ? { boxShadow: `0 1px 6px var(--accent-glow)` } : undefined}
                        >
                            <Icon
                                className={`w-4.5 h-4.5 flex-shrink-0 ${isActive
                                    ? "text-[var(--accent)]"
                                    : "text-[var(--text-tertiary)] group-hover:text-[var(--text-secondary)]"
                                    }`}
                            />
                            {!collapsed && (
                                <span className="animate-fade-in">{item.label}</span>
                            )}
                            {isActive && !collapsed && (
                                <div className="ml-auto w-1.5 h-1.5 rounded-full bg-[var(--accent)] animate-pulse" />
                            )}
                        </Link>
                    );
                })}

                {/* Admin Item */}
                {userRole === "admin" && (
                    <Link
                        href={ADMIN_NAV_ITEM.href}
                        onClick={() => setMobileOpen(false)}
                        className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 group mt-4 border border-[var(--warning)]/20 ${pathname.startsWith(ADMIN_NAV_ITEM.href)
                            ? "bg-[var(--warning)]/10 text-[var(--warning)] shadow-sm"
                            : "text-[var(--warning)]/70 hover:text-[var(--warning)] hover:bg-[var(--warning)]/10"
                            }`}
                    >
                        <ADMIN_NAV_ITEM.icon
                            className={`w-4.5 h-4.5 flex-shrink-0 ${pathname.startsWith(ADMIN_NAV_ITEM.href)
                                ? "text-[var(--warning)]"
                                : "text-[var(--warning)]/70 group-hover:text-[var(--warning)]"
                                }`}
                        />
                        {!collapsed && (
                            <span className="animate-fade-in">{ADMIN_NAV_ITEM.label}</span>
                        )}
                    </Link>
                )}
            </nav>

            {/* BNG Products */}
            <div className="flex-1 px-3 pb-2 overflow-y-auto">
                {!collapsed && (
                    <p className="px-3 mb-2 text-[9px] uppercase tracking-widest font-semibold text-[var(--text-tertiary)]">
                        BNG Products
                    </p>
                )}
                <div className="space-y-0.5">
                    {BNG_PRODUCT_LIST.map((product) => {
                        const Icon = product.icon;
                        const isProductActive = pathname === `/product/${product.id}`;
                        return (
                            <Link
                                key={product.id}
                                href={`/product/${product.id}`}
                                onClick={() => setMobileOpen(false)}
                                className={`flex items-center gap-3 px-3 py-2 rounded-xl text-xs font-medium transition-all duration-200 group ${isProductActive
                                        ? "bg-[var(--accent-subtle)] text-[var(--accent)]"
                                        : "text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)]"
                                    }`}
                            >
                                <Icon className={`w-3.5 h-3.5 flex-shrink-0 ${isProductActive
                                        ? "text-[var(--accent)]"
                                        : "text-[var(--text-tertiary)] group-hover:text-[var(--accent)]"
                                    }`} />
                                {!collapsed && (
                                    <span className="animate-fade-in truncate">{product.label}</span>
                                )}
                            </Link>
                        );
                    })}
                </div>
            </div>

            {/* Theme picker */}
            <div className="py-2 border-t border-[var(--card-border)]">
                <ThemePicker collapsed={collapsed} />
            </div>

            {/* Collapse toggle (desktop only) */}
            <div className="hidden lg:block px-3 py-3 border-t border-[var(--card-border)]">
                <button
                    onClick={() => setCollapsed(!collapsed)}
                    className="flex items-center justify-center w-full py-2 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)] transition-colors"
                >
                    {collapsed ? (
                        <ChevronRight className="w-4 h-4" />
                    ) : (
                        <ChevronLeft className="w-4 h-4" />
                    )}
                </button>
            </div>
        </div>
    );

    return (
        <>
            {/* Mobile hamburger */}
            <button
                onClick={() => setMobileOpen(true)}
                className="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-xl glass text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
            >
                <Menu className="w-5 h-5" />
            </button>

            {/* Mobile overlay */}
            {mobileOpen && (
                <div
                    className="lg:hidden fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Mobile sidebar */}
            <div
                className={`lg:hidden fixed inset-y-0 left-0 z-50 w-64 glass-strong transform transition-transform duration-300 ${mobileOpen ? "translate-x-0" : "-translate-x-full"
                    }`}
            >
                <button
                    onClick={() => setMobileOpen(false)}
                    className="absolute top-4 right-4 p-1.5 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-primary)] hover:bg-[var(--accent-subtle)] transition-colors"
                >
                    <X className="w-4 h-4" />
                </button>
                {navContent}
            </div>

            {/* Desktop sidebar */}
            <aside
                className={`hidden lg:flex flex-col fixed inset-y-0 left-0 z-30 glass-strong border-r border-[var(--card-border)] transition-all duration-300 ${collapsed ? "w-[72px]" : "w-56"
                    }`}
            >
                {navContent}
            </aside>

            {/* Spacer to push content */}
            <div
                className={`hidden lg:block flex-shrink-0 transition-all duration-300 ${collapsed ? "w-[72px]" : "w-56"
                    }`}
            />
        </>
    );
}
