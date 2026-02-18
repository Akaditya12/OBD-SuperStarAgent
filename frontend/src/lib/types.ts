/**
 * Shared types for the OBD SuperStar Agent frontend.
 * These mirror the JSON structures returned by the backend pipeline.
 */

export interface Script {
  variant_id: number;
  theme: string;
  language: string;
  hook: string;
  body: string;
  cta: string;
  fallback_1: string;
  fallback_2: string;
  polite_closure: string;
  full_script: string;
  word_count: number;
  estimated_duration_seconds: number;
  audio_tags_used?: string[];
}

export interface ScriptsResult {
  scripts: Script[];
  language_used: string;
  creative_rationale: string;
}

export interface EvaluationConsensus {
  ranking: number[];
  critical_improvements: string[];
  revision_instructions: string;
  best_variant_id: number;
  overall_assessment: string;
}

export interface EvaluationResult {
  evaluations: unknown[];
  consensus: EvaluationConsensus;
}

export interface VoiceSettings {
  stability: number;
  similarity_boost: number;
  style: number;
  speed: number;
}

export interface ElevenLabsApiParams {
  model_id: string;
  output_format: string;
  voice_id: string;
  voice_settings: {
    stability: number;
    similarity_boost: number;
    style: number;
    use_speaker_boost: boolean;
  };
  sample_api_call: string;
}

export interface VoiceSelection {
  selected_voice: {
    voice_id: string;
    name: string;
    description: string;
    language: string;
    gender: string;
    age: string;
    accent: string;
    preview_url?: string;
  };
  voice_settings: VoiceSettings;
  elevenlabs_api_params?: ElevenLabsApiParams;
  rationale: string;
  alternative_voices?: {
    voice_id: string;
    name: string;
    reason: string;
    preview_url?: string;
  }[];
  audio_production_notes?: string;
}

export interface AudioFile {
  file_name: string;
  file_path?: string;
  file_size_bytes?: number;
  variant_id: number;
  type: string;
  theme?: string;
  voice_id?: string;
  model?: string;
  error?: string;
}

export interface AudioResult {
  session_id: string;
  session_dir: string;
  tts_engine?: "elevenlabs" | "edge-tts";
  voice_used: {
    voice_id: string;
    name: string;
    settings: VoiceSettings;
  };
  audio_files: AudioFile[];
  failed_files?: AudioFile[];
  summary: {
    total_generated: number;
    total_failed: number;
    variants_count: number;
    has_background_music?: boolean;
  };
}

export interface PipelineResult {
  session_id: string;
  product_brief?: Record<string, unknown>;
  market_analysis?: Record<string, unknown>;
  initial_scripts?: ScriptsResult;
  evaluation_round_1?: EvaluationResult;
  revised_scripts_round_1?: ScriptsResult;
  final_scripts?: ScriptsResult;
  voice_selection?: VoiceSelection;
  audio?: AudioResult;
  error?: string;
}

export interface WsProgressMessage {
  agent: string;
  status: "started" | "completed" | "error" | "done";
  message: string;
  data?: Record<string, unknown>;
  session_id?: string;
  result?: PipelineResult;
}

export interface Campaign {
  id: string;
  name: string;
  created_by: string;
  created_at: string;
  country: string;
  telco: string;
  language: string;
  script_count: number;
  has_audio: boolean;
}

export interface CampaignDetail extends Campaign {
  result: PipelineResult;
}

// ── Collaboration Types ──

export interface Comment {
  id: string;
  campaign_id: string;
  username: string;
  text: string;
  created_at: string;
}

export interface PresenceUser {
  username: string;
  connected_at: number;
  last_active: number;
  viewing_campaign: string | null;
  color: string;
}

export interface CollaborationEvent {
  id: string;
  type: "campaign_created" | "comment_added" | "user_joined" | "user_left";
  username: string;
  campaign_id?: string;
  campaign_name?: string;
  detail?: string;
  timestamp: number;
}
