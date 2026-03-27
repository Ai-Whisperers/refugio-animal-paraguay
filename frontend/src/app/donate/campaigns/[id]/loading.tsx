/**
 * Campaign detail segment loading boundary.
 *
 * Shown during navigation to a specific donation campaign page.
 * Mirrors the two-column layout (campaign info + donation form) to
 * prevent layout shift while the server fetches campaign data.
 */
export default function CampaignDetailLoading() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8 sm:py-12 animate-pulse">
      {/* Back link placeholder */}
      <div className="mb-6 h-5 w-32 rounded bg-gray-200" />

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left column — campaign info */}
        <div className="lg:col-span-2 space-y-6">
          {/* Hero image */}
          <div className="h-64 rounded-xl bg-gray-200" />

          {/* Category badge + title */}
          <div className="space-y-2">
            <div className="h-5 w-24 rounded-full bg-gray-200" />
            <div className="h-8 w-3/4 rounded bg-gray-200" />
          </div>

          {/* Progress card */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 space-y-3">
            <div className="flex justify-between">
              <div className="h-6 w-28 rounded bg-gray-200" />
              <div className="h-5 w-24 rounded bg-gray-200" />
            </div>
            <div className="h-3 w-full rounded-full bg-gray-200" />
            <div className="flex gap-6">
              <div className="h-4 w-24 rounded bg-gray-200" />
              <div className="h-4 w-20 rounded bg-gray-200" />
            </div>
          </div>

          {/* Description lines */}
          <div className="space-y-2">
            <div className="h-4 w-full rounded bg-gray-100" />
            <div className="h-4 w-11/12 rounded bg-gray-100" />
            <div className="h-4 w-4/5 rounded bg-gray-100" />
            <div className="h-4 w-3/4 rounded bg-gray-100" />
          </div>
        </div>

        {/* Right column — donation form skeleton */}
        <div className="lg:col-span-1">
          <div className="rounded-xl border border-gray-100 bg-white shadow-sm p-6 space-y-4">
            <div className="h-6 w-40 rounded bg-gray-200" />
            <div className="grid grid-cols-3 gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-10 rounded-lg bg-gray-200" />
              ))}
            </div>
            <div className="h-12 w-full rounded-lg bg-gray-200" />
            <div className="h-10 w-full rounded-lg bg-gray-200" />
          </div>
        </div>
      </div>
    </div>
  );
}
