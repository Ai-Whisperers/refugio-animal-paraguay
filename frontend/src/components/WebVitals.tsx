"use client";

import { useEffect } from "react";

/**
 * Core Web Vitals reporter.
 *
 * Logs LCP, FID, CLS, TTFB, and INP to console in development
 * and sends metrics to analytics endpoint in production.
 */

interface WebVitalMetric {
  name: string;
  value: number;
  rating: "good" | "needs-improvement" | "poor";
  id: string;
}

const VITALS_THRESHOLDS: Record<string, { good: number; poor: number }> = {
  LCP: { good: 2500, poor: 4000 },
  FID: { good: 100, poor: 300 },
  CLS: { good: 0.1, poor: 0.25 },
  TTFB: { good: 800, poor: 1800 },
  INP: { good: 200, poor: 500 },
};

function getRating(name: string, value: number): "good" | "needs-improvement" | "poor" {
  const threshold = VITALS_THRESHOLDS[name];
  if (!threshold) return "good";
  if (value <= threshold.good) return "good";
  if (value <= threshold.poor) return "needs-improvement";
  return "poor";
}

function reportMetric(metric: WebVitalMetric): void {
  const emoji = metric.rating === "good" ? "OK" : metric.rating === "needs-improvement" ? "WARN" : "BAD";
  if (process.env.NODE_ENV === "development") {
    console.log(`[WebVitals] ${emoji} ${metric.name}: ${metric.value.toFixed(2)}ms (${metric.rating})`);
  }

  // In production, send to analytics endpoint
  if (process.env.NODE_ENV === "production" && process.env.NEXT_PUBLIC_VITALS_URL) {
    const body = JSON.stringify({
      name: metric.name,
      value: metric.value,
      rating: metric.rating,
      id: metric.id,
      url: window.location.pathname,
    });
    // Use sendBeacon for reliable delivery without blocking navigation
    if (navigator.sendBeacon) {
      navigator.sendBeacon(process.env.NEXT_PUBLIC_VITALS_URL, body);
    }
  }
}

export default function WebVitals() {
  useEffect(() => {
    // Dynamically import web-vitals to avoid blocking initial load
    import("web-vitals").then(({ onCLS, onFID, onLCP, onTTFB, onINP }) => {
      const handler = (metric: { name: string; value: number; id: string }) => {
        reportMetric({
          ...metric,
          rating: getRating(metric.name, metric.value),
        });
      };

      onCLS(handler);
      onFID(handler);
      onLCP(handler);
      onTTFB(handler);
      onINP(handler);
    }).catch(() => {
      // web-vitals not available -- skip silently
    });
  }, []);

  return null;
}
