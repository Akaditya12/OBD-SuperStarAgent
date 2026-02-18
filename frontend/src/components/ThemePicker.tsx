"use client";

import { useState } from "react";
import { Palette, Check, ChevronDown, ChevronUp } from "lucide-react";
import { useTheme, type ThemeId } from "./ThemeProvider";

export default function ThemePicker({ collapsed }: { collapsed?: boolean }) {
  const { theme, setTheme, themes } = useTheme();
  const [open, setOpen] = useState(false);

  const current = themes.find((t) => t.id === theme);

  if (collapsed) {
    return (
      <button
        onClick={() => setOpen(!open)}
        className="relative flex items-center justify-center w-full py-2 rounded-lg text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)] transition-colors"
        title="Change theme"
      >
        <Palette className="w-4 h-4" />
        {open && (
          <div className="absolute left-full ml-2 bottom-0 z-50 p-2 rounded-xl bg-[var(--card)] border border-[var(--card-border)] shadow-2xl animate-scale-in min-w-[180px]">
            <p className="text-[10px] font-medium text-[var(--text-tertiary)] uppercase tracking-wider px-2 mb-2">
              Theme
            </p>
            <div className="space-y-0.5">
              {themes.map((t) => (
                <ThemeOption
                  key={t.id}
                  themeId={t.id}
                  label={t.label}
                  bg={t.preview.bg}
                  accent={t.preview.accent}
                  card={t.preview.card}
                  isActive={theme === t.id}
                  onClick={() => {
                    setTheme(t.id);
                    setOpen(false);
                  }}
                />
              ))}
            </div>
          </div>
        )}
      </button>
    );
  }

  return (
    <div className="px-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center justify-between w-full px-3 py-2 rounded-xl text-sm text-[var(--text-tertiary)] hover:text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)] transition-all"
      >
        <div className="flex items-center gap-2.5">
          <Palette className="w-4 h-4" />
          <span className="text-xs font-medium">{current?.label || "Theme"}</span>
        </div>
        <div className="flex items-center gap-2">
          <div
            className="w-3 h-3 rounded-full ring-1 ring-white/10"
            style={{ background: current?.preview.accent }}
          />
          {open ? (
            <ChevronUp className="w-3 h-3" />
          ) : (
            <ChevronDown className="w-3 h-3" />
          )}
        </div>
      </button>

      {open && (
        <div className="mt-1 p-2 rounded-xl bg-[var(--card)] border border-[var(--card-border)] shadow-lg animate-scale-in">
          <div className="space-y-0.5">
            {themes.map((t) => (
              <ThemeOption
                key={t.id}
                themeId={t.id}
                label={t.label}
                bg={t.preview.bg}
                accent={t.preview.accent}
                card={t.preview.card}
                isActive={theme === t.id}
                onClick={() => {
                  setTheme(t.id);
                  setOpen(false);
                }}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ThemeOption({
  label,
  bg,
  accent,
  card,
  isActive,
  onClick,
}: {
  themeId: ThemeId;
  label: string;
  bg: string;
  accent: string;
  card: string;
  isActive: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2.5 w-full px-2.5 py-2 rounded-lg text-left transition-all ${
        isActive
          ? "bg-[var(--accent-subtle)] text-[var(--text-primary)]"
          : "text-[var(--text-secondary)] hover:bg-[var(--accent-subtle)] hover:text-[var(--text-primary)]"
      }`}
    >
      {/* Mini preview swatch */}
      <div
        className="w-6 h-6 rounded-md flex-shrink-0 overflow-hidden border border-white/10 shadow-sm"
        style={{ background: bg }}
      >
        <div className="flex h-full">
          <div className="w-1/2" style={{ background: card, opacity: 0.9 }} />
          <div className="w-1/2 flex items-center justify-center">
            <div
              className="w-2 h-2 rounded-full"
              style={{ background: accent }}
            />
          </div>
        </div>
      </div>

      <span className="text-xs font-medium flex-1">{label}</span>

      {isActive && <Check className="w-3.5 h-3.5 text-[var(--accent)]" />}
    </button>
  );
}
