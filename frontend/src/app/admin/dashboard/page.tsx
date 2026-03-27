"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PawPrint, LogOut } from "lucide-react";
import { isAuthenticated, clearAccessToken, getAccessToken, decodeToken } from "@/lib/auth";
import type { UserRole } from "@/types/api";

const LABEL_DASHBOARD = "Panel de Administracion";
const LABEL_WELCOME = "Bienvenido al panel de administracion";
const LABEL_LOGOUT = "Cerrar Sesion";
const LABEL_LOADING = "Verificando sesion...";

export default function AdminDashboardPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);
  const [userRole, setUserRole] = useState<UserRole | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }

    const token = getAccessToken();
    if (token) {
      const payload = decodeToken(token);
      if (payload) {
        setUserRole(payload.role);
      }
    }
    setIsChecking(false);
  }, [router]);

  function handleLogout() {
    clearAccessToken();
    router.replace("/admin/login");
  }

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Admin header bar */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          <div className="flex items-center gap-3">
            <PawPrint className="h-6 w-6 text-primary-600" aria-hidden="true" />
            <h1 className="text-lg font-semibold text-warm-text-primary">
              {LABEL_DASHBOARD}
            </h1>
          </div>
          <div className="flex items-center gap-4">
            {userRole && (
              <span className="rounded-full bg-primary-100 px-3 py-1 text-xs font-medium text-primary-700 capitalize">
                {userRole}
              </span>
            )}
            <button
              onClick={handleLogout}
              className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              {LABEL_LOGOUT}
            </button>
          </div>
        </div>
      </header>

      {/* Dashboard content placeholder */}
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-warm-border bg-warm-surface p-8 text-center">
          <PawPrint className="mx-auto h-12 w-12 text-primary-300" aria-hidden="true" />
          <h2 className="mt-4 text-lg font-medium text-warm-text-primary">
            {LABEL_WELCOME}
          </h2>
          <p className="mt-2 text-sm text-warm-text-secondary">
            Aqui podras gestionar animales, adopciones, donaciones y mas.
          </p>
        </div>
      </div>
    </div>
  );
}
