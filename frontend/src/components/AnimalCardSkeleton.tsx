/** Skeleton placeholder for animal cards while loading. */
export default function AnimalCardSkeleton() {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden animate-pulse">
      {/* Photo area */}
      <div className="aspect-[4/3] bg-gray-200 relative">
        {/* Badge placeholder */}
        <div className="absolute top-3 right-3 h-5 w-16 bg-gray-300 rounded-full" />
      </div>

      {/* Info area */}
      <div className="p-4 space-y-3">
        {/* Name placeholder */}
        <div className="h-5 bg-gray-200 rounded w-2/3" />
        {/* Species + age placeholder */}
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        {/* Description placeholder */}
        <div className="space-y-2">
          <div className="h-3 bg-gray-100 rounded w-full" />
          <div className="h-3 bg-gray-100 rounded w-3/4" />
        </div>
        {/* CTA placeholder */}
        <div className="h-4 bg-gray-200 rounded w-1/3 mt-2" />
      </div>
    </div>
  );
}
