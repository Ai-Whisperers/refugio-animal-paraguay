/**
 * Animal detail segment loading boundary.
 *
 * Shown during navigation to an individual animal profile.
 * Renders a skeleton that mirrors the real page layout (photo hero +
 * thumbnail strip + info section) to eliminate layout shift.
 */
export default function AnimalDetailLoading() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-pulse">
      {/* Breadcrumb placeholder */}
      <div className="mb-6 h-4 w-48 rounded bg-gray-200" />

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Hero image placeholder */}
        <div className="h-64 md:h-96 bg-gray-200 relative">
          {/* Status badge placeholder */}
          <div className="absolute top-4 right-4 h-6 w-20 rounded-full bg-gray-300" />
        </div>

        {/* Thumbnail strip placeholder */}
        <div className="flex gap-2 px-4 py-3 bg-gray-50">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="flex-shrink-0 h-20 w-20 rounded-lg bg-gray-200" />
          ))}
        </div>

        {/* Info section placeholder */}
        <div className="p-6 md:p-8 space-y-6">
          {/* Name */}
          <div className="h-8 w-48 rounded bg-gray-200" />

          {/* Detail grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="space-y-1">
                <div className="h-3 w-12 rounded bg-gray-200" />
                <div className="h-5 w-20 rounded bg-gray-200" />
              </div>
            ))}
          </div>

          {/* Description lines */}
          <div className="space-y-2">
            <div className="h-5 w-32 rounded bg-gray-200" />
            <div className="h-4 w-full rounded bg-gray-100" />
            <div className="h-4 w-5/6 rounded bg-gray-100" />
            <div className="h-4 w-4/6 rounded bg-gray-100" />
          </div>

          {/* CTA buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="h-12 w-48 rounded-lg bg-gray-200" />
            <div className="h-12 w-48 rounded-lg bg-gray-200" />
            <div className="h-12 w-32 rounded-lg bg-gray-100" />
          </div>
        </div>
      </div>
    </div>
  );
}
