"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { X, Settings, Check } from "lucide-react";
import { COOKIE_CONSENT } from "@/lib/strings";

const CONSENT_KEY = "rap_cookie_consent";

export type CookiePreferences = {
  essential: true;
  analytics: boolean;
  marketing: boolean;
};

function loadConsent(): CookiePreferences | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CONSENT_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as CookiePreferences;
  } catch {
    return null;
  }
}

function saveConsent(prefs: CookiePreferences): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(CONSENT_KEY, JSON.stringify(prefs));
}

type ToggleProps = {
  checked: boolean;
  onChange: (val: boolean) => void;
  disabled?: boolean;
  label: string;
};

function Toggle({ checked, onChange, disabled = false, label }: ToggleProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      disabled={disabled}
      onClick={() => !disabled && onChange(!checked)}
      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
        checked ? "bg-primary-600" : "bg-gray-200"
      } ${disabled ? "opacity-50 cursor-not-allowed" : "cursor-pointer"}`}
    >
      <span
        className={`inline-block h-4 w-4 transform rounded-full bg-white shadow transition-transform ${
          checked ? "translate-x-6" : "translate-x-1"
        }`}
      />
    </button>
  );
}

/**
 * Cookie consent banner shown at bottom of screen until user makes a choice.
 * Preferences are persisted in localStorage under `rap_cookie_consent`.
 */
export default function CookieConsentBanner() {
  const [visible, setVisible] = useState(false);
  const [showPrefs, setShowPrefs] = useState(false);
  const [analytics, setAnalytics] = useState(false);

  useEffect(() => {
    const existing = loadConsent();
    if (!existing) {
      // Small delay to avoid layout shift on first paint
      const timer = setTimeout(() => setVisible(true), 800);
      return () => clearTimeout(timer);
    }
  }, []);

  function acceptAll() {
    saveConsent({ essential: true, analytics: true, marketing: false });
    setVisible(false);
    setShowPrefs(false);
  }

  function rejectOptional() {
    saveConsent({ essential: true, analytics: false, marketing: false });
    setVisible(false);
    setShowPrefs(false);
  }

  function saveCustom() {
    saveConsent({ essential: true, analytics, marketing: false });
    setVisible(false);
    setShowPrefs(false);
  }

  if (!visible) return null;

  return (
    <>
      {/* Overlay (only when preferences modal is open) */}
      {showPrefs && (
        <div
          className="fixed inset-0 bg-black/40 z-40"
          onClick={() => setShowPrefs(false)}
          aria-hidden="true"
        />
      )}

      {/* Preferences modal */}
      {showPrefs && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="cookie-prefs-title"
          className="fixed bottom-0 left-0 right-0 sm:bottom-auto sm:top-1/2 sm:left-1/2 sm:-translate-x-1/2 sm:-translate-y-1/2 sm:max-w-md sm:w-full bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl p-6 z-50 mx-auto"
        >
          <div className="flex items-center justify-between mb-4">
            <h2 id="cookie-prefs-title" className="text-lg font-heading font-bold text-gray-900">
              {COOKIE_CONSENT.preferencesTitle}
            </h2>
            <button
              type="button"
              onClick={() => setShowPrefs(false)}
              aria-label={COOKIE_CONSENT.closeModal}
              className="p-2 rounded-full text-gray-500 hover:text-gray-800 hover:bg-gray-100 transition-colors"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="text-sm text-gray-500 mb-6">{COOKIE_CONSENT.preferencesSubtitle}</p>

          <div className="space-y-5">
            {/* Essential */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium text-gray-900 text-sm">{COOKIE_CONSENT.essentialTitle}</p>
                <p className="text-xs text-gray-500 mt-1">{COOKIE_CONSENT.essentialDesc}</p>
              </div>
              <div className="flex items-center gap-2 shrink-0">
                <span className="text-xs text-gray-400">{COOKIE_CONSENT.alwaysActive}</span>
                <Toggle
                  checked={true}
                  onChange={() => {}}
                  disabled={true}
                  label={COOKIE_CONSENT.essentialTitle}
                />
              </div>
            </div>

            {/* Analytics */}
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="font-medium text-gray-900 text-sm">{COOKIE_CONSENT.analyticsTitle}</p>
                <p className="text-xs text-gray-500 mt-1">{COOKIE_CONSENT.analyticsDesc}</p>
              </div>
              <Toggle
                checked={analytics}
                onChange={setAnalytics}
                label={COOKIE_CONSENT.analyticsTitle}
              />
            </div>

            {/* Marketing */}
            <div className="flex items-start justify-between gap-4 opacity-50">
              <div>
                <p className="font-medium text-gray-900 text-sm">{COOKIE_CONSENT.marketingTitle}</p>
                <p className="text-xs text-gray-500 mt-1">{COOKIE_CONSENT.marketingDesc}</p>
              </div>
              <Toggle
                checked={false}
                onChange={() => {}}
                disabled={true}
                label={COOKIE_CONSENT.marketingTitle}
              />
            </div>
          </div>

          <div className="mt-6 flex gap-3">
            <button
              type="button"
              onClick={() => setShowPrefs(false)}
              className="flex-1 px-4 py-2 rounded-lg border border-gray-300 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              {COOKIE_CONSENT.cancel}
            </button>
            <button
              type="button"
              onClick={saveCustom}
              className="flex-1 px-4 py-2 rounded-lg bg-primary-600 text-white text-sm font-medium hover:bg-primary-700 transition-colors"
            >
              {COOKIE_CONSENT.savePreferences}
            </button>
          </div>
        </div>
      )}

      {/* Main banner */}
      {!showPrefs && (
        <div
          role="banner"
          aria-label={COOKIE_CONSENT.bannerTitle}
          className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 shadow-lg px-4 py-4 sm:px-6"
          style={{ paddingBottom: "max(1rem, env(safe-area-inset-bottom))" }}
        >
          <div className="max-w-5xl mx-auto">
            <div className="flex flex-col sm:flex-row sm:items-center gap-4">
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-900 mb-1">
                  {COOKIE_CONSENT.bannerTitle}
                </p>
                <p className="text-xs text-gray-500 leading-relaxed">
                  {COOKIE_CONSENT.bannerText}{" "}
                  <Link href="/privacy" className="underline hover:text-primary-600">
                    {COOKIE_CONSENT.privacyLink}
                  </Link>
                </p>
              </div>
              <div className="flex items-center gap-2 shrink-0 flex-wrap">
                <button
                  type="button"
                  onClick={() => setShowPrefs(true)}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  <Settings className="h-3.5 w-3.5" />
                  {COOKIE_CONSENT.customize}
                </button>
                <button
                  type="button"
                  onClick={rejectOptional}
                  className="px-3 py-2 rounded-lg border border-gray-300 text-xs text-gray-700 hover:bg-gray-50 transition-colors"
                >
                  {COOKIE_CONSENT.rejectOptional}
                </button>
                <button
                  type="button"
                  onClick={acceptAll}
                  className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-primary-600 text-white text-xs font-medium hover:bg-primary-700 transition-colors"
                >
                  <Check className="h-3.5 w-3.5" />
                  {COOKIE_CONSENT.acceptAll}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
