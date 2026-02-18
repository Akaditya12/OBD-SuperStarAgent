"use client";

interface BNGLogoProps {
  size?: number;
  className?: string;
}

export default function BNGLogo({ size = 36, className = "" }: BNGLogoProps) {
  const fontSize = Math.round(size * 0.38);
  const rx = Math.round(size * 0.28);
  const textY = size * 0.65;

  return (
    <div
      className={`flex items-center justify-center font-extrabold text-white shrink-0 ${className}`}
      style={{
        width: size,
        height: size,
        borderRadius: rx,
        fontSize,
        letterSpacing: "-0.5px",
        background: "linear-gradient(135deg, var(--accent, #5c7cfa), #cc5de8)",
        lineHeight: 1,
      }}
    >
      BNG
    </div>
  );
}
