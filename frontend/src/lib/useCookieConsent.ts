"use client";

import { useState, useEffect } from "react";
import type { CookiePreferences } from "@/components/CookieConsentBanner";

const CONSENT_KEY = "rap_cookie_consent";

/**
 * Returns the current cookie consent preferences, or null if not yet set.
 * Re-reads from localStorage on mount.
 */
export function useCookieConsent(): CookiePreferences | null {
  const [prefs, setPrefs] = useState<CookiePreferences | null>(null);

  useEffect(() => {
    try {
      const raw = localStorage.getItem(CONSENT_KEY);
      if (raw) setPrefs(JSON.parse(raw) as CookiePreferences);
    } catch {
      setPrefs(null);
    }
  }, []);

  return prefs;
}
