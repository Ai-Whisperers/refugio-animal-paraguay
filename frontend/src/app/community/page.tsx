"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API = process.env.NEXT_PUBLIC_API_URL ?? "";
const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type FeedItemType = "animal" | "campaign" | "need" | "success";

interface FeedItem {
  id: string;
  event_type: FeedItemType;
  title: string;
  preview: string;
  timestamp: string;
  image_url: string | null;
  detail_url: string;
  rescuer_name: string | null;
  location_city: string | null;
  badge: string;
  // type-specific extras
  species?: string;
  breed?: string;
  target_eur?: number;
  fund_category?: string;
  category?: string;
  adopter_name?: string;
  is_featured?: boolean;
}

interface FeedResponse {
  items: FeedItem[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const TYPE_LABELS: Record<FeedItemType, string> = {
  animal: "Animals",
  campaign: "Campaigns",
  need: "Help Needed",
  success: "Success Stories",
};

const TYPE_COLORS: Record<FeedItemType, string> = {
  animal: "bg-emerald-100 text-emerald-800",
  campaign: "bg-blue-100 text-blue-800",
  need: "bg-amber-100 text-amber-800",
  success: "bg-purple-100 text-purple-800",
};

const TYPE_ICONS: Record<FeedItemType, string> = {
  animal: "🐾",
  campaign: "🎯",
  need: "🆘",
  success: "🏡",
};

function formatRelativeTime(ts: string): string {
  const diffMs = Date.now() - new Date(ts).getTime();
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffH = Math.floor(diffMin / 60);
  if (diffH < 24) return `${diffH}h ago`;
  const diffD = Math.floor(diffH / 24);
  if (diffD < 30) return `${diffD}d ago`;
  return new Date(ts).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

// ---------------------------------------------------------------------------
// Feed item card
// ---------------------------------------------------------------------------

function FeedCard({ item }: { item: FeedItem }) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
      {item.image_url && (
        <div className="h-48 overflow-hidden bg-gray-100">
          <img
            src={item.image_url}
            alt={item.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      )}
      <div className="p-4">
        {/* Header row */}
        <div className="flex items-center justify-between mb-2 gap-2 flex-wrap">
          <span
            className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${TYPE_COLORS[item.event_type]}`}
          >
            {TYPE_ICONS[item.event_type]} {item.badge}
          </span>
          <span className="text-xs text-gray-400">{formatRelativeTime(item.timestamp)}</span>
        </div>

        {/* Title */}
        <h3 className="text-base font-semibold text-gray-900 leading-snug mb-1 line-clamp-2">
          {item.title}
        </h3>

        {/* Rescuer / location */}
        {(item.rescuer_name || item.location_city) && (
          <p className="text-xs text-gray-500 mb-2">
            {item.rescuer_name && (
              <span className="font-medium text-gray-700">{item.rescuer_name}</span>
            )}
            {item.rescuer_name && item.location_city && " · "}
            {item.location_city}
          </p>
        )}

        {/* Preview */}
        {item.preview && (
          <p className="text-sm text-gray-600 line-clamp-3 mb-3">{item.preview}</p>
        )}

        {/* CTA */}
        <Link
          href={item.detail_url}
          className="inline-block text-sm font-medium text-emerald-700 hover:text-emerald-900 hover:underline"
        >
          Learn more →
        </Link>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Filter bar
// ---------------------------------------------------------------------------

type ActiveFilters = Set<FeedItemType>;

function FilterBar({
  active,
  onChange,
}: {
  active: ActiveFilters;
  onChange: (t: FeedItemType) => void;
}) {
  const all = Object.entries(TYPE_LABELS) as [FeedItemType, string][];
  return (
    <div className="flex flex-wrap gap-2">
      {all.map(([type, label]) => {
        const isActive = active.has(type);
        return (
          <button
            key={type}
            onClick={() => onChange(type)}
            className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-full text-sm font-medium border transition-colors ${
              isActive
                ? "bg-emerald-600 text-white border-emerald-600"
                : "bg-white text-gray-700 border-gray-300 hover:border-emerald-400 hover:text-emerald-700"
            }`}
          >
            {TYPE_ICONS[type]} {label}
          </button>
        );
      })}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------

export default function CommunityFeedPage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [page, setPage] = useState(1);
  const [hasNext, setHasNext] = useState(false);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTypes, setActiveTypes] = useState<ActiveFilters>(
    new Set(["animal", "campaign", "need", "success"] as FeedItemType[])
  );

  const fetchPage = useCallback(
    async (pageNum: number, types: ActiveFilters, append: boolean) => {
      setLoading(true);
      setError(null);
      try {
        const typeParams = [...types].map((t) => `types=${t}`).join("&");
        const url = `${API}/api/community/feed?page=${pageNum}&page_size=${PAGE_SIZE}&${typeParams}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const data: FeedResponse = await res.json();
        setItems((prev) => (append ? [...prev, ...data.items] : data.items));
        setHasNext(data.has_next);
        setTotal(data.total);
        setPage(data.page);
      } catch (err) {
        setError((err as Error).message || "Failed to load feed");
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Initial load and on filter change
  useEffect(() => {
    fetchPage(1, activeTypes, false);
  }, [activeTypes, fetchPage]);

  function toggleType(type: FeedItemType) {
    setActiveTypes((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        if (next.size === 1) return prev; // keep at least one active
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }

  function loadMore() {
    fetchPage(page + 1, activeTypes, true);
  }

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Hero */}
      <div className="bg-emerald-700 text-white py-12 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl font-bold mb-2">Community Feed</h1>
          <p className="text-emerald-100 text-lg">
            Follow rescue efforts, new arrivals, active campaigns, and happy endings.
          </p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Filter bar */}
        <div className="mb-6">
          <p className="text-sm text-gray-500 mb-3">Filter by type:</p>
          <FilterBar active={activeTypes} onChange={toggleType} />
        </div>

        {/* Stats */}
        {total > 0 && !loading && (
          <p className="text-sm text-gray-500 mb-4">
            {total} {total === 1 ? "activity" : "activities"} found
          </p>
        )}

        {/* Error */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg p-4 mb-6">
            {error}
          </div>
        )}

        {/* Grid */}
        {items.length > 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {items.map((item) => (
              <FeedCard key={`${item.event_type}-${item.id}`} item={item} />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && items.length === 0 && !error && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-5xl mb-4">🌱</p>
            <p className="text-lg font-medium text-gray-600">No activity yet</p>
            <p className="text-sm">Check back soon — the community is growing.</p>
          </div>
        )}

        {/* Load more */}
        {hasNext && (
          <div className="mt-8 text-center">
            <button
              onClick={loadMore}
              disabled={loading}
              className="px-6 py-2.5 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? "Loading…" : "Load more"}
            </button>
          </div>
        )}

        {loading && items.length === 0 && (
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="bg-white rounded-xl border border-gray-100 h-64 animate-pulse"
              />
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
