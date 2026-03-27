/**
 * Donation segment loading boundary.
 */
export default function DonateLoading() {
  return (
    <div className="flex min-h-[50vh] items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-9 w-9 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        <p className="text-sm text-gray-500">Cargando formulario de donación…</p>
      </div>
    </div>
  );
}
