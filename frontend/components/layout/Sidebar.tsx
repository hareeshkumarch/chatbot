"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { MessageSquare, FileText, Plug, BarChart3, Settings, History, PanelLeftClose, PanelLeftOpen } from "lucide-react";
import { LogoMark } from "@/components/icons/Logo";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/app", label: "Chat", icon: MessageSquare },
  { href: "/app/history", label: "History", icon: History },
  { href: "/app/documents", label: "Documents", icon: FileText },
  { href: "/app/connectors", label: "Connectors", icon: Plug },
  { href: "/app/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/app/settings", label: "Settings", icon: Settings },
];

const ITEM_HEIGHT = 44;
const COLLAPSE_STORAGE_KEY = "sidebar-collapsed";

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();
  const isMobileDrawer = Boolean(onNavigate);
  const [storedCollapsed, setStoredCollapsed] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const collapsed = !isMobileDrawer && storedCollapsed;

  useEffect(() => {
    setStoredCollapsed(window.localStorage.getItem(COLLAPSE_STORAGE_KEY) === "true");
    setHydrated(true);
  }, []);

  const toggleCollapsed = () => {
    const next = !storedCollapsed;
    setStoredCollapsed(next);
    window.localStorage.setItem(COLLAPSE_STORAGE_KEY, String(next));
  };

  const activeIndex = NAV_ITEMS.findIndex((item) => (item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href)));

  return (
    <aside
      className={cn(
        "flex h-screen shrink-0 flex-col border-r border-line bg-surface transition-[width] duration-150 ease-out",
        collapsed ? "w-16" : "w-56",
        !hydrated && "invisible",
      )}
    >
      <div className={cn("flex items-center gap-2 px-5 py-5", collapsed && "justify-center px-0")}>
        <Link href="/" onClick={onNavigate} className={cn("flex items-center gap-2 transition-opacity hover:opacity-80", collapsed && "justify-center")}>
          <LogoMark className="h-6 w-6 shrink-0" animated />
          {!collapsed && <span className="font-display text-sm font-medium tracking-tight text-ink">Enterprise AI</span>}
        </Link>
      </div>

      <nav className={cn("relative flex-1 pt-2", collapsed ? "px-2" : "px-3")}>
        {activeIndex >= 0 && !collapsed && (
          <div
            className="absolute left-3 w-0.5 rounded-full bg-route transition-transform duration-200 ease-out"
            style={{ height: ITEM_HEIGHT - 12, transform: `translateY(${activeIndex * ITEM_HEIGHT + 6}px)` }}
          />
        )}
        <ul className="flex flex-col gap-0.5">
          {NAV_ITEMS.map((item) => {
            const isActive = item.href === "/app" ? pathname === "/app" : pathname.startsWith(item.href);
            const Icon = item.icon;
            const link = (
              <Link
                href={item.href}
                onClick={onNavigate}
                className={cn(
                  "flex h-full items-center gap-3 rounded-sm text-sm transition-colors duration-150",
                  collapsed ? "justify-center px-0" : "pl-4 pr-3",
                  isActive ? "bg-route-soft text-route" : "text-ink-muted hover:bg-surface-sunken hover:text-ink",
                )}
              >
                <Icon className="h-4 w-4 shrink-0" strokeWidth={1.75} />
                {!collapsed && item.label}
              </Link>
            );
            return (
              <li key={item.href} style={{ height: ITEM_HEIGHT }}>
                {collapsed ? (
                  <Tooltip content={item.label} side="right" className="block h-full w-full">
                    {link}
                  </Tooltip>
                ) : (
                  link
                )}
              </li>
            );
          })}
        </ul>
      </nav>

      <div className={cn("border-t border-line", collapsed ? "px-2 py-3" : "px-4 py-4")}>
        {!collapsed && <p className="mb-2 font-mono text-[11px] uppercase tracking-wide text-ink-faint">Default Workspace</p>}
        {!isMobileDrawer && (
          <Tooltip content={collapsed ? "Expand sidebar" : "Collapse sidebar"} side="right" className={collapsed ? "flex w-full justify-center" : "block"}>
            <button
              type="button"
              onClick={toggleCollapsed}
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              className={cn(
                "flex h-8 items-center gap-2 rounded-sm text-ink-faint transition-colors duration-150 hover:bg-surface-sunken hover:text-ink",
                collapsed ? "w-8 justify-center" : "w-full px-2 text-xs",
              )}
            >
              {collapsed ? <PanelLeftOpen className="h-4 w-4" strokeWidth={1.75} /> : <PanelLeftClose className="h-4 w-4" strokeWidth={1.75} />}
              {!collapsed && "Collapse"}
            </button>
          </Tooltip>
        )}
      </div>
    </aside>
  );
}
