"use client";

import { useCallback, useEffect, useState } from "react";
import type { IntelligenceCapabilities } from "@/lib/types";
import { getIntelligenceCapabilities } from "@/lib/api";

export function useIntelligenceCapabilities() {
  const [capabilities, setCapabilities] = useState<IntelligenceCapabilities | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    try {
      setCapabilities(await getIntelligenceCapabilities());
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { capabilities, isLoading, refresh };
}
