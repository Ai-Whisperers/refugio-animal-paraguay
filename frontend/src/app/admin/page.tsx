"use client";

/**
 * Admin dashboard overview page.
 * Shows quick stats and links to management sections.
 */

import Link from "next/link";
import { useAuth } from "@/contexts/AuthContext";

const QUICK_LINKS = [
  {
    href: "/admin/animals",
    title: "Manage Animals",
    description: "View, add, edit, and remove animal records",
    color: "bg-primary-50 border-primary-200 hover:bg-primary-100",
  },
  {
    href: "/admin/adoptions",
    title: "Adoption Requests",
    description: "Review and process adoption applications",
    color: "bg-accent-50 border-accent-200 hover:bg-accent-100",
  },
] as const;

export default function AdminDashboard() {
  const { user } = useAuth();

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back{user ? `, ${user.email.split("@")[0]}` : ""}
        </h1>
        <p className="text-gray-500 mt-1">
          Refugio Animal Paraguay &mdash; Staff Administration
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {QUICK_LINKS.map((link) => (
          <Link
            key={link.href}
            href={link.href}
            className={`block p-6 rounded-lg border-2 transition-colors ${link.color}`}
          >
            <h2 className="text-lg font-semibold text-gray-900">
              {link.title}
            </h2>
            <p className="text-sm text-gray-600 mt-1">{link.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
