"use client";

import { useEffect, useState } from "react";
import { useRouter, useParams } from "next/navigation";
import { PawPrint, ArrowLeft, RefreshCw } from "lucide-react";
import { isAuthenticated } from "@/lib/auth";
import { api, ApiClientError } from "@/lib/api";
import AnimalForm from "@/components/admin/AnimalForm";
import type { Animal } from "@/types/api";

const LABEL_PAGE_TITLE = "Editar Animal";
const LABEL_BACK = "Volver a la lista";
const LABEL_LOADING = "Cargando animal...";
const LABEL_ERROR = "Error al cargar el animal";
const LABEL_NOT_FOUND = "Animal no encontrado";
const LABEL_RETRY = "Reintentar";

export default function EditAnimalPage() {
  const router = useRouter();
  const params = useParams();
  const animalId = params.id as string;

  const [isChecking, setIsChecking] = useState(true);
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.replace("/admin/login?expired=true");
      return;
    }
    setIsChecking(false);
  }, [router]);

  useEffect(() => {
    if (isChecking || !animalId) return;

    async function fetchAnimal() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await api.get<Animal>(`/animals/${animalId}`);
        setAnimal(data);
      } catch (err) {
        if (err instanceof ApiClientError && err.statusCode === 404) {
          setError(LABEL_NOT_FOUND);
        } else if (err instanceof ApiClientError) {
          setError(`${LABEL_ERROR}: ${err.detail}`);
        } else {
          setError(LABEL_ERROR);
        }
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnimal();
  }, [isChecking, animalId]);

  if (isChecking || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <RefreshCw className="mr-2 h-5 w-5 animate-spin text-primary-500" />
        <p className="text-warm-text-secondary">{LABEL_LOADING}</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-4">
        <p className="text-warm-text-secondary">{error}</p>
        <button
          onClick={() => window.location.reload()}
          className="text-sm font-medium text-primary-600 underline hover:text-primary-700"
        >
          {LABEL_RETRY}
        </button>
      </div>
    );
  }

  if (!animal) return null;

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
            {LABEL_PAGE_TITLE}: {animal.name}
          </h1>
        </div>
      </header>

      {/* Form */}
      <div className="mx-auto max-w-3xl px-4 py-6 sm:px-6 lg:px-8">
        <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
          <AnimalForm
            mode="edit"
            animalId={animalId}
            initialData={{
              name: animal.name,
              species: animal.species,
              status: animal.status,
              breed: animal.breed ?? "",
              gender: animal.gender ?? "",
              size: animal.size ?? "",
              birth_date: animal.birth_date ?? "",
              description: animal.description ?? "",
              primary_photo_url: animal.primary_photo_url ?? "",
            }}
            existingPhotos={animal.photos}
          />
        </div>
      </div>
    </div>
  );
}
