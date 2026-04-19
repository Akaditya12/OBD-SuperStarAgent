"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import VoiceLibrary from "@/components/VoiceLibrary";

export default function VoiceLibraryPage() {
  const router = useRouter();
  const [authChecked, setAuthChecked] = useState(false);

  useEffect(() => {
    fetch("/api/auth/me")
      .then((r) => r.json())
      .then((d) => { if (d.authenticated) setAuthChecked(true); else router.push("/login"); })
      .catch(() => router.push("/login"));
  }, [router]);

  if (!authChecked) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return <VoiceLibrary />;
}
