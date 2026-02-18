"use client";

import { Megaphone, Phone, MessageSquare, Hash, Layers } from "lucide-react";

export interface PromotionType {
  id: string;
  name: string;
  icon: React.ReactNode;
  description: string;
  scriptGuidance: string;
}

export const PROMOTION_TYPES: PromotionType[] = [
  {
    id: "obd_standard",
    name: "OBD Campaign",
    icon: <Phone className="w-4 h-4" />,
    description: "Standard outbound dialer with IVR and DTMF",
    scriptGuidance:
      "Standard OBD promotional call. Hook (5s) + Body (15-18s) + CTA with DTMF (5-7s). Total under 30 seconds. Include fallback CTAs and polite closure.",
  },
  {
    id: "obd_named_cli",
    name: "OBD + Named CLI",
    icon: <Megaphone className="w-4 h-4" />,
    description: "OBD with verified business caller ID for 93% pickup",
    scriptGuidance:
      "OBD with Named CLI (caller sees business name). Since pickup rate is 93%+, focus on conversion quality over attention-grabbing. The caller already trusts the source. Hook can be warmer and more personal. Total under 30 seconds with DTMF CTA.",
  },
  {
    id: "ivr_flow",
    name: "IVR Menu Flow",
    icon: <Layers className="w-4 h-4" />,
    description: "Multi-level IVR with branching DTMF navigation",
    scriptGuidance:
      "Multi-level IVR flow with branching paths. Design a welcome message, then 3-4 DTMF options. Each option leads to a sub-menu or action. Include: main menu greeting, option descriptions, confirmation messages, and exit path. Total main menu under 20 seconds. Each sub-option under 15 seconds.",
  },
  {
    id: "sms_followup",
    name: "SMS + OBD Combo",
    icon: <MessageSquare className="w-4 h-4" />,
    description: "OBD script paired with follow-up SMS text",
    scriptGuidance:
      "Combined OBD + SMS campaign. Generate both: (1) A 30-second OBD script with hook/body/CTA, and (2) A follow-up SMS message (160 chars max) to be sent after the call. The SMS should reinforce the OBD message with a direct action link or USSD code. OBD CTA should mention 'we will also send you an SMS with details.'",
  },
  {
    id: "ussd_push",
    name: "USSD Push Promo",
    icon: <Hash className="w-4 h-4" />,
    description: "USSD push notification with subscription flow",
    scriptGuidance:
      "USSD push promotion script. Design a short, compelling USSD message (max 182 chars per screen) with clear options. Include: Screen 1 (hook + offer), Screen 2 (details + pricing), Screen 3 (confirmation). Each screen must have numbered options. Also generate a supporting OBD script that drives users to the USSD code.",
  },
];

interface PromotionTypeSelectProps {
  selected: string;
  onChange: (type: PromotionType) => void;
}

export default function PromotionTypeSelect({
  selected,
  onChange,
}: PromotionTypeSelectProps) {
  return (
    <div className="space-y-3">
      <label className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)]">
        <Megaphone className="w-4 h-4 text-[var(--accent)]" />
        Promotion Type
      </label>

      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
        {PROMOTION_TYPES.map((type) => {
          const isSelected = selected === type.id;
          return (
            <button
              key={type.id}
              onClick={() => onChange(type)}
              className={`group flex items-start gap-2.5 p-3 rounded-xl border text-left transition-all duration-200 ${
                isSelected
                  ? "border-[var(--accent)] bg-[var(--accent-subtle)]"
                  : "border-[var(--card-border)] hover:border-[var(--card-border-hover)] hover:bg-[var(--card-hover)]"
              }`}
              style={
                isSelected
                  ? { boxShadow: `0 2px 8px var(--accent-glow)` }
                  : undefined
              }
            >
              <div
                className={`p-1.5 rounded-lg flex-shrink-0 transition-colors ${
                  isSelected
                    ? "bg-[var(--accent)] text-white"
                    : "bg-[var(--input-bg)] text-[var(--text-tertiary)] group-hover:text-[var(--accent)]"
                }`}
              >
                {type.icon}
              </div>
              <div className="min-w-0">
                <p
                  className={`text-xs font-semibold leading-tight ${
                    isSelected
                      ? "text-[var(--accent)]"
                      : "text-[var(--text-primary)]"
                  }`}
                >
                  {type.name}
                </p>
                <p className="text-[10px] text-[var(--text-tertiary)] mt-0.5 line-clamp-2">
                  {type.description}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
