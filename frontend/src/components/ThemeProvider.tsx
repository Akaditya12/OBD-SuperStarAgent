"use client";

import {
  createContext,
  useContext,
  useState,
  useEffect,
  useCallback,
  type ReactNode,
} from "react";

export type ThemeId = "midnight" | "ocean" | "ember" | "forest" | "lavender" | "light";

export interface ThemeDefinition {
  id: ThemeId;
  label: string;
  preview: { bg: string; accent: string; card: string };
}

export const THEMES: ThemeDefinition[] = [
  {
    id: "midnight",
    label: "Midnight",
    preview: { bg: "#0a0a12", accent: "#5c7cfa", card: "#111119" },
  },
  {
    id: "ocean",
    label: "Ocean",
    preview: { bg: "#0a1628", accent: "#22d3ee", card: "#0f1f38" },
  },
  {
    id: "ember",
    label: "Ember",
    preview: { bg: "#140a0a", accent: "#f97316", card: "#1c1010" },
  },
  {
    id: "forest",
    label: "Forest",
    preview: { bg: "#0a120a", accent: "#22c55e", card: "#0f1a0f" },
  },
  {
    id: "lavender",
    label: "Lavender",
    preview: { bg: "#100a18", accent: "#a78bfa", card: "#161022" },
  },
  {
    id: "light",
    label: "Light",
    preview: { bg: "#f8f9fc", accent: "#4c6ef5", card: "#ffffff" },
  },
];

interface ThemeContextValue {
  theme: ThemeId;
  setTheme: (id: ThemeId) => void;
  themes: ThemeDefinition[];
}

const ThemeContext = createContext<ThemeContextValue>({
  theme: "midnight",
  setTheme: () => {},
  themes: THEMES,
});

export function useTheme() {
  return useContext(ThemeContext);
}

const STORAGE_KEY = "obd-theme";

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemeId>("midnight");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as ThemeId | null;
    if (stored && THEMES.some((t) => t.id === stored)) {
      setThemeState(stored);
    }
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!mounted) return;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem(STORAGE_KEY, theme);

    // Update meta theme-color for mobile browsers
    const meta = document.querySelector('meta[name="theme-color"]');
    const def = THEMES.find((t) => t.id === theme);
    if (meta && def) {
      meta.setAttribute("content", def.preview.bg);
    }
  }, [theme, mounted]);

  const setTheme = useCallback((id: ThemeId) => {
    setThemeState(id);
  }, []);

  // Prevent flash of wrong theme
  if (!mounted) {
    return <>{children}</>;
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}
