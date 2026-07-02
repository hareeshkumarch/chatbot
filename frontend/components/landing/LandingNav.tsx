"use client";

import { useState } from "react";
import Link from "next/link";
import { ArrowRight, Menu, X } from "lucide-react";
import { Logo } from "@/components/icons/Logo";
import { useScrollSpy } from "@/hooks/useScrollSpy";
import { LANDING_SHELL } from "@/lib/constants/landing";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "capabilities", label: "Capabilities" },
  { href: "routing", label: "How it works" },
  { href: "architecture", label: "System" },
  { href: "reports", label: "Reports" },
];

export function LandingNav() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const activeId = useScrollSpy(LINKS.map((l) => l.href));

  return (
    <header className="sticky top-0 z-30 border-b border-line bg-canvas">
      <div className={cn("flex h-16 items-center justify-between", LANDING_SHELL)}>
        <Logo />
        <nav className="hidden items-center gap-8 md:flex">
          {LINKS.map((link) => (
            <a
              key={link.href}
              href={`#${link.href}`}
              className={cn(
                "text-sm transition-colors",
                activeId === link.href ? "text-route" : "text-ink-muted hover:text-ink",
              )}
            >
              {link.label}
            </a>
          ))}
        </nav>
        <div className="flex items-center gap-2">
          <Link
            href="/app"
            className="hidden items-center gap-1.5 rounded-sm bg-ink px-4 py-2 text-sm font-medium text-canvas transition-opacity hover:opacity-90 sm:flex"
          >
            Launch app
            <ArrowRight className="h-3.5 w-3.5" strokeWidth={2} />
          </Link>
          <button
            type="button"
            onClick={() => setMobileOpen((prev) => !prev)}
            aria-label={mobileOpen ? "Close menu" : "Open menu"}
            className="flex h-9 w-9 items-center justify-center rounded-sm text-ink md:hidden"
          >
            {mobileOpen ? <X className="h-5 w-5" strokeWidth={1.75} /> : <Menu className="h-5 w-5" strokeWidth={1.75} />}
          </button>
        </div>
      </div>

      {mobileOpen && (
        <div className={cn("animate-slide-fade-in border-t border-line bg-canvas py-4 md:hidden", LANDING_SHELL)}>
          <nav className="flex flex-col gap-4">
            {LINKS.map((link) => (
              <a key={link.href} href={`#${link.href}`} onClick={() => setMobileOpen(false)} className="text-sm text-ink-muted hover:text-ink">
                {link.label}
              </a>
            ))}
            <Link
              href="/app"
              className="mt-2 flex items-center justify-center gap-1.5 rounded-sm bg-ink px-4 py-2.5 text-sm font-medium text-canvas"
            >
              Launch app
              <ArrowRight className="h-3.5 w-3.5" strokeWidth={2} />
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
