import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "OBD SuperStar Agent",
  description:
    "AI-powered multi-agent system for generating OBD promotional scripts and audio",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen antialiased">{children}</body>
    </html>
  );
}
