import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Force-download a file from a same-origin URL.
 * Fetches as blob (with auth cookies) and triggers browser download dialog
 * so we control the filename. Falls back to a new-tab navigation on failure
 * (the browser will still send cookies and use the server's filename).
 */
export async function forceDownload(url: string, filename: string) {
  try {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) {
      // Don't save the error body as the requested file. Fall through to new-tab.
      throw new Error(`download failed: ${res.status}`);
    }
    const blob = await res.blob();
    const blobUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = blobUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(blobUrl);
  } catch {
    window.open(url, "_blank");
  }
}

/** Sanitize a string for use in a filename (keeps letters, digits, _, -). */
export function sanitizeFilename(s: string): string {
  return (s || "audio")
    .replace(/[^a-zA-Z0-9_-]+/g, "_")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "")
    || "audio";
}
