"use client";

import { useCallback, useEffect, useState } from "react";
import type { CampaignPublic, FundCategory } from "@/types/api";
import { listCampaignsPublic } from "@/lib/public-api";
import { getCategoryLabel } from "@/lib/campaign-utils";
import CampaignCard from "@/components/CampaignCard";
import { DONATE } from "@/lib/strings";

const CATEGORY_FILTERS: Array<{ value: FundCategory | "all"; label: string }> = [
  { value: "all", label: "Todas" },
  { value: "medical", label: getCategoryLabel("medical") },
  { value: "food", label: getCategoryLabel("food") },
  { value: "rescue", label: getCategoryLabel("rescue") },
  { value: "operations", label: getCategoryLabel("operations") },
  { value: "infrastructure", label: getCategoryLabel("infrastructure") },
  { value: "general", label: getCategoryLabel("general") },
];

const PAGE_SIZE = 12;

export default function CampaignListSection() {
  const [campaigns, setCampaigns] = useState<CampaignPublic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState<FundCategory | "all">("all");
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);

  const fetchCampaigns = useCallback(async (category: FundCategory | "all", pageNum: number) => {
    setLoading(true);
    setError(null);
    try {
      const response = await listCampaignsPublic({
        category: category === "all" ? undefined : category,
        page: pageNum,
        page_size: PAGE_SIZE,
      });
      setCampaigns(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error al cargar campanas");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCampaigns(activeCategory, page);
  }, [activeCategory, page, fetchCampaigns]);

  function handleCategoryChange(category: FundCategory | "all") {
    setActiveCategory(category);
    setPage(1);
  }

  const totalPages = Math.ceil(total / PAGE_SIZE);

  return (
    <div>
      {/* Category Filter Tabs */}
      <div className="flex flex-wrap gap-2 mb-6 justify-center">
        {CATEGORY_FILTERS.map((filter) => (
          <button
            key={filter.value}
            onClick={() => handleCategoryChange(filter.value)}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              activeCategory === filter.value
                ? "bg-primary-600 text-white"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            {filter.label}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {Array.from({ length: 3 }).map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse"
            >
              <div className="h-40 bg-gray-200" />
              <div className="p-5 space-y-3">
                <div className="h-4 bg-gray-200 rounded w-1/4" />
                <div className="h-5 bg-gray-200 rounded w-3/4" />
                <div className="h-4 bg-gray-200 rounded w-full" />
                <div className="h-2.5 bg-gray-200 rounded-full w-full" />
                <div className="flex justify-between">
                  <div className="h-4 bg-gray-200 rounded w-1/3" />
                  <div className="h-4 bg-gray-200 rounded w-1/6" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Error State */}
      {!loading && error && (
        <div className="text-center py-12">
          <p className="text-red-600 mb-2">{error}</p>
          <button
            onClick={() => fetchCampaigns(activeCategory, page)}
            className="text-primary-600 hover:text-primary-700 font-medium"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Empty State */}
      {!loading && !error && campaigns.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-500">
            {activeCategory === "all"
              ? DONATE.noCampaigns
              : `No hay campanas activas en la categoria "${getCategoryLabel(activeCategory as FundCategory)}".`}
          </p>
        </div>
      )}

      {/* Campaign Grid */}
      {!loading && !error && campaigns.length > 0 && (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {campaigns.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} />
            ))}
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex justify-center gap-2 mt-8">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page === 1}
                className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Anterior
              </button>
              <span className="px-4 py-2 text-sm text-gray-600">
                {page} de {totalPages}
              </span>
              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={page === totalPages}
                className="px-4 py-2 rounded-lg text-sm font-medium border border-gray-200 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50 transition-colors"
              >
                Siguiente
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
