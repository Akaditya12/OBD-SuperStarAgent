"use client";

import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Phone } from "lucide-react";
import CampaignSelector from "@/components/call-simulator/CampaignSelector";
import PhoneUI from "@/components/call-simulator/PhoneUI";
import CallLog from "@/components/call-simulator/CallLog";
import { buildIVRFlow, IVRStateMachine } from "@/lib/ivr-state-machine";
import type { IVRState } from "@/lib/ivr-state-machine";
import type { CampaignDetail, AudioFile, Script } from "@/lib/types";

const INITIAL_STATE: IVRState = {
  currentNodeId: "",
  currentLabel: "",
  status: "idle",
  callLog: [],
  callStartTime: null,
  callDurationMs: 0,
};

export default function CallSimulatorPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const initialCampaignId = searchParams.get("campaign") || undefined;
  const [authChecked, setAuthChecked] = useState(false);

  // Campaign data
  const [campaignDetail, setCampaignDetail] = useState<CampaignDetail | null>(null);
  const [variantId, setVariantId] = useState<number>(1);

  // IVR state
  const [ivrState, setIvrState] = useState<IVRState>(INITIAL_STATE);
  const machineRef = useRef<IVRStateMachine | null>(null);

  // Auth check
  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((d) => { if (d.authenticated) setAuthChecked(true); else router.push("/login"); })
      .catch(() => router.push("/login"));
  }, [router]);

  // Cleanup machine on unmount
  useEffect(() => {
    return () => {
      machineRef.current?.destroy();
    };
  }, []);

  const handleCampaignReady = useCallback((detail: CampaignDetail, vid: number) => {
    // Stop any running call
    if (machineRef.current) {
      machineRef.current.destroy();
      machineRef.current = null;
    }
    setCampaignDetail(detail);
    setVariantId(vid);
    setIvrState(INITIAL_STATE);
  }, []);

  const handleStartCall = useCallback(() => {
    if (!campaignDetail) return;

    const audioFiles: AudioFile[] = campaignDetail.result?.audio?.audio_files || [];
    const variantAudio = audioFiles.filter((af) => af.variant_id === variantId && !af.error);
    const sessionId = campaignDetail.result?.audio?.session_id || campaignDetail.result?.session_id || campaignDetail.id;

    // Edge case: zero audio — log error instead of silent no-op
    if (variantAudio.length === 0) {
      setIvrState((prev) => ({
        ...prev,
        status: "ended",
        currentLabel: "No Audio",
        callLog: [
          ...prev.callLog,
          {
            timestamp: Date.now(),
            elapsed: 0,
            type: "error" as const,
            message: "No audio files found for this variant. Generate audio first.",
          },
        ],
      }));
      return;
    }

    // Find the matching script for context
    const scripts: Script[] =
      campaignDetail.result?.final_scripts?.scripts ||
      campaignDetail.result?.revised_scripts_round_1?.scripts ||
      campaignDetail.result?.initial_scripts?.scripts ||
      [];
    const script = scripts.find((s) => s.variant_id === variantId) || null;

    // Destroy previous machine
    machineRef.current?.destroy();

    // Build flow and create machine
    const flow = buildIVRFlow(variantAudio, script, sessionId);
    const machine = new IVRStateMachine(flow, (state) => {
      setIvrState(state);
    });
    machineRef.current = machine;
    machine.startCall();
  }, [campaignDetail, variantId]);

  const handleKeyPress = useCallback((key: string) => {
    machineRef.current?.handleDTMF(key);
  }, []);

  const handleHangUp = useCallback(() => {
    machineRef.current?.hangUp();
  }, []);

  const handleClearLog = useCallback(() => {
    setIvrState((prev) => ({ ...prev, callLog: [] }));
  }, []);

  // Restart = same as start call (destroys previous, builds fresh)
  const handleRestart = useCallback(() => {
    handleStartCall();
  }, [handleStartCall]);

  const isCallActive = ivrState.status !== "idle" && ivrState.status !== "ended";
  const canStart = !!campaignDetail && (ivrState.status === "idle" || ivrState.status === "ended");

  // Derive campaign name + variant label for phone header
  const campaignName = campaignDetail?.name || undefined;
  const variantLabel = variantId ? `V${variantId}` : undefined;

  // Estimate total call duration from script
  const estimatedDurationSec = useMemo(() => {
    if (!campaignDetail) return undefined;
    const scripts: Script[] =
      campaignDetail.result?.final_scripts?.scripts ||
      campaignDetail.result?.revised_scripts_round_1?.scripts ||
      campaignDetail.result?.initial_scripts?.scripts ||
      [];
    const script = scripts.find((s) => s.variant_id === variantId);
    if (script?.estimated_duration_seconds) return Math.round(script.estimated_duration_seconds);
    // Rough estimate: word count / 2.5 words per second
    const text = script?.full_script || "";
    const wordCount = text.split(/\s+/).filter(Boolean).length;
    return wordCount > 0 ? Math.round(wordCount / 2.5) : undefined;
  }, [campaignDetail, variantId]);

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[var(--background)] p-6">
      <div className="max-w-6xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-[var(--accent-subtle)]">
            <Phone className="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-[var(--text-primary)]">Call Simulator</h1>
            <p className="text-xs text-[var(--text-tertiary)]">
              Test your campaign audio in a simulated IVR call environment
            </p>
          </div>
        </div>

        {/* Main layout */}
        <div className="grid grid-cols-1 lg:grid-cols-[280px_1fr_300px] gap-6 items-start">
          {/* Left: Campaign selector */}
          <CampaignSelector
            onCampaignReady={handleCampaignReady}
            disabled={isCallActive}
            currentNodeId={ivrState.status !== "idle" ? ivrState.currentNodeId : undefined}
            initialCampaignId={initialCampaignId}
          />

          {/* Center: Phone */}
          <div className="flex justify-center py-4">
            <PhoneUI
              ivrState={ivrState}
              isCallActive={isCallActive}
              canStart={canStart}
              onKeyPress={handleKeyPress}
              onStartCall={handleStartCall}
              onHangUp={handleHangUp}
              campaignName={campaignName}
              variantLabel={variantLabel}
              onRestart={handleRestart}
              estimatedDurationSec={estimatedDurationSec}
            />
          </div>

          {/* Right: Call log */}
          <CallLog
            entries={ivrState.callLog}
            onClear={handleClearLog}
          />
        </div>
      </div>
    </div>
  );
}
