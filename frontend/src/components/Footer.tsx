import Link from "next/link";
import { APP_NAME } from "@/lib/constants";

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-stone-800 text-stone-300">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 gap-8 sm:grid-cols-3">
          {/* About section */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
              {APP_NAME}
            </h3>
            <p className="mt-2 text-sm">
              Rescatamos, rehabilitamos y buscamos hogares para animales
              abandonados en Paraguay.
            </p>
          </div>

          {/* Quick links */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
              Enlaces
            </h3>
            <ul className="mt-2 space-y-1">
              <li>
                <Link href="/animals" className="text-sm hover:text-white">
                  Animales disponibles
                </Link>
              </li>
              <li>
                <Link href="/adopt" className="text-sm hover:text-white">
                  Proceso de adopcion
                </Link>
              </li>
              <li>
                <Link href="/donate" className="text-sm hover:text-white">
                  Donar
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-sm hover:text-white">
                  Contacto
                </Link>
              </li>
            </ul>
          </div>

          {/* Contact info */}
          <div>
            <h3 className="text-sm font-semibold uppercase tracking-wider text-white">
              Contacto
            </h3>
            <ul className="mt-2 space-y-1 text-sm">
              <li>Paraguay</li>
              <li>info@refugioanimal.org.py</li>
            </ul>
          </div>
        </div>

        <div className="mt-8 border-t border-stone-700 pt-4 text-center text-xs">
          &copy; {currentYear} {APP_NAME}. Todos los derechos reservados.
        </div>
      </div>
    </footer>
  );
}
