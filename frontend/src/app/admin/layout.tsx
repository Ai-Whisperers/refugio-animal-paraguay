"use client";

import { usePathname } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";
import Breadcrumbs from "@/components/admin/Breadcrumbs";

/**
 * Admin layout with sidebar navigation for staff/admin pages.
 * Login and auth pages render without the sidebar.
 */

const AUTH_PATHS = ["/admin/login", "/admin/forgot-password", "/admin/reset-password"];

export default function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const isAuthPage = AUTH_PATHS.some((p) => pathname.startsWith(p));

  // Auth pages get a plain layout without sidebar
  if (isAuthPage) {
    return <div className="min-h-screen bg-warm-bg">{children}</div>;
  }

  return (
    <div className="flex min-h-screen bg-warm-bg">
      <AdminSidebar />
      <main className="flex-1 overflow-auto p-6">
        <Breadcrumbs />
        {children}
      </main>
    </div>
  );
}
