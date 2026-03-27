/**
 * Root loading boundary — shown while any route segment is loading.
 *
 * Next.js automatically renders this component as a Suspense fallback
 * during server-side data fetching or when navigating to a new route.
 *
 * @see https://nextjs.org/docs/app/building-your-application/routing/loading-ui-and-streaming
 */
export default function GlobalLoading() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <div className="flex flex-col items-center gap-4">
        <div className="h-10 w-10 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        <p className="text-sm text-gray-500">Cargando…</p>
      </div>
    </div>
  );
}
