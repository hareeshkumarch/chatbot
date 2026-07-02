"use client";

import { useEffect, useRef, useState } from "react";
import { ChevronDown } from "lucide-react";
import { cn } from "@/lib/utils";

interface DropdownOption {
  value: string;
  label: string;
  description?: string;
  icon?: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  group?: string;
}

interface DropdownProps {
  value: string | null;
  onChange: (value: string) => void;
  options: DropdownOption[];
  placeholder?: string;
  className?: string;
}

export function Dropdown({ value, onChange, options, placeholder = "Select", className }: DropdownProps) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    }
    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const selected = options.find((option) => option.value === value);
  const SelectedIcon = selected?.icon;

  return (
    <div ref={containerRef} className={cn("relative", className)}>
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className="flex h-10 w-full items-center justify-between rounded-sm border border-line bg-surface px-3 text-sm text-ink hover:border-line-strong"
      >
        <span className={cn("flex items-center gap-2", selected ? "text-ink" : "text-ink-faint")}>
          {SelectedIcon && <SelectedIcon className="h-3.5 w-3.5 shrink-0" />}
          {selected?.label ?? placeholder}
        </span>
        <ChevronDown className="h-4 w-4 text-ink-faint" />
      </button>
      {open && (
        <div
          role="listbox"
          className="animate-slide-fade-in absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-sm border border-line bg-surface shadow-md"
        >
          {options.map((option, index) => {
            const Icon = option.icon;
            const showGroupHeader = option.group && option.group !== options[index - 1]?.group;
            return (
              <div key={option.value}>
                {showGroupHeader && (
                  <p className="px-3 pb-1 pt-2 font-mono text-[10px] uppercase tracking-wide text-ink-faint">{option.group}</p>
                )}
                <button
                  type="button"
                  role="option"
                  aria-selected={option.value === value}
                  onClick={() => {
                    onChange(option.value);
                    setOpen(false);
                  }}
                  className={cn(
                    "flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-surface-sunken",
                    option.value === value ? "text-route" : "text-ink",
                  )}
                >
                  {Icon && <Icon className="h-3.5 w-3.5 shrink-0" />}
                  <span className="min-w-0 flex-1">
                    <span className="block truncate">{option.label}</span>
                    {option.description && <span className="block truncate font-mono text-[10px] text-ink-faint">{option.description}</span>}
                  </span>
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
