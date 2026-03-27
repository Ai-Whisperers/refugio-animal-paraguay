"use client";

import { useEffect, useState, useCallback } from "react";
import { Settings, UserPlus, Check, X, Loader2 } from "lucide-react";
import { api } from "@/lib/api";

interface RoleInfo {
  role: string;
  label: string;
  description: string;
  assigned: boolean;
}

interface UserRolesData {
  roles: string[];
  available_roles: RoleInfo[];
}

interface RoleActionResult {
  roles: string[];
  message: string;
}

const ROLE_ICONS: Record<string, string> = {
  adopter: "\u{1F43E}",
  donor: "\u{1F49B}",
  volunteer: "\u{1F91D}",
  foster: "\u{1F3E0}",
};

const ROLE_LABELS: Record<string, string> = {
  adopter: "Adoptante",
  donor: "Donante",
  volunteer: "Voluntario/a",
  foster: "Hogar transitorio",
};

const ROLE_DESCRIPTIONS: Record<string, string> = {
  adopter: "Buscar y adoptar animales del refugio",
  donor: "Apoyar a los animales con donaciones",
  volunteer: "Ayudar con el cuidado, transporte y eventos",
  foster: "Cuidar temporalmente animales en tu hogar",
};

export default function PortalSettingsPage() {
  const [rolesData, setRolesData] = useState<UserRolesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchRoles = useCallback(async () => {
    try {
      const data = await api.get<UserRolesData>("/api/users/roles");
      setRolesData(data);
    } catch {
      setErrorMessage("Error al cargar los roles.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRoles();
  }, [fetchRoles]);

  async function handleRoleToggle(role: string, currentlyAssigned: boolean) {
    setActionLoading(role);
    setSuccessMessage(null);
    setErrorMessage(null);

    try {
      const result = await api.post<RoleActionResult>("/api/users/roles", {
        role,
        action: currentlyAssigned ? "remove" : "add",
      });
      setRolesData((prev) =>
        prev
          ? {
              ...prev,
              roles: result.roles,
              available_roles: prev.available_roles.map((r) => ({
                ...r,
                assigned: result.roles.includes(r.role),
              })),
            }
          : null
      );
      setSuccessMessage(result.message);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Error al actualizar el rol.";
      setErrorMessage(message);
    } finally {
      setActionLoading(null);
    }
  }

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center bg-gray-50">
        <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-md p-8">
          <div className="flex items-center gap-3 mb-6">
            <Settings className="h-8 w-8 text-amber-500" />
            <h1 className="text-2xl font-bold text-gray-900">Configuracion</h1>
          </div>

          {/* Success message */}
          {successMessage && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm flex items-center gap-2">
              <Check className="h-4 w-4" />
              {successMessage}
            </div>
          )}

          {/* Error message */}
          {errorMessage && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm flex items-center gap-2">
              <X className="h-4 w-4" />
              {errorMessage}
            </div>
          )}

          {/* Current roles */}
          <section className="mb-8">
            <h2 className="text-lg font-semibold text-gray-800 mb-3">
              Mis roles
            </h2>
            <div className="flex flex-wrap gap-2">
              {rolesData?.roles.map((role) => (
                <span
                  key={role}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-amber-50 text-amber-800 rounded-full text-sm font-medium border border-amber-200"
                >
                  <span>{ROLE_ICONS[role] || ""}</span>
                  {ROLE_LABELS[role] || role}
                </span>
              ))}
            </div>
          </section>

          {/* Role management */}
          <section>
            <div className="flex items-center gap-2 mb-4">
              <UserPlus className="h-5 w-5 text-gray-600" />
              <h2 className="text-lg font-semibold text-gray-800">
                Gestionar roles
              </h2>
            </div>

            <p className="text-sm text-gray-500 mb-4">
              Puedes tener multiples roles. Selecciona los que se ajusten a como
              quieres participar.
            </p>

            <div className="space-y-3">
              {rolesData?.available_roles.map((roleInfo) => {
                const isLoading = actionLoading === roleInfo.role;
                const canRemove =
                  roleInfo.assigned && (rolesData?.roles.length ?? 0) > 1;

                return (
                  <div
                    key={roleInfo.role}
                    className={`flex items-center justify-between p-4 rounded-lg border transition-colors ${
                      roleInfo.assigned
                        ? "bg-amber-50 border-amber-200"
                        : "bg-white border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-2xl">
                        {ROLE_ICONS[roleInfo.role] || ""}
                      </span>
                      <div>
                        <p className="font-medium text-gray-900">
                          {ROLE_LABELS[roleInfo.role] || roleInfo.label}
                        </p>
                        <p className="text-sm text-gray-500">
                          {ROLE_DESCRIPTIONS[roleInfo.role] ||
                            roleInfo.description}
                        </p>
                      </div>
                    </div>

                    <button
                      onClick={() =>
                        handleRoleToggle(roleInfo.role, roleInfo.assigned)
                      }
                      disabled={
                        isLoading ||
                        (roleInfo.assigned && !canRemove)
                      }
                      className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                        roleInfo.assigned
                          ? "bg-white text-red-600 border border-red-200 hover:bg-red-50"
                          : "bg-amber-500 text-white hover:bg-amber-600"
                      }`}
                    >
                      {isLoading ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : roleInfo.assigned ? (
                        "Quitar"
                      ) : (
                        "Agregar"
                      )}
                    </button>
                  </div>
                );
              })}
            </div>

            {rolesData?.roles.length === 1 && (
              <p className="mt-3 text-xs text-gray-400">
                Debes tener al menos un rol activo.
              </p>
            )}
          </section>
        </div>
      </div>
    </main>
  );
}
