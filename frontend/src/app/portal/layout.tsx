"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { isAuthenticated } from "@/lib/auth";

/**
 * Portal layout: wraps all /portal/* pages.
 * Redirects to login if the user is not authenticated.
 */
export default function PortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login");
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6">
          <h1 className="text-lg font-semibold text-gray-900">
            Refugio Animal Paraguay
          </h1>
          <nav className="flex items-center gap-4 text-sm text-gray-600">
            <a href="/portal/dashboard" className="hover:text-green-700">
              Mi Panel
            </a>
            <a href="/animals" className="hover:text-green-700">
              Animales
            </a>
            <a href="/donate" className="hover:text-green-700">
              Donar
            </a>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6">{children}</main>
    </div>
  );
}
