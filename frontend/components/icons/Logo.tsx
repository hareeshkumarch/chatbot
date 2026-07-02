interface LogoMarkProps {
  className?: string;
  animated?: boolean;
  spin?: boolean;
}

export function LogoMark({ className, animated = false, spin = false }: LogoMarkProps) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={`${className ?? ""} ${spin ? "animate-logo-spin" : ""}`.trim()}
      role="img"
      aria-label="Enterprise AI"
    >
      <path
        d="M 16 3 L 27.26 9.5 L 27.26 22.5 L 16 29 L 4.74 22.5 L 4.74 9.5 Z"
        stroke="#2F3EE0"
        strokeWidth="2"
        strokeLinejoin="round"
      />
      <path d="M 16 9.5 L 21.63 12.75 L 21.63 19.25 L 16 22.5 L 10.37 19.25 L 10.37 12.75 Z" fill="#2F3EE0" />
      <path
        d="M 16 9.5 L 21.63 12.75 L 16 16 Z"
        fill="#1B8C6F"
        className={animated ? "animate-signal-pulse" : undefined}
      />
    </svg>
  );
}

interface LogoProps {
  className?: string;
  markClassName?: string;
  textClassName?: string;
  animated?: boolean;
}

export function Logo({ className, markClassName = "h-8 w-8", textClassName = "text-lg", animated = false }: LogoProps) {
  return (
    <span className={`inline-flex items-center gap-2 ${className ?? ""}`}>
      <LogoMark className={markClassName} animated={animated} />
      <span className={`font-display font-medium tracking-tight text-ink ${textClassName}`}>Enterprise AI</span>
    </span>
  );
}
