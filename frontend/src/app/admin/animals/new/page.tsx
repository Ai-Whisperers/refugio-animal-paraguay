"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { PawPrint, ArrowLeft } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import AnimalForm from "@/components/admin/AnimalForm";

const LABEL_PAGE_TITLE = "Nuevo Animal";
const LABEL_BACK = "Volver a la lista";
const LABEL_LOADING = "Verificando sesion...";

export default function NewAnimalPage() {
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  if (isChecking) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b border-warm-border bg-warm-surface">
        <div className="mx-auto flex max-w-3xl items-center gap-3 px-4 py-3 sm:px-6 lg:px-8">
          <button
            onClick={() => router.push("/admin/animals")}
            className="rounded-lg p-1.5 text-warm-text-secondary transition-colors hover:bg-warm-bg hover:text-warm-text-primary"
            aria-label={LABEL_BACK}
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <PawPrint className="h-6 w-6 text-primary-600" aria-hidden="true" />
          <h1 className="text-lg font-semibold text-warm-text-primary">
            {LABEL_PAGE_TITLE}
          </h1>
        </div>
      </header>

      {/* Form */}
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
          <AnimalForm mode="create" />
        </div>
      </div>
    </div>
  );
}
