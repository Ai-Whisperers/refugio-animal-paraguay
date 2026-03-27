"use client";

import { usePathname } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Home } from "lucide-react";

/**
 * Human-readable labels for admin URL segments (Spanish).
 * Segments not in this map are title-cased automatically.
 * UUID-like segments are skipped in display (shown as "Detalle").
 */
const SEGMENT_LABELS: Record<string, string> = {
  admin: "Admin",
  dashboard: "Panel",
  animals: "Animales",
  adoptions: "Adopciones",
  donors: "Donantes",
  donations: "Donaciones",
  users: "Usuarios",
  settings: "Configuracion",
  analytics: "Analiticas",
  new: "Nuevo",
  edit: "Editar",
};

const LABEL_DETAIL = "Detalle";

/** Matches UUID v4 pattern or any long hex-like string (common DB IDs). */
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const NUMERIC_PATTERN = /^\d+$/;

function isIdSegment(segment: string): boolean {
  return UUID_PATTERN.test(segment) || NUMERIC_PATTERN.test(segment);
}

function getSegmentLabel(segment: string): string {
  if (isIdSegment(segment)) return LABEL_DETAIL;
  return SEGMENT_LABELS[segment] ?? segment.charAt(0).toUpperCase() + segment.slice(1);
}

interface BreadcrumbItem {
  label: string;
  href: string;
}

export function buildBreadcrumbs(pathname: string): BreadcrumbItem[] {
  const segments = pathname.split("/").filter(Boolean);
  const items: BreadcrumbItem[] = [];

  for (let i = 0; i < segments.length; i++) {
    const href = "/" + segments.slice(0, i + 1).join("/");
    const label = getSegmentLabel(segments[i]);
    items.push({ label, href });
  }

  return items;
}

export default function Breadcrumbs() {
  const pathname = usePathname();
  const items = buildBreadcrumbs(pathname);

  // Don't render breadcrumbs on the root admin page or dashboard
  if (items.length <= 2) return null;

  return (
    <nav aria-label="Breadcrumb" className="mb-4">
      <ol className="flex items-center gap-1.5 text-sm text-warm-text-tertiary">
        <li>
          <Link
            href="/admin/dashboard"
            className="flex items-center gap-1 hover:text-warm-text-primary transition-colors"
          >
            <Home className="h-3.5 w-3.5" />
            <span className="sr-only">Admin</span>
          </Link>
        </li>
        {items.slice(1).map((item, index) => {
          const isLast = index === items.length - 2;
          return (
            <li key={item.href} className="flex items-center gap-1.5">
              <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
              {isLast ? (
                <span className="font-medium text-warm-text-primary" aria-current="page">
                  {item.label}
                </span>
              ) : (
                <Link
                  href={item.href}
                  className="hover:text-warm-text-primary transition-colors"
                >
                  {item.label}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
