"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { CampaignPublic } from "@/types/api";
import { getCampaignPublic } from "@/lib/public-api";

const DEFAULT_POLL_INTERVAL_MS = 30_000;

interface UseCampaignPollingOptions {
  /** Polling interval in milliseconds. Default: 30000 (30s). */
  intervalMs?: number;
  /** Whether polling is enabled. Default: true. */
  enabled?: boolean;
}

interface UseCampaignPollingResult {
  campaign: CampaignPublic | null;
  loading: boolean;
  error: string | null;
  /** True when a progress increase was just detected (resets after 4s). */
  donationFlash: boolean;
  /** True when campaign just became fully funded (resets after 6s). */
  fullyFundedFlash: boolean;
}

/**
 * Hook that fetches a campaign and polls for updates.
 *
 * Pauses polling when the page is hidden (Page Visibility API)
 * and resumes when the user returns. Detects progress increases
 * and triggers flash notifications.
 */
export function useCampaignPolling(
  campaignId: string,
  options: UseCampaignPollingOptions = {}
): UseCampaignPollingResult {
  const { intervalMs = DEFAULT_POLL_INTERVAL_MS, enabled = true } = options;

  const [campaign, setCampaign] = useState<CampaignPublic | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [donationFlash, setDonationFlash] = useState(false);
  const [fullyFundedFlash, setFullyFundedFlash] = useState(false);

  const prevRaisedRef = useRef<number | null>(null);
  const prevFullyFundedRef = useRef(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchCampaign = useCallback(
    async (isInitial: boolean) => {
      try {
        const data = await getCampaignPublic(campaignId);

        // Detect progress increase (only on poll updates, not initial load)
        if (!isInitial && prevRaisedRef.current !== null) {
          if (data.raised_amount_cents > prevRaisedRef.current) {
            setDonationFlash(true);
            setTimeout(() => setDonationFlash(false), 4_000);
          }

          // Detect transition to fully funded
          const nowFullyFunded =
            data.progress_percentage >= 100 || data.status === "completed";
          if (nowFullyFunded && !prevFullyFundedRef.current) {
            setFullyFundedFlash(true);
            setTimeout(() => setFullyFundedFlash(false), 6_000);
          }
          prevFullyFundedRef.current = nowFullyFunded;
        } else {
          // Set initial state
          prevFullyFundedRef.current =
            data.progress_percentage >= 100 || data.status === "completed";
        }

        prevRaisedRef.current = data.raised_amount_cents;
        setCampaign(data);
        setError(null);
      } catch {
        if (isInitial) {
          setError("No se pudo cargar la campana.");
        }
        // On poll failure, keep last known data (graceful degradation)
      } finally {
        if (isInitial) {
          setLoading(false);
        }
      }
    },
    [campaignId]
  );

  // Initial fetch
  useEffect(() => {
    fetchCampaign(true);
  }, [fetchCampaign]);

  // Polling with visibility pause
  useEffect(() => {
    if (!enabled) return;

    function startPolling() {
      if (intervalRef.current) return;
      intervalRef.current = setInterval(() => {
        fetchCampaign(false);
      }, intervalMs);
    }

    function stopPolling() {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    function handleVisibilityChange() {
      if (document.hidden) {
        stopPolling();
      } else {
        // Fetch immediately on return, then resume interval
        fetchCampaign(false);
        startPolling();
      }
    }

    // Start polling if page is visible
    if (!document.hidden) {
      startPolling();
    }

    document.addEventListener("visibilitychange", handleVisibilityChange);

    return () => {
      stopPolling();
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [enabled, intervalMs, fetchCampaign]);

  return { campaign, loading, error, donationFlash, fullyFundedFlash };
}
