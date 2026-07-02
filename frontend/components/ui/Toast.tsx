"use client";

import { useEffect } from "react";
import { useToastStore, type ToastTone } from "@/store/toastStore";
import { cn } from "@/lib/utils";

const toneClasses: Record<ToastTone, string> = {
  neutral: "border-line bg-surface text-ink",
  live: "border-live/30 bg-live-soft text-live",
  attn: "border-attn/30 bg-attn-soft text-attn",
};

function ToastRow({ id, message, tone }: { id: string; message: string; tone: ToastTone }) {
  const dismiss = useToastStore((state) => state.dismiss);

  useEffect(() => {
    const timer = setTimeout(() => dismiss(id), 5000);
    return () => clearTimeout(timer);
  }, [id, dismiss]);

  return (
    <div
      className={cn("animate-slide-fade-in rounded-sm border px-4 py-3 text-sm shadow-md", toneClasses[tone])}
      onClick={() => dismiss(id)}
      role="status"
    >
      {message}
    </div>
  );
}

export function Toaster() {
  const toasts = useToastStore((state) => state.toasts);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2">
      {toasts.map((toast) => (
        <ToastRow key={toast.id} {...toast} />
      ))}
    </div>
  );
}
