import Link from "next/link";
import { FOOTER } from "@/lib/strings";

const FOOTER_LINKS = {
  shelter: [
    { href: "/about", label: FOOTER.aboutUs },
    { href: "/animals", label: FOOTER.ourAnimals },
    { href: "/stories", label: FOOTER.stories },
    { href: "/contact", label: FOOTER.contact },
  ],
  support: [
    { href: "/donate", label: FOOTER.donate },
    { href: "/volunteer", label: FOOTER.volunteer },
    { href: "/foster", label: FOOTER.foster },
  ],
} as const;

const CURRENT_YEAR = new Date().getFullYear();

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-8">
          {/* Brand — full width on smallest screens */}
          <div className="col-span-2 sm:col-span-1">
            <div className="flex items-center space-x-2 mb-3">
              <span className="text-2xl" role="img" aria-label="Paw">
                {"\u{1F43E}"}
              </span>
              <span className="font-heading font-bold text-lg text-primary-700">
                {FOOTER.brand}
              </span>
            </div>
            <p className="text-gray-500 text-sm leading-relaxed">
              {FOOTER.tagline}
            </p>
          </div>

          {/* Shelter links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wider">
              {FOOTER.shelter}
            </h3>
            <ul className="space-y-2">
              {FOOTER_LINKS.shelter.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-500 hover:text-primary-600 text-sm transition-colors inline-flex items-center min-h-[44px]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          {/* Support links */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-3 text-sm uppercase tracking-wider">
              {FOOTER.supportUs}
            </h3>
            <ul className="space-y-2">
              {FOOTER_LINKS.support.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-gray-500 hover:text-primary-600 text-sm transition-colors inline-flex items-center min-h-[44px]"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Copyright */}
        <div className="mt-8 pt-6 border-t border-gray-200 text-center">
          <p className="text-gray-400 text-sm">
            {FOOTER.copyright(CURRENT_YEAR)}
          </p>
        </div>
      </div>

      {/* Bottom safe area padding for notched devices */}
      <div
        className="bg-gray-50"
        style={{ paddingBottom: "env(safe-area-inset-bottom)" }}
      />
    </footer>
  );
}
