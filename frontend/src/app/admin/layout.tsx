"use client";

import { usePathname } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";
import Breadcrumbs from "@/components/admin/Breadcrumbs";
import NotificationCenter from "@/components/NotificationCenter";

/**
 * Admin layout with sidebar navigation for staff/admin pages.
 * Login and auth pages render without the sidebar.
 *
 * Includes a top bar with the NotificationCenter bell icon for
 * real-time in-app notification access.
 */

const AUTH_PATHS = ["/admin/login", "/admin/forgot-password", "/admin/reset-password"];

export default function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage = AUTH_PATHS.some((p) => pathname.startsWith(p));

  if (isAuthPage) {
    return <div className="min-h-screen bg-warm-bg">{children}</div>;
  }

  return (
    <div className="flex min-h-screen bg-warm-bg">
      <AdminSidebar />
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top bar with notification center */}
        <header className="flex h-14 items-center justify-end border-b border-warm-border bg-warm-surface px-4 md:px-6">
          <NotificationCenter />
        </header>
        <main className="flex-1 overflow-auto px-4 pb-6 pt-4 md:px-6">
          <Breadcrumbs />
          {children}
        </main>
      </div>
    </div>
  );
}
