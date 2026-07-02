"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { DashboardMetrics } from "@/lib/types";
import { getDashboardMetrics, ApiError } from "@/lib/api";

const POLL_INTERVAL_MS = 10_000;

export function useAnalytics(days: number) {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const daysRef = useRef(days);

  daysRef.current = days;

  const fetchMetrics = useCallback(async (silent: boolean) => {
    if (silent) {
      setIsRefreshing(true);
    } else {
      setIsLoading(true);
    }

    try {
      const data = await getDashboardMetrics(daysRef.current);
      setMetrics(data);
      setLastUpdated(new Date());
      setError(null);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else if (err instanceof TypeError) {
        setError("Could not reach the backend. Check that the API is running on port 8000.");
      } else {
        setError(err instanceof Error ? err.message : "Failed to load analytics");
      }
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    await fetchMetrics(metrics !== null);
  }, [fetchMetrics, metrics]);

  useEffect(() => {
    void fetchMetrics(false);
  }, [days, fetchMetrics]);

  useEffect(() => {
    const poll = () => {
      if (document.visibilityState === "visible") {
        void fetchMetrics(true);
      }
    };

    const intervalId = window.setInterval(poll, POLL_INTERVAL_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") {
        void fetchMetrics(true);
      }
    };

    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(intervalId);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, [fetchMetrics]);

  return { metrics, isLoading, isRefreshing, lastUpdated, error, refresh };
};
