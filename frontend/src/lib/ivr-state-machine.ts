/**
 * IVR State Machine for the Call Simulator.
 * Pure TypeScript — no React dependency.
 * Manages audio playback, DTMF routing, and call flow.
 */

import type { AudioFile, Script } from "./types";

// ── Types ──

export interface IVRNode {
  id: string;
  label: string;
  audioUrl: string | null;
  autoAdvance: boolean;
  transitions: Record<string, string>; // DTMF key → next node id
  defaultNext: string | null;
  timeoutSeconds: number;
  timeoutNext: string | null;
}

export interface IVRFlow {
  nodes: Record<string, IVRNode>;
  entryNodeId: string;
}

export interface CallLogEntry {
  timestamp: number;
  elapsed: number; // ms since call start
  type: "call_start" | "call_end" | "audio_start" | "audio_end" | "dtmf" | "timeout" | "error" | "info";
  message: string;
  nodeId?: string;
  key?: string;
}

export interface IVRState {
  currentNodeId: string;
  currentLabel: string;
  status: "idle" | "ringing" | "playing" | "waiting_dtmf" | "ended";
  callLog: CallLogEntry[];
  callStartTime: number | null;
  callDurationMs: number;
}

// ── DTMF Tone Generator ──

const DTMF_FREQS: Record<string, [number, number]> = {
  "1": [697, 1209], "2": [697, 1336], "3": [697, 1477],
  "4": [770, 1209], "5": [770, 1336], "6": [770, 1477],
  "7": [852, 1209], "8": [852, 1336], "9": [852, 1477],
  "*": [941, 1209], "0": [941, 1336], "#": [941, 1477],
};

function playDTMFTone(key: string, durationMs = 120): void {
  const freqs = DTMF_FREQS[key];
  if (!freqs) return;
  try {
    const ctx = new AudioContext();
    const gain = ctx.createGain();
    gain.gain.value = 0.15;
    gain.connect(ctx.destination);
    for (const freq of freqs) {
      const osc = ctx.createOscillator();
      osc.type = "sine";
      osc.frequency.value = freq;
      osc.connect(gain);
      osc.start();
      osc.stop(ctx.currentTime + durationMs / 1000);
    }
    setTimeout(() => ctx.close(), durationMs + 50);
  } catch {
    // Web Audio API not available — silent fallback
  }
}

/**
 * Play a realistic phone ringing tone (two-tone burst pattern).
 * Uses Web Audio API — no autoplay restrictions since it's synthesized.
 * Returns a promise that resolves after the ring duration.
 */
function playRingTone(durationMs = 1500): Promise<void> {
  return new Promise((resolve) => {
    try {
      const ctx = new AudioContext();
      const gain = ctx.createGain();
      gain.gain.value = 0.08;
      gain.connect(ctx.destination);

      // US ring tone: 440 Hz + 480 Hz, 2s on / 4s off pattern
      // We play a shortened version: two quick ring bursts
      const ringBurst = (startTime: number, dur: number) => {
        for (const freq of [440, 480]) {
          const osc = ctx.createOscillator();
          osc.type = "sine";
          osc.frequency.value = freq;
          const burstGain = ctx.createGain();
          burstGain.gain.setValueAtTime(0.08, startTime);
          burstGain.gain.setValueAtTime(0, startTime + dur);
          osc.connect(burstGain);
          burstGain.connect(ctx.destination);
          osc.start(startTime);
          osc.stop(startTime + dur);
        }
      };

      // Two short ring bursts with a gap
      ringBurst(ctx.currentTime, 0.4);
      ringBurst(ctx.currentTime + 0.6, 0.4);

      setTimeout(() => {
        ctx.close().catch(() => {});
        resolve();
      }, durationMs);
    } catch {
      // Web Audio not available — just wait
      setTimeout(resolve, durationMs);
    }
  });
}

// ── Flow Builder ──

export function buildIVRFlow(
  audioFiles: AudioFile[],
  script: Script | null,
  sessionId: string,
): IVRFlow {
  const urlFor = (af: AudioFile) =>
    af.public_url || `/api/audio/${sessionId}/${af.file_name}`;

  // Normalize: work on a local copy to avoid mutating React state
  const normalized = audioFiles
    .filter((af) => af.file_name && !af.error)
    .map((af) => ({ ...af }));

  // Edge case: single audio file with unrecognized type → treat as "main"
  const knownTypes = new Set(["main", "fallback1", "fallback2", "closure"]);
  if (normalized.length === 1 && !knownTypes.has(normalized[0].type) && !normalized[0].type.startsWith("step_")) {
    normalized[0].type = "main";
  }

  const byType: Record<string, AudioFile> = {};
  for (const af of normalized) {
    byType[af.type] = af;
  }

  const hasSteps = Object.keys(byType).some((t) => t.startsWith("step_"));

  if (hasSteps) {
    return buildFlowScriptIVR(byType, urlFor);
  }
  return buildStandardIVR(byType, urlFor);
}

function buildFlowScriptIVR(
  byType: Record<string, AudioFile>,
  urlFor: (af: AudioFile) => string,
): IVRFlow {
  // Collect step_ types in order
  const stepKeys = Object.keys(byType)
    .filter((t) => t.startsWith("step_"))
    .sort(); // alphabetical: step_sub, step_thanks, step_welcome

  // Prioritize known order: welcome, sub/subscription, then rest, then thanks at end
  const ordered = sortStepKeys(stepKeys);

  const nodes: Record<string, IVRNode> = {};
  const nodeIds: string[] = [];

  for (const stepKey of ordered) {
    const nodeId = stepKey.replace("step_", "");
    const label = formatLabel(nodeId);
    nodes[nodeId] = {
      id: nodeId,
      label,
      audioUrl: urlFor(byType[stepKey]),
      autoAdvance: true,
      transitions: {},
      defaultNext: null,
      timeoutSeconds: 0,
      timeoutNext: null,
    };
    nodeIds.push(nodeId);
  }

  // Add "ended" node
  nodes["ended"] = {
    id: "ended",
    label: "Call Ended",
    audioUrl: null,
    autoAdvance: false,
    transitions: {},
    defaultNext: null,
    timeoutSeconds: 0,
    timeoutNext: null,
  };

  // Wire nodes: each audio node → wait_dtmf → next audio node
  for (let i = 0; i < nodeIds.length; i++) {
    const current = nodeIds[i];
    const next = nodeIds[i + 1] || "ended";

    if (i < nodeIds.length - 1) {
      // Add a DTMF wait node between audio nodes
      const waitId = `wait_after_${current}`;
      nodes[waitId] = {
        id: waitId,
        label: `Press a key to continue...`,
        audioUrl: null,
        autoAdvance: false,
        transitions: {
          "1": next,
          "2": next,
          "3": next,
          "*": next,
          "#": next,
        },
        defaultNext: null,
        timeoutSeconds: 10,
        timeoutNext: next, // auto-advance on timeout
      };
      nodes[current].defaultNext = waitId;
    } else {
      // Last audio node → ended
      nodes[current].defaultNext = "ended";
    }
  }

  return { nodes, entryNodeId: nodeIds[0] || "ended" };
}

function buildStandardIVR(
  byType: Record<string, AudioFile>,
  urlFor: (af: AudioFile) => string,
): IVRFlow {
  const nodes: Record<string, IVRNode> = {};

  // Ended node
  nodes["ended"] = {
    id: "ended",
    label: "Call Ended",
    audioUrl: null,
    autoAdvance: false,
    transitions: {},
    defaultNext: null,
    timeoutSeconds: 0,
    timeoutNext: null,
  };

  const hasMain = !!byType["main"];
  const hasFallback1 = !!byType["fallback1"];
  const hasFallback2 = !!byType["fallback2"];
  const hasClosure = !!byType["closure"];

  if (!hasMain) {
    // No audio at all — just end
    return { nodes, entryNodeId: "ended" };
  }

  // Main node
  nodes["main"] = {
    id: "main",
    label: "Main Script",
    audioUrl: urlFor(byType["main"]),
    autoAdvance: true,
    transitions: {},
    defaultNext: null,
    timeoutSeconds: 0,
    timeoutNext: null,
  };

  // Closure confirm node (when user presses a key to accept CTA)
  if (hasClosure) {
    nodes["closure"] = {
      id: "closure",
      label: "Confirmation",
      audioUrl: urlFor(byType["closure"]),
      autoAdvance: true,
      transitions: {},
      defaultNext: "ended",
      timeoutSeconds: 0,
      timeoutNext: null,
    };
  }

  // Fallback 1
  if (hasFallback1) {
    nodes["fallback1"] = {
      id: "fallback1",
      label: "Fallback 1",
      audioUrl: urlFor(byType["fallback1"]),
      autoAdvance: true,
      transitions: {},
      defaultNext: null,
      timeoutSeconds: 0,
      timeoutNext: null,
    };
  }

  // Fallback 2
  if (hasFallback2) {
    nodes["fallback2"] = {
      id: "fallback2",
      label: "Fallback 2",
      audioUrl: urlFor(byType["fallback2"]),
      autoAdvance: true,
      transitions: {},
      defaultNext: hasClosure ? "closure" : "ended",
      timeoutSeconds: 0,
      timeoutNext: null,
    };
  }

  // Wire the flow:
  // main → wait_dtmf_1
  //   key 1/2/3 → closure (user accepted CTA)
  //   timeout → fallback1 → wait_dtmf_2
  //     key 1/2/3 → closure
  //     timeout → fallback2 → closure → ended

  const closureOrEnd = hasClosure ? "closure" : "ended";

  // Edge case: only main audio — play straight through, no DTMF waits
  if (!hasFallback1 && !hasFallback2 && !hasClosure) {
    nodes["main"].defaultNext = "ended";
    return { nodes, entryNodeId: "main" };
  }

  if (hasFallback1 || hasFallback2) {
    // Wait after main
    nodes["wait_dtmf_1"] = {
      id: "wait_dtmf_1",
      label: "Waiting for key press...",
      audioUrl: null,
      autoAdvance: false,
      transitions: { "1": closureOrEnd, "2": closureOrEnd, "3": closureOrEnd },
      defaultNext: null,
      timeoutSeconds: 10,
      timeoutNext: hasFallback1 ? "fallback1" : (hasFallback2 ? "fallback2" : closureOrEnd),
    };
    nodes["main"].defaultNext = "wait_dtmf_1";

    if (hasFallback1) {
      if (hasFallback2) {
        // Wait after fallback1
        nodes["wait_dtmf_2"] = {
          id: "wait_dtmf_2",
          label: "Waiting for key press...",
          audioUrl: null,
          autoAdvance: false,
          transitions: { "1": closureOrEnd, "2": closureOrEnd, "3": closureOrEnd },
          defaultNext: null,
          timeoutSeconds: 10,
          timeoutNext: "fallback2",
        };
        nodes["fallback1"].defaultNext = "wait_dtmf_2";
      } else {
        nodes["fallback1"].defaultNext = closureOrEnd;
      }
    }
  } else {
    // No fallbacks — main → wait → closure/ended
    nodes["wait_dtmf_1"] = {
      id: "wait_dtmf_1",
      label: "Waiting for key press...",
      audioUrl: null,
      autoAdvance: false,
      transitions: { "1": closureOrEnd, "2": closureOrEnd, "3": closureOrEnd },
      defaultNext: null,
      timeoutSeconds: 10,
      timeoutNext: closureOrEnd,
    };
    nodes["main"].defaultNext = "wait_dtmf_1";
  }

  return { nodes, entryNodeId: "main" };
}

// ── Helpers ──

function sortStepKeys(keys: string[]): string[] {
  const priority: Record<string, number> = {
    step_welcome: 0,
    step_greeting: 0,
    step_intro: 1,
    step_sub: 2,
    step_subscription: 2,
    step_cta: 3,
    step_thanks: 4,
    step_thank: 4,
    step_confirmation: 4,
    step_closure: 5,
  };
  return [...keys].sort((a, b) => {
    const pa = priority[a] ?? 3;
    const pb = priority[b] ?? 3;
    if (pa !== pb) return pa - pb;
    return a.localeCompare(b);
  });
}

function formatLabel(nodeId: string): string {
  return nodeId
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

// ── State Machine ──

export class IVRStateMachine {
  private flow: IVRFlow;
  private state: IVRState;
  private audioElement: HTMLAudioElement | null = null;
  private timeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private audioTimeoutTimer: ReturnType<typeof setTimeout> | null = null;
  private durationTimer: ReturnType<typeof setInterval> | null = null;
  private onStateChange: (state: IVRState) => void;
  private preloaded: Map<string, HTMLAudioElement> = new Map();

  constructor(flow: IVRFlow, onStateChange: (state: IVRState) => void) {
    this.flow = flow;
    this.onStateChange = onStateChange;
    this.state = {
      currentNodeId: flow.entryNodeId,
      currentLabel: "",
      status: "idle",
      callLog: [],
      callStartTime: null,
      callDurationMs: 0,
    };
    this.preloadAudio();
  }

  private preloadAudio(): void {
    for (const node of Object.values(this.flow.nodes)) {
      if (node.audioUrl) {
        const audio = new Audio();
        audio.preload = "auto";
        audio.src = node.audioUrl;
        audio.load();
        this.preloaded.set(node.id, audio);
      }
    }
  }

  getState(): IVRState {
    return { ...this.state };
  }

  startCall(): void {
    const now = Date.now();
    this.state.callStartTime = now;
    this.state.callDurationMs = 0;
    this.state.status = "ringing";
    this.state.currentLabel = "Ringing...";
    this.log("call_start", "Call started");
    this.notify();

    // Play a synthesized ring tone (Web Audio API — no autoplay restriction).
    // Creating AudioContext in the gesture context also unlocks HTML5 Audio.
    playRingTone(1500).then(() => {
      if (this.state.status === "ended") return;
      this.playNode(this.flow.entryNodeId);
    });

    // Duration timer
    this.durationTimer = setInterval(() => {
      if (this.state.callStartTime && this.state.status !== "ended") {
        this.state.callDurationMs = Date.now() - this.state.callStartTime;
        this.notify();
      }
    }, 200);
  }

  handleDTMF(key: string): void {
    if (this.state.status !== "waiting_dtmf") return;

    playDTMFTone(key);

    const node = this.flow.nodes[this.state.currentNodeId];
    if (!node) return;

    const nextId = node.transitions[key];
    this.log("dtmf", `Key pressed: ${key}`, this.state.currentNodeId, key);

    if (nextId) {
      this.clearTimeout();
      this.transition(nextId);
    } else {
      this.log("info", `Key ${key} — no action mapped`);
      this.notify();
    }
  }

  hangUp(): void {
    this.stopAudio();
    this.clearTimeout();
    this.clearDurationTimer();
    this.state.status = "ended";
    this.state.currentLabel = "Call Ended";
    this.log("call_end", `Call ended — ${this.formatDuration()}`);
    this.notify();
  }

  destroy(): void {
    this.stopAudio();
    this.clearTimeout();
    this.clearAudioTimeout();
    this.clearDurationTimer();
    for (const audio of this.preloaded.values()) {
      audio.src = "";
    }
    this.preloaded.clear();
  }

  // ── Private ──

  private playNode(nodeId: string): void {
    const node = this.flow.nodes[nodeId];
    if (!node) {
      this.hangUp();
      return;
    }

    this.state.currentNodeId = nodeId;
    this.state.currentLabel = node.label;

    if (nodeId === "ended") {
      this.hangUp();
      return;
    }

    if (node.audioUrl) {
      this.state.status = "playing";
      this.log("audio_start", `Playing: ${node.label}`, nodeId);
      this.notify();

      // Use preloaded audio if available, else create new
      const audio = this.preloaded.get(nodeId) || new Audio(node.audioUrl);
      this.stopAudio();
      this.audioElement = audio;

      audio.currentTime = 0;
      // Safety timeout: skip node only if audio fails to load (not if it's playing fine)
      this.clearAudioTimeout();
      this.audioTimeoutTimer = setTimeout(() => {
        // Only skip if audio hasn't started playing (currentTime still 0 means it never loaded)
        if (audio.currentTime < 0.5 && audio.paused) {
          this.log("timeout", `Audio failed to load: ${node.label}`, nodeId);
          this.stopAudio();
          if (node.defaultNext) this.transition(node.defaultNext);
          else this.hangUp();
        }
        // If audio IS playing, don't interfere — let onended handle it
      }, 30000);
      audio.onended = () => {
        this.clearAudioTimeout();
        this.log("audio_end", `Finished: ${node.label}`, nodeId);
        if (node.autoAdvance && node.defaultNext) {
          this.transition(node.defaultNext);
        } else if (!node.autoAdvance) {
          this.state.status = "waiting_dtmf";
          this.state.currentLabel = node.label;
          this.notify();
          this.startTimeout(node);
        } else {
          // No defaultNext and not waiting — end
          this.hangUp();
        }
      };
      audio.onerror = () => {
        this.clearAudioTimeout();
        this.log("error", `Audio failed to load: ${node.label}`, nodeId);
        // Skip to next node
        if (node.defaultNext) this.transition(node.defaultNext);
        else this.hangUp();
      };
      audio.play().catch(() => {
        this.log("error", `Playback blocked: ${node.label}`, nodeId);
        if (node.defaultNext) this.transition(node.defaultNext);
        else this.hangUp();
      });
    } else {
      // Wait node (no audio)
      this.state.status = "waiting_dtmf";
      this.log("info", node.label, nodeId);
      this.notify();
      this.startTimeout(node);
    }
  }

  private transition(toNodeId: string): void {
    this.clearTimeout();
    this.playNode(toNodeId);
  }

  private startTimeout(node: IVRNode): void {
    if (node.timeoutSeconds > 0 && node.timeoutNext) {
      this.timeoutTimer = setTimeout(() => {
        this.log("timeout", `No input — advancing`, node.id);
        this.transition(node.timeoutNext!);
      }, node.timeoutSeconds * 1000);
    }
  }

  private stopAudio(): void {
    if (this.audioElement) {
      this.audioElement.onended = null;
      this.audioElement.onerror = null;
      this.audioElement.pause();
      this.audioElement = null;
    }
  }

  private clearTimeout(): void {
    if (this.timeoutTimer) {
      clearTimeout(this.timeoutTimer);
      this.timeoutTimer = null;
    }
  }

  private clearAudioTimeout(): void {
    if (this.audioTimeoutTimer) {
      clearTimeout(this.audioTimeoutTimer);
      this.audioTimeoutTimer = null;
    }
  }

  private clearDurationTimer(): void {
    if (this.durationTimer) {
      clearInterval(this.durationTimer);
      this.durationTimer = null;
    }
  }

  private log(type: CallLogEntry["type"], message: string, nodeId?: string, key?: string): void {
    this.state.callLog.push({
      timestamp: Date.now(),
      elapsed: this.state.callStartTime ? Date.now() - this.state.callStartTime : 0,
      type,
      message,
      nodeId,
      key,
    });
  }

  private formatDuration(): string {
    const s = Math.round(this.state.callDurationMs / 1000);
    const m = Math.floor(s / 60);
    const sec = s % 60;
    return `${m}:${String(sec).padStart(2, "0")}`;
  }

  private notify(): void {
    this.onStateChange({ ...this.state, callLog: [...this.state.callLog] });
  }
}
