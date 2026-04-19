"use client";

import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from "react";

export interface SelectedVoice {
  voice_id: string;
  name: string;
  description?: string;
  labels?: { accent?: string; gender?: string; age?: string };
  preview_url?: string | null;
  best_for_regions?: string[];
}

interface VoiceContextValue {
  selectedVoice: SelectedVoice | null;
  setSelectedVoice: (voice: SelectedVoice | null) => void;
}

const VoiceContext = createContext<VoiceContextValue>({
  selectedVoice: null,
  setSelectedVoice: () => {},
});

const STORAGE_KEY = "obd_selected_voice";

export function VoiceProvider({ children }: { children: ReactNode }) {
  const [selectedVoice, setSelectedVoiceState] = useState<SelectedVoice | null>(null);

  // Load from localStorage on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setSelectedVoiceState(JSON.parse(stored));
      }
    } catch {
      // ignore parse errors
    }
  }, []);

  const setSelectedVoice = useCallback((voice: SelectedVoice | null) => {
    setSelectedVoiceState(voice);
    try {
      if (voice) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(voice));
      } else {
        localStorage.removeItem(STORAGE_KEY);
      }
    } catch {
      // ignore storage errors
    }
  }, []);

  return (
    <VoiceContext.Provider value={{ selectedVoice, setSelectedVoice }}>
      {children}
    </VoiceContext.Provider>
  );
}

export function useVoice(): VoiceContextValue {
  return useContext(VoiceContext);
}
