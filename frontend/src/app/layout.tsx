import type { Metadata } from "next";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import ToastProvider from "@/components/ToastProvider";
import ThemeProvider from "@/components/ThemeProvider";
import { VoiceProvider } from "@/components/VoiceContext";

export const metadata: Metadata = {
  title: "OBD SuperStar Agent — blackNgreen AI Campaign Generator",
  description:
    "blackNgreen AI-powered multi-agent system for generating culturally-relevant OBD promotional scripts and audio recordings for telecom operators across 100+ countries.",
  keywords: [
    "blackNgreen",
    "BNG",
    "OBD",
    "AI",
    "scripts",
    "audio",
    "telecom",
    "marketing",
    "EVA",
    "SmartConnect",
    "Call Signature",
    "Magic Voice",
  ],
  openGraph: {
    title: "OBD SuperStar Agent — by blackNgreen",
    description:
      "AI-powered OBD campaign generation for telecom operators. Create scripts, audio, and promotions for EVA, SmartConnect, Call Signature, and more.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#0a0a12" />
      </head>
      <body className="antialiased min-h-screen">
        <ThemeProvider>
          <ToastProvider>
            <VoiceProvider>
              <div className="flex min-h-screen">
                <Sidebar />
                <main className="flex-1 min-w-0">{children}</main>
              </div>
            </VoiceProvider>
          </ToastProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
