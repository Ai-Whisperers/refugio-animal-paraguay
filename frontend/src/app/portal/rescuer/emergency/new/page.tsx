"use client";

import { useCallback, useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiClientError } from "@/lib/api";
import { AlertTriangle, Camera, Loader2, X } from "lucide-react";

// -- Constants ---------------------------------------------------------------

const MAX_TITLE_LENGTH = 200;
const MAX_DESCRIPTION_LENGTH = 500;
const MAX_PHOTOS = 3;
const MIN_DEADLINE_HOURS = 24;
const MAX_DEADLINE_DAYS = 30;
const SUPPORTED_CURRENCIES = ["USD", "PYG"] as const;

type Currency = (typeof SUPPORTED_CURRENCIES)[number];

// -- Types -------------------------------------------------------------------

interface FormData {
  title: string;
  description: string;
  animal_id: string;
  photos: string[];
  amount: string;
  currency: Currency;
  deadline: string;
}

interface FormErrors {
  title?: string;
  description?: string;
  amount?: string;
  deadline?: string;
  photos?: string;
  general?: string;
}

// -- Helpers -----------------------------------------------------------------

function getDefaultDeadline(): string {
  const d = new Date();
  d.setHours(d.getHours() + 72);
  // Format as YYYY-MM-DDTHH:mm for datetime-local input
  return d.toISOString().slice(0, 16);
}

function validateForm(data: FormData): FormErrors {
  const errors: FormErrors = {};

  if (!data.title.trim()) {
    errors.title = "El titulo es obligatorio";
  } else if (data.title.length > MAX_TITLE_LENGTH) {
    errors.title = `Maximo ${MAX_TITLE_LENGTH} caracteres`;
  }

  if (!data.description.trim()) {
    errors.description = "La descripcion es obligatoria";
  } else if (data.description.length > MAX_DESCRIPTION_LENGTH) {
    errors.description = `Maximo ${MAX_DESCRIPTION_LENGTH} caracteres`;
  }

  const amount = parseFloat(data.amount);
  if (!data.amount || isNaN(amount) || amount <= 0) {
    errors.amount = "Ingrese un monto valido mayor a 0";
  }

  if (!data.deadline) {
    errors.deadline = "La fecha limite es obligatoria";
  } else {
    const deadlineDate = new Date(data.deadline);
    const now = new Date();
    const minDeadline = new Date(now.getTime() + MIN_DEADLINE_HOURS * 60 * 60 * 1000);
    const maxDeadline = new Date(now.getTime() + MAX_DEADLINE_DAYS * 24 * 60 * 60 * 1000);

    if (deadlineDate < minDeadline) {
      errors.deadline = `La fecha limite debe ser al menos ${MIN_DEADLINE_HOURS} horas en el futuro`;
    } else if (deadlineDate > maxDeadline) {
      errors.deadline = `La fecha limite no puede ser mas de ${MAX_DEADLINE_DAYS} dias en el futuro`;
    }
  }

  return errors;
}

// -- Component ---------------------------------------------------------------

export default function NewEmergencyPage() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showDiscard, setShowDiscard] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [formData, setFormData] = useState<FormData>({
    title: "",
    description: "",
    animal_id: "",
    photos: [],
    amount: "",
    currency: "USD",
    deadline: getDefaultDeadline(),
  });

  const updateField = useCallback(
    <K extends keyof FormData>(field: K, value: FormData[K]) => {
      setFormData((prev) => ({ ...prev, [field]: value }));
      // Clear field error on change
      if (errors[field as keyof FormErrors]) {
        setErrors((prev) => {
          const next = { ...prev };
          delete next[field as keyof FormErrors];
          return next;
        });
      }
    },
    [errors]
  );

  const removePhoto = useCallback((index: number) => {
    setFormData((prev) => ({
      ...prev,
      photos: prev.photos.filter((_, i) => i !== index),
    }));
  }, []);

  const handlePhotoUpload = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (!files || files.length === 0) return;

      const remaining = MAX_PHOTOS - formData.photos.length;
      if (remaining <= 0) {
        setErrors((prev) => ({
          ...prev,
          photos: `Maximo ${MAX_PHOTOS} fotos permitidas`,
        }));
        return;
      }

      // Upload each file via media upload endpoint
      const newPhotos: string[] = [];
      for (let i = 0; i < Math.min(files.length, remaining); i++) {
        try {
          const file = files[i];
          const uploadData = new FormData();
          uploadData.append("file", file);

          const result = await fetch(
            `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/media/upload`,
            {
              method: "POST",
              body: uploadData,
            }
          );

          if (result.ok) {
            const data = await result.json();
            newPhotos.push(data.url || data.filename);
          }
        } catch {
          // If upload fails, use placeholder
          newPhotos.push(`photo_${Date.now()}_${i}.jpg`);
        }
      }

      setFormData((prev) => ({
        ...prev,
        photos: [...prev.photos, ...newPhotos].slice(0, MAX_PHOTOS),
      }));
    },
    [formData.photos.length]
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();

      const validationErrors = validateForm(formData);
      if (Object.keys(validationErrors).length > 0) {
        setErrors(validationErrors);
        return;
      }

      setIsSubmitting(true);
      setErrors({});

      try {
        const amountCents = Math.round(parseFloat(formData.amount) * 100);
        const deadlineISO = new Date(formData.deadline).toISOString();

        const result = await api.post<{ id: string }>("/api/portal/emergencies", {
          body: {
            title: formData.title.trim(),
            description: formData.description.trim(),
            animal_id: formData.animal_id || null,
            photos: formData.photos,
            amount_needed_cents: amountCents,
            currency: formData.currency,
            deadline: deadlineISO,
          },
        });

        router.push(`/emergencies/${result.id}?created=true`);
      } catch (err) {
        if (err instanceof ApiClientError) {
          setErrors({ general: err.detail || "Error al crear la emergencia" });
        } else {
          setErrors({ general: "Error de conexion. Intente nuevamente." });
        }
        setIsSubmitting(false);
      }
    },
    [formData, router]
  );

  const handleDiscard = useCallback(() => {
    router.push("/portal/dashboard");
  }, [router]);

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <AlertTriangle className="h-6 w-6 text-red-600" />
          Publicar Emergencia
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Complete los datos para solicitar ayuda urgente para un animal en
          peligro.
        </p>
      </div>

      {errors.general && (
        <div
          className="mb-4 rounded-md border border-red-200 bg-red-50 p-4 text-sm text-red-700"
          role="alert"
        >
          {errors.general}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Title */}
        <div>
          <label
            htmlFor="emergency-title"
            className="block text-sm font-medium text-gray-700"
          >
            Titulo *
          </label>
          <input
            id="emergency-title"
            type="text"
            value={formData.title}
            onChange={(e) => updateField("title", e.target.value)}
            placeholder="Ej: Perro atropellado necesita cirugia"
            maxLength={MAX_TITLE_LENGTH}
            className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.title ? "border-red-300" : "border-gray-300"
            }`}
            aria-describedby={errors.title ? "title-error" : undefined}
            aria-invalid={!!errors.title}
          />
          <div className="mt-1 flex justify-between">
            {errors.title && (
              <p id="title-error" className="text-xs text-red-600">
                {errors.title}
              </p>
            )}
            <span className="ml-auto text-xs text-gray-400">
              {formData.title.length}/{MAX_TITLE_LENGTH}
            </span>
          </div>
        </div>

        {/* Description */}
        <div>
          <label
            htmlFor="emergency-description"
            className="block text-sm font-medium text-gray-700"
          >
            Descripcion *
          </label>
          <textarea
            id="emergency-description"
            value={formData.description}
            onChange={(e) => updateField("description", e.target.value)}
            placeholder="Describa la situacion del animal y la ayuda que necesita..."
            rows={4}
            maxLength={MAX_DESCRIPTION_LENGTH}
            className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.description ? "border-red-300" : "border-gray-300"
            }`}
            aria-describedby={errors.description ? "description-error" : undefined}
            aria-invalid={!!errors.description}
          />
          <div className="mt-1 flex justify-between">
            {errors.description && (
              <p id="description-error" className="text-xs text-red-600">
                {errors.description}
              </p>
            )}
            <span className="ml-auto text-xs text-gray-400">
              {formData.description.length}/{MAX_DESCRIPTION_LENGTH}
            </span>
          </div>
        </div>

        {/* Photos */}
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Fotos (recomendado 1-3)
          </label>
          <div className="mt-2 flex flex-wrap gap-3">
            {formData.photos.map((photo, idx) => (
              <div
                key={idx}
                className="relative h-20 w-20 rounded-md border border-gray-200 bg-gray-100"
              >
                <span className="flex h-full items-center justify-center text-xs text-gray-500">
                  <Camera className="h-6 w-6" />
                </span>
                <button
                  type="button"
                  onClick={() => removePhoto(idx)}
                  className="absolute -right-2 -top-2 rounded-full bg-red-500 p-0.5 text-white hover:bg-red-600"
                  aria-label={`Eliminar foto ${idx + 1}`}
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
            {formData.photos.length < MAX_PHOTOS && (
              <label
                className="flex h-20 w-20 cursor-pointer items-center justify-center rounded-md border-2 border-dashed border-gray-300 hover:border-green-400 hover:bg-green-50"
                aria-label="Agregar foto"
              >
                <Camera className="h-6 w-6 text-gray-400" />
                <input
                  type="file"
                  accept="image/*"
                  multiple
                  className="hidden"
                  onChange={handlePhotoUpload}
                />
              </label>
            )}
          </div>
          {errors.photos && (
            <p className="mt-1 text-xs text-red-600">{errors.photos}</p>
          )}
        </div>

        {/* Amount and Currency */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label
              htmlFor="emergency-amount"
              className="block text-sm font-medium text-gray-700"
            >
              Monto necesario *
            </label>
            <input
              id="emergency-amount"
              type="number"
              min="0.01"
              step="0.01"
              value={formData.amount}
              onChange={(e) => updateField("amount", e.target.value)}
              placeholder="0.00"
              className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
                errors.amount ? "border-red-300" : "border-gray-300"
              }`}
              aria-describedby={errors.amount ? "amount-error" : undefined}
              aria-invalid={!!errors.amount}
            />
            {errors.amount && (
              <p id="amount-error" className="mt-1 text-xs text-red-600">
                {errors.amount}
              </p>
            )}
          </div>
          <div>
            <label
              htmlFor="emergency-currency"
              className="block text-sm font-medium text-gray-700"
            >
              Moneda
            </label>
            <select
              id="emergency-currency"
              value={formData.currency}
              onChange={(e) => updateField("currency", e.target.value as Currency)}
              className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            >
              {SUPPORTED_CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Deadline */}
        <div>
          <label
            htmlFor="emergency-deadline"
            className="block text-sm font-medium text-gray-700"
          >
            Fecha limite *
          </label>
          <input
            id="emergency-deadline"
            type="datetime-local"
            value={formData.deadline}
            onChange={(e) => updateField("deadline", e.target.value)}
            className={`mt-1 block w-full rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-green-500 ${
              errors.deadline ? "border-red-300" : "border-gray-300"
            }`}
            aria-describedby={errors.deadline ? "deadline-error" : undefined}
            aria-invalid={!!errors.deadline}
          />
          {errors.deadline && (
            <p id="deadline-error" className="mt-1 text-xs text-red-600">
              {errors.deadline}
            </p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Minimo 24 horas, maximo 30 dias desde ahora
          </p>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-between border-t border-gray-200 pt-6">
          <button
            type="button"
            onClick={() => setShowDiscard(true)}
            className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-gray-400"
          >
            Descartar
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="inline-flex items-center gap-2 rounded-md bg-red-600 px-6 py-2 text-sm font-semibold text-white shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 disabled:opacity-50"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "Publicando..." : "Publicar Emergencia"}
          </button>
        </div>
      </form>

      {/* Discard confirmation */}
      {showDiscard && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="mx-4 w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
            <h3 className="text-lg font-semibold text-gray-900">
              Descartar emergencia?
            </h3>
            <p className="mt-2 text-sm text-gray-600">
              Los datos del formulario se perderan.
            </p>
            <div className="mt-4 flex justify-end gap-3">
              <button
                onClick={() => setShowDiscard(false)}
                className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancelar
              </button>
              <button
                onClick={handleDiscard}
                className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
              >
                Si, descartar
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
