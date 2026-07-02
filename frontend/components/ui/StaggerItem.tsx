"use client";

import { cn } from "@/lib/utils";

interface StaggerItemProps {
  index?: number;
  className?: string;
  children: React.ReactNode;
  baseDelay?: number;
  step?: number;
}

export function StaggerItem({ index = 0, className, children, baseDelay = 0, step = 55 }: StaggerItemProps) {
  return (
    <div className={cn("animate-rise-in", className)} style={{ animationDelay: `${baseDelay + index * step}ms` }}>
      {children}
    </div>
  );
}
