"use client";

import { Megaphone, Phone, MessageSquare } from "lucide-react";

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
    id: "sms_followup",
    name: "SMS + OBD Combo",
    icon: <MessageSquare className="w-4 h-4" />,
    description: "OBD script paired with follow-up SMS text",
    scriptGuidance:
      "Combined OBD + SMS campaign. Generate both: (1) A 30-second OBD script with hook/body/CTA, and (2) A follow-up SMS message (160 chars max) to be sent after the call. The SMS should reinforce the OBD message with a direct action link or USSD code. OBD CTA should mention 'we will also send you an SMS with details.'",
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

      <div className="grid grid-cols-2 gap-2">
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
