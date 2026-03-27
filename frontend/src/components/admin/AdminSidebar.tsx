"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  PawPrint,
  LayoutDashboard,
  List,
  Heart,
  Users,
  DollarSign,
  Megaphone,
  LogOut,
  Menu,
  X,
  Settings,
  Shield,
  Scissors,
  Syringe,
  Stethoscope,
  ClipboardList,
  Calendar,
} from "lucide-react";
import { useState } from "react";
import { clearAccessToken, getCurrentUserRole } from "@/lib/auth";
import { hasRoleAccess } from "@/lib/role-access";
import type { UserRole } from "@/types/api";

interface NavItem {
  label: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  /** If set, only users with this role (or higher) can see this item. */
  requiredRole?: UserRole;
}

const NAV_ITEMS: NavItem[] = [
  {
    label: "Panel",
    href: "/admin/dashboard",
    icon: LayoutDashboard,
  },
  {
    label: "Animales",
    href: "/admin/animals",
    icon: List,
  },
  {
    label: "Adopciones",
    href: "/admin/adoptions",
    icon: Heart,
  },
  {
    label: "Donantes",
    href: "/admin/donors",
    icon: Users,
  },
  {
    label: "Donaciones",
    href: "/admin/donations",
    icon: DollarSign,
  },
  {
    label: "Campanas",
    href: "/admin/campaigns",
    icon: Megaphone,
  },
  {
    label: "Cirugias",
    href: "/admin/surgeries",
    icon: Scissors,
  },
  {
    label: "Alertas Medicas",
    href: "/admin/medical/alerts",
    icon: Syringe,
  },
  {
    label: "Vacunaciones",
    href: "/admin/vaccinations",
    icon: Syringe,
  },
  {
    label: "Recetas",
    href: "/admin/prescriptions",
    icon: ClipboardList,
  },
  {
    label: "Citas Medicas",
    href: "/admin/appointments",
    icon: Calendar,
  },
  {
    label: "Panel Veterinario",
    href: "/admin/vet-dashboard",
    icon: Stethoscope,
  },
  {
    label: "Usuarios",
    href: "/admin/users",
    icon: Shield,
    requiredRole: "admin",
  },
  {
    label: "Configuracion",
    href: "/admin/settings",
    icon: Settings,
    requiredRole: "admin",
  },
];

const LABEL_SHELTER_NAME = "Refugio Animal";
const LABEL_ADMIN = "Administracion";
const LABEL_LOGOUT = "Cerrar Sesion";
const LABEL_TOGGLE_MENU = "Abrir menu";

function isActive(pathname: string, href: string): boolean {
  if (href === "/admin/dashboard") {
    return pathname === "/admin/dashboard" || pathname === "/admin";
  }
  return pathname.startsWith(href);
}

export default function AdminSidebar() {
  const pathname = usePathname();
  const router = useRouter();
  const [isMobileOpen, setIsMobileOpen] = useState(false);
  const userRole = getCurrentUserRole();
  const visibleItems = NAV_ITEMS.filter((item) => hasRoleAccess(userRole, item.requiredRole));

  function handleLogout() {
    clearAccessToken();
    router.replace("/admin/login");
  }

  function handleNavClick(href: string) {
    router.push(href);
    setIsMobileOpen(false);
  }

  const sidebarContent = (
    <div className="flex h-full flex-col">
      {/* Logo / Brand */}
      <div className="flex items-center gap-3 border-b border-warm-border px-4 py-4">
        <PawPrint className="h-7 w-7 text-primary-600" aria-hidden="true" />
        <div>
          <p className="text-sm font-bold text-warm-text-primary">
            {LABEL_SHELTER_NAME}
          </p>
          <p className="text-xs text-warm-text-tertiary">{LABEL_ADMIN}</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4" aria-label="Admin navigation">
        {visibleItems.map((item) => {
          const active = isActive(pathname, item.href);
          const Icon = item.icon;
          return (
            <button
              key={item.href}
              onClick={() => handleNavClick(item.href)}
              className={`flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors ${
                active
                  ? "bg-primary-50 text-primary-700"
                  : "text-warm-text-secondary hover:bg-warm-bg hover:text-warm-text-primary"
              }`}
              aria-current={active ? "page" : undefined}
            >
              <Icon
                className={`h-5 w-5 ${
                  active ? "text-primary-600" : "text-warm-text-tertiary"
                }`}
              />
              {item.label}
            </button>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="border-t border-warm-border px-3 py-4">
        <button
          onClick={handleLogout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-warm-text-secondary transition-colors hover:bg-red-50 hover:text-red-700"
        >
          <LogOut className="h-5 w-5" />
          {LABEL_LOGOUT}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 flex-shrink-0 border-r border-warm-border bg-warm-surface md:block">
        {sidebarContent}
      </aside>

      {/* Mobile hamburger button */}
      <button
        onClick={() => setIsMobileOpen(true)}
        className="fixed left-4 top-4 z-40 rounded-lg border border-warm-border bg-warm-surface p-2 shadow-sm md:hidden"
        aria-label={LABEL_TOGGLE_MENU}
      >
        <Menu className="h-5 w-5 text-warm-text-primary" />
      </button>

      {/* Mobile overlay */}
      {isMobileOpen && (
        <div className="fixed inset-0 z-50 md:hidden">
          {/* Backdrop */}
          <div
            className="absolute inset-0 bg-black/30"
            onClick={() => setIsMobileOpen(false)}
          />
          {/* Sidebar panel */}
          <aside className="relative h-full w-64 bg-warm-surface shadow-xl">
            <button
              onClick={() => setIsMobileOpen(false)}
              className="absolute right-3 top-3 rounded-lg p-1.5 text-warm-text-secondary hover:bg-warm-bg"
              aria-label="Cerrar menu"
            >
              <X className="h-5 w-5" />
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}
    </>
  );
}
