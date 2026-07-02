import { create } from "zustand";

export type ToastTone = "neutral" | "live" | "attn";

export interface ToastItem {
  id: string;
  message: string;
  tone: ToastTone;
}

interface ToastState {
  toasts: ToastItem[];
  push: (message: string, tone?: ToastTone) => void;
  dismiss: (id: string) => void;
}

export const useToastStore = create<ToastState>()((set) => ({
  toasts: [],
  push: (message, tone = "neutral") =>
    set((state) => ({
      toasts: [...state.toasts, { id: `${Date.now()}-${Math.random().toString(16).slice(2)}`, message, tone }],
    })),
  dismiss: (id) => set((state) => ({ toasts: state.toasts.filter((toast) => toast.id !== id) })),
}));
