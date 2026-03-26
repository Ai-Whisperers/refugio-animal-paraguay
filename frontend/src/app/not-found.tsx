import Link from "next/link";
import { Home, Search } from "lucide-react";

/** Custom 404 page in Spanish with branded design. */
export default function NotFound() {
  return (
    <div className="max-w-2xl mx-auto px-4 py-20 text-center">
      <div className="mb-8">
        <p className="text-8xl font-bold text-[#E8622A]/20 mb-4">404</p>
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-3">
          Pagina no encontrada
        </h1>
        <p className="text-gray-500 max-w-md mx-auto">
          La pagina que buscas no existe o fue movida. Pero no te preocupes, hay muchos amiguitos esperandote.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          href="/"
          className="inline-flex items-center justify-center gap-2 bg-[#E8622A] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#d4571f] transition-colors"
        >
          <Home className="h-5 w-5" />
          Volver al inicio
        </Link>
        <Link
          href="/animals"
          className="inline-flex items-center justify-center gap-2 bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
        >
          <Search className="h-5 w-5" />
          Ver animales
        </Link>
      </div>
    </div>
  );
}
