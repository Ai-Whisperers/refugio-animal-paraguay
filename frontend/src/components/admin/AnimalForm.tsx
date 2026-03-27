"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Save, X, Upload, Trash2 } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import type { AnimalSpecies, AnimalStatus, AnimalPhoto } from "@/types/api";

// --- Labels (Spanish) ---
const LABEL_NAME = "Nombre";
const LABEL_SPECIES = "Especie";
const LABEL_STATUS = "Estado";
const LABEL_BREED = "Raza";
const LABEL_GENDER = "Genero";
const LABEL_SIZE = "Tamano";
const LABEL_BIRTH_DATE = "Fecha de nacimiento";
const LABEL_DESCRIPTION = "Descripcion";
const LABEL_PHOTO_URL = "URL de foto principal";
const LABEL_SAVE = "Guardar";
const LABEL_CANCEL = "Cancelar";
const LABEL_SAVING = "Guardando...";
const LABEL_REQUIRED = "Este campo es obligatorio";
const LABEL_ADD_PHOTO = "Agregar foto a galeria";
const LABEL_PHOTO_URL_LABEL = "URL de la foto";
const LABEL_PHOTO_CAPTION = "Descripcion de la foto";
const LABEL_PHOTOS = "Galeria de fotos";
const LABEL_NO_PHOTOS = "Sin fotos en la galeria";
const LABEL_PHOTO_ADDED = "Foto agregada";

const SPECIES_OPTIONS: { value: AnimalSpecies; label: string }[] = [
  { value: "dog", label: "Perro" },
  { value: "cat", label: "Gato" },
  { value: "other", label: "Otro" },
];

const STATUS_OPTIONS: { value: AnimalStatus; label: string }[] = [
  { value: "intake", label: "Ingreso" },
  { value: "quarantine", label: "Cuarentena" },
  { value: "available", label: "Disponible" },
  { value: "foster", label: "Acogida" },
  { value: "under_treatment", label: "En tratamiento" },
  { value: "adopted", label: "Adoptado" },
  { value: "deceased", label: "Fallecido" },
];

const GENDER_OPTIONS = [
  { value: "", label: "Sin especificar" },
  { value: "male", label: "Macho" },
  { value: "female", label: "Hembra" },
  { value: "unknown", label: "Desconocido" },
];

const SIZE_OPTIONS = [
  { value: "", label: "Sin especificar" },
  { value: "small", label: "Pequeno" },
  { value: "medium", label: "Mediano" },
  { value: "large", label: "Grande" },
  { value: "extra_large", label: "Extra grande" },
];

interface AnimalFormData {
  name: string;
  species: AnimalSpecies;
  status: AnimalStatus;
  breed: string;
  gender: string;
  size: string;
  birth_date: string;
  description: string;
  primary_photo_url: string;
}

interface AnimalFormProps {
  mode: "create" | "edit";
  initialData?: Partial<AnimalFormData>;
  animalId?: string;
  existingPhotos?: AnimalPhoto[];
  onSuccess?: () => void;
}

export default function AnimalForm({
  mode,
  initialData,
  animalId,
  existingPhotos = [],
  onSuccess,
}: AnimalFormProps) {
  const router = useRouter();
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [nameError, setNameError] = useState<string | null>(null);

  const [formData, setFormData] = useState<AnimalFormData>({
    name: initialData?.name ?? "",
    species: initialData?.species ?? "dog",
    status: initialData?.status ?? "intake",
    breed: initialData?.breed ?? "",
    gender: initialData?.gender ?? "",
    size: initialData?.size ?? "",
    birth_date: initialData?.birth_date ?? "",
    description: initialData?.description ?? "",
    primary_photo_url: initialData?.primary_photo_url ?? "",
  });

  // Photo gallery state
  const [photos, setPhotos] = useState<AnimalPhoto[]>(existingPhotos);
  const [newPhotoUrl, setNewPhotoUrl] = useState("");
  const [newPhotoCaption, setNewPhotoCaption] = useState("");
  const [photoMessage, setPhotoMessage] = useState<string | null>(null);

  function handleChange(
    field: keyof AnimalFormData,
    value: string
  ) {
    setFormData((prev) => ({ ...prev, [field]: value }));
    if (field === "name") {
      setNameError(null);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    // Validate name
    if (!formData.name.trim()) {
      setNameError(LABEL_REQUIRED);
      return;
    }

    setIsSaving(true);
    try {
      const payload: Record<string, unknown> = {
        name: formData.name.trim(),
        species: formData.species,
        status: formData.status,
      };

      if (formData.breed.trim()) payload.breed = formData.breed.trim();
      if (formData.gender) payload.gender = formData.gender;
      if (formData.size) payload.size = formData.size;
      if (formData.birth_date) payload.birth_date = formData.birth_date;
      if (formData.description.trim()) payload.description = formData.description.trim();
      if (formData.primary_photo_url.trim()) payload.primary_photo_url = formData.primary_photo_url.trim();

      if (mode === "create") {
        await api.post("/animals", payload);
      } else if (animalId) {
        await api.patch(`/animals/${animalId}`, payload);
      }

      if (onSuccess) {
        onSuccess();
      } else {
        router.push("/admin/animals");
      }
    } catch (err) {
      if (err instanceof ApiClientError) {
        setError(err.detail);
      } else {
        setError("Error al guardar el animal");
      }
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAddPhoto() {
    if (!animalId || !newPhotoUrl.trim()) return;
    setPhotoMessage(null);

    try {
      const photo = await api.post<AnimalPhoto>(`/animals/${animalId}/photos`, {
        url: newPhotoUrl.trim(),
        caption: newPhotoCaption.trim() || null,
        display_order: photos.length,
      });
      setPhotos((prev) => [...prev, photo]);
      setNewPhotoUrl("");
      setNewPhotoCaption("");
      setPhotoMessage(LABEL_PHOTO_ADDED);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setPhotoMessage(err.detail);
      }
    }
  }

  async function handleDeletePhoto(photoId: string) {
    if (!animalId) return;
    try {
      await api.delete(`/animals/${animalId}/photos/${photoId}`);
      setPhotos((prev) => prev.filter((p) => p.id !== photoId));
    } catch (err) {
      if (err instanceof ApiClientError) {
        setPhotoMessage(err.detail);
      }
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Error banner */}
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {/* Name (required) */}
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-warm-text-primary">
          {LABEL_NAME} *
        </label>
        <input
          id="name"
          type="text"
          value={formData.name}
          onChange={(e) => handleChange("name", e.target.value)}
          className={`mt-1 w-full rounded-lg border px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:outline-none focus:ring-1 ${
            nameError
              ? "border-red-300 focus:border-red-500 focus:ring-red-500"
              : "border-warm-border focus:border-primary-500 focus:ring-primary-500"
          }`}
          placeholder="Ej: Luna"
        />
        {nameError && <p className="mt-1 text-xs text-red-600">{nameError}</p>}
      </div>

      {/* Species + Status row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="species" className="block text-sm font-medium text-warm-text-primary">
            {LABEL_SPECIES}
          </label>
          <select
            id="species"
            value={formData.species}
            onChange={(e) => handleChange("species", e.target.value)}
            className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {SPECIES_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="status" className="block text-sm font-medium text-warm-text-primary">
            {LABEL_STATUS}
          </label>
          <select
            id="status"
            value={formData.status}
            onChange={(e) => handleChange("status", e.target.value)}
            className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Breed + Gender + Size row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div>
          <label htmlFor="breed" className="block text-sm font-medium text-warm-text-primary">
            {LABEL_BREED}
          </label>
          <input
            id="breed"
            type="text"
            value={formData.breed}
            onChange={(e) => handleChange("breed", e.target.value)}
            className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            placeholder="Ej: Mestizo"
          />
        </div>

        <div>
          <label htmlFor="gender" className="block text-sm font-medium text-warm-text-primary">
            {LABEL_GENDER}
          </label>
          <select
            id="gender"
            value={formData.gender}
            onChange={(e) => handleChange("gender", e.target.value)}
            className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {GENDER_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>

        <div>
          <label htmlFor="size" className="block text-sm font-medium text-warm-text-primary">
            {LABEL_SIZE}
          </label>
          <select
            id="size"
            value={formData.size}
            onChange={(e) => handleChange("size", e.target.value)}
            className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          >
            {SIZE_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Birth date */}
      <div>
        <label htmlFor="birth_date" className="block text-sm font-medium text-warm-text-primary">
          {LABEL_BIRTH_DATE}
        </label>
        <input
          id="birth_date"
          type="date"
          value={formData.birth_date}
          onChange={(e) => handleChange("birth_date", e.target.value)}
          className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
        />
      </div>

      {/* Description */}
      <div>
        <label htmlFor="description" className="block text-sm font-medium text-warm-text-primary">
          {LABEL_DESCRIPTION}
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleChange("description", e.target.value)}
          rows={3}
          className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          placeholder="Descripcion del animal..."
        />
      </div>

      {/* Primary photo URL */}
      <div>
        <label htmlFor="primary_photo_url" className="block text-sm font-medium text-warm-text-primary">
          {LABEL_PHOTO_URL}
        </label>
        <input
          id="primary_photo_url"
          type="url"
          value={formData.primary_photo_url}
          onChange={(e) => handleChange("primary_photo_url", e.target.value)}
          className="mt-1 w-full rounded-lg border border-warm-border px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          placeholder="https://example.com/photo.jpg"
        />
        {formData.primary_photo_url && (
          <div className="mt-2">
            <img
              src={formData.primary_photo_url}
              alt="Vista previa"
              className="h-24 w-24 rounded-lg object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = "none";
              }}
            />
          </div>
        )}
      </div>

      {/* Photo gallery (edit mode only) */}
      {mode === "edit" && animalId && (
        <div className="border-t border-warm-border pt-6">
          <h3 className="mb-3 text-sm font-medium text-warm-text-primary">
            {LABEL_PHOTOS}
          </h3>

          {photos.length === 0 && (
            <p className="mb-3 text-sm text-warm-text-tertiary">{LABEL_NO_PHOTOS}</p>
          )}

          {photos.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-3">
              {photos.map((photo) => (
                <div key={photo.id} className="relative group">
                  <img
                    src={photo.url}
                    alt={photo.caption ?? "Foto del animal"}
                    className="h-20 w-20 rounded-lg object-cover"
                  />
                  <button
                    type="button"
                    onClick={() => handleDeletePhoto(photo.id)}
                    className="absolute -right-1 -top-1 hidden rounded-full bg-red-500 p-0.5 text-white group-hover:block"
                    aria-label="Eliminar foto"
                  >
                    <Trash2 className="h-3 w-3" />
                  </button>
                </div>
              ))}
            </div>
          )}

          {/* Add photo form */}
          <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
            <div className="flex-1">
              <label htmlFor="new-photo-url" className="block text-xs text-warm-text-secondary">
                {LABEL_PHOTO_URL_LABEL}
              </label>
              <input
                id="new-photo-url"
                type="url"
                value={newPhotoUrl}
                onChange={(e) => setNewPhotoUrl(e.target.value)}
                className="mt-1 w-full rounded-lg border border-warm-border px-3 py-1.5 text-sm"
                placeholder="https://example.com/photo.jpg"
              />
            </div>
            <div className="flex-1">
              <label htmlFor="new-photo-caption" className="block text-xs text-warm-text-secondary">
                {LABEL_PHOTO_CAPTION}
              </label>
              <input
                id="new-photo-caption"
                type="text"
                value={newPhotoCaption}
                onChange={(e) => setNewPhotoCaption(e.target.value)}
                className="mt-1 w-full rounded-lg border border-warm-border px-3 py-1.5 text-sm"
                placeholder="Opcional"
              />
            </div>
            <button
              type="button"
              onClick={handleAddPhoto}
              disabled={!newPhotoUrl.trim()}
              className="flex items-center gap-1 rounded-lg bg-primary-600 px-3 py-1.5 text-sm text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
            >
              <Upload className="h-4 w-4" />
              {LABEL_ADD_PHOTO}
            </button>
          </div>
          {photoMessage && (
            <p className="mt-1 text-xs text-warm-text-secondary">{photoMessage}</p>
          )}
        </div>
      )}

      {/* Action buttons */}
      <div className="flex items-center gap-3 border-t border-warm-border pt-6">
        <button
          type="submit"
          disabled={isSaving}
          className="flex items-center gap-1.5 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {isSaving ? LABEL_SAVING : LABEL_SAVE}
        </button>
        <button
          type="button"
          onClick={() => router.push("/admin/animals")}
          className="flex items-center gap-1.5 rounded-lg border border-warm-border px-4 py-2 text-sm text-warm-text-secondary transition-colors hover:bg-warm-bg"
        >
          <X className="h-4 w-4" />
          {LABEL_CANCEL}
        </button>
      </div>
    </form>
  );
}
