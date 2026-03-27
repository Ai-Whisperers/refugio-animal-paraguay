/**
 * Contact page segment loading boundary.
 *
 * Shown during navigation to the contact page.
 * Renders a skeleton that matches the real page layout (header,
 * WhatsApp CTA card, info cards, email form) to eliminate layout shift.
 */
export default function ContactLoading() {
  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 animate-pulse">
      {/* Header */}
      <div className="text-center mb-10 space-y-3">
        <div className="mx-auto h-10 w-72 rounded bg-gray-200" />
        <div className="mx-auto h-5 w-80 rounded bg-gray-100" />
      </div>

      {/* WhatsApp CTA card */}
      <div className="rounded-xl bg-gray-100 p-6 mb-8 flex flex-col items-center gap-3">
        <div className="h-14 w-14 rounded-full bg-gray-200" />
        <div className="h-6 w-48 rounded bg-gray-200" />
        <div className="h-4 w-64 rounded bg-gray-100" />
        <div className="h-11 w-40 rounded-lg bg-gray-200" />
      </div>

      {/* Info cards row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="rounded-lg bg-gray-100 p-4 flex flex-col items-center gap-2">
            <div className="h-6 w-6 rounded bg-gray-200" />
            <div className="h-4 w-24 rounded bg-gray-200" />
            <div className="h-3 w-32 rounded bg-gray-100" />
          </div>
        ))}
      </div>

      {/* Form skeleton */}
      <div className="rounded-xl border border-gray-100 bg-white shadow-sm p-6 sm:p-8 space-y-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="space-y-1">
            <div className="h-4 w-28 rounded bg-gray-200" />
            <div className={`w-full rounded-lg bg-gray-100 ${i === 3 ? "h-28" : "h-10"}`} />
          </div>
        ))}
        <div className="h-12 w-full rounded-lg bg-gray-200" />
      </div>
    </div>
  );
}
