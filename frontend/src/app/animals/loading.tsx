/**
 * Animals segment loading boundary.
 *
 * Shown during navigation to the animals listing or while data is fetching.
 * Renders a grid of skeleton cards that matches the layout of the real
 * animal cards to avoid layout shift.
 */
export default function AnimalsLoading() {
  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6 h-8 w-48 animate-pulse rounded bg-gray-200" />
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm">
            <div className="h-48 animate-pulse bg-gray-200" />
            <div className="p-4 space-y-2">
              <div className="h-5 w-3/4 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-1/2 animate-pulse rounded bg-gray-200" />
              <div className="h-4 w-2/3 animate-pulse rounded bg-gray-200" />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
