"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { Home, Search, Heart, HandCoins, Menu } from "lucide-react";
import { useState } from "react";
import { NAV } from "@/lib/strings";

interface BottomNavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
}

const BOTTOM_NAV_ITEMS: BottomNavItem[] = [
  { href: "/", label: NAV.home, icon: Home },
  { href: "/animals", label: NAV.animals, icon: Search },
  { href: "/donate", label: NAV.donate, icon: HandCoins },
  { href: "/stories", label: "Historias", icon: Heart },
];

const MORE_ITEMS: { href: string; label: string }[] = [
  { href: "/about", label: NAV.about },
  { href: "/contact", label: NAV.contact },
];

/**
 * App-like bottom navigation bar for mobile devices.
 *
 * Shows 4 primary destinations + a "More" menu.
 * Hidden on screens >= md breakpoint where the top navbar handles navigation.
 * Uses 44px minimum touch targets per WCAG 2.1 guidelines.
 */
export default function BottomNav() {
  const pathname = usePathname();
  const [isMoreOpen, setIsMoreOpen] = useState(false);

  // Hide on admin pages — admin has its own sidebar
  if (pathname.startsWith("/admin")) return null;

  function isActive(href: string): boolean {
    if (href === "/") return pathname === "/";
    return pathname.startsWith(href);
  }

  const isMoreActive = MORE_ITEMS.some((item) => pathname.startsWith(item.href));

  return (
    <>
      {/* Spacer to prevent content from being hidden behind fixed bottom nav */}
      <div className="h-16 md:hidden" aria-hidden="true" />

      {/* More menu popover */}
      {isMoreOpen && (
        <div className="fixed inset-0 z-40 md:hidden" onClick={() => setIsMoreOpen(false)}>
          <div className="absolute bottom-16 left-0 right-0 bg-white border-t border-gray-200 shadow-lg">
            <div className="max-w-lg mx-auto px-4 py-2">
              {MORE_ITEMS.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                    pathname.startsWith(item.href)
                      ? "text-primary-600 bg-primary-50"
                      : "text-gray-700 hover:text-primary-600 hover:bg-gray-50"
                  }`}
                  onClick={() => setIsMoreOpen(false)}
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Bottom navigation bar */}
      <nav
        className="fixed bottom-0 left-0 right-0 z-30 bg-white border-t border-gray-200 shadow-[0_-2px_10px_rgba(0,0,0,0.05)] md:hidden"
        role="navigation"
        aria-label="Navegacion principal"
      >
        <div className="max-w-lg mx-auto flex items-center justify-around h-16 px-2">
          {BOTTOM_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex flex-col items-center justify-center min-w-[64px] min-h-[44px] px-1 py-1 rounded-lg transition-colors ${
                  active
                    ? "text-primary-600"
                    : "text-gray-500 hover:text-primary-600"
                }`}
                aria-current={active ? "page" : undefined}
              >
                <Icon className={`h-5 w-5 ${active ? "text-primary-600" : ""}`} />
                <span className={`text-[10px] mt-0.5 leading-tight ${active ? "font-semibold" : "font-medium"}`}>
                  {item.label}
                </span>
              </Link>
            );
          })}

          {/* More button */}
          <button
            onClick={() => setIsMoreOpen(!isMoreOpen)}
            className={`flex flex-col items-center justify-center min-w-[64px] min-h-[44px] px-1 py-1 rounded-lg transition-colors ${
              isMoreActive || isMoreOpen
                ? "text-primary-600"
                : "text-gray-500 hover:text-primary-600"
            }`}
            aria-expanded={isMoreOpen}
            aria-label="Mas opciones"
          >
            <Menu className={`h-5 w-5 ${isMoreActive || isMoreOpen ? "text-primary-600" : ""}`} />
            <span className={`text-[10px] mt-0.5 leading-tight ${isMoreActive || isMoreOpen ? "font-semibold" : "font-medium"}`}>
              Mas
            </span>
          </button>
        </div>
      </nav>
    </>
  );
}
