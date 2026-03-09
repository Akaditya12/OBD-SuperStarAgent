"use client";

interface BNGLogoProps {
  size?: number;
  className?: string;
}

export default function BNGLogo({ size = 36, className = "" }: BNGLogoProps) {
  return (
    <img
      src="/bng-logo.png"
      alt="blackNgreen"
      width={size}
      height={size}
      className={`object-contain shrink-0 rounded-lg ${className}`}
      style={{
        width: size,
        height: size,
      }}
    />
  );
}
