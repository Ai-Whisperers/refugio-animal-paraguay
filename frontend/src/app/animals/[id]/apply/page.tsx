"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { CheckCircle, MessageCircle } from "lucide-react";
import type { Animal } from "@/types/api";
import { getAnimalPublic, submitAdoptionApplication } from "@/lib/public-api";
import { ApiClientError } from "@/lib/api";
import { ADOPTION_FORM, ANIMAL_DETAIL, COMMON, SPECIES_LABELS } from "@/lib/strings";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";

// --- Constants ---
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_MESSAGE_LENGTH = 2000;
const TOTAL_STEPS = 3;
const WHATSAPP_BASE = "https://wa.me/595981000000";
const STORAGE_KEY_PREFIX = "refugio_adoption_";

// --- Types ---
interface FormData {
  fullName: string;
  email: string;
  phone: string;
  message: string;
  livingSituation: string;
  gdprConsent: boolean;
}

interface FormErrors {
  fullName?: string;
  email?: string;
  phone?: string;
  message?: string;
  gdprConsent?: string;
}

const INITIAL_FORM: FormData = {
  fullName: "",
  email: "",
  phone: "",
  message: "",
  livingSituation: "",
  gdprConsent: false,
};

// --- localStorage helpers ---
function loadFormData(animalId: string): FormData {
  if (typeof window === "undefined") return INITIAL_FORM;
  try {
    const stored = localStorage.getItem(`${STORAGE_KEY_PREFIX}${animalId}`);
    if (stored) {
      const parsed = JSON.parse(stored) as Partial<FormData>;
      return { ...INITIAL_FORM, ...parsed };
    }
  } catch {
    // corrupted data, start fresh
  }
  return INITIAL_FORM;
}

function saveFormData(animalId: string, data: FormData): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(`${STORAGE_KEY_PREFIX}${animalId}`, JSON.stringify(data));
  } catch {
    // storage full, fail silently
  }
}

function clearFormData(animalId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${animalId}`);
  } catch {
    // fail silently
  }
}

export default function AdoptionApplicationPage() {
  const params = useParams<{ id: string }>();

  // Animal data
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoadingAnimal, setIsLoadingAnimal] = useState(true);
  const [animalError, setAnimalError] = useState<string | null>(null);

  // Form state
  const [step, setStep] = useState(1);
  const [form, setForm] = useState<FormData>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  // Load saved form data on mount
  useEffect(() => {
    if (params.id) {
      setForm(loadFormData(params.id));
    }
  }, [params.id]);

  // Auto-save form data on changes
  useEffect(() => {
    if (params.id && !isSuccess) {
      saveFormData(params.id, form);
    }
  }, [form, params.id, isSuccess]);

  // Fetch animal
  useEffect(() => {
    if (!params.id) return;

    async function fetchAnimal() {
      setIsLoadingAnimal(true);
      setAnimalError(null);
      try {
        const data = await getAnimalPublic(params.id);
        if (data.status !== "available") {
          setAnimalError(ADOPTION_FORM.animalNotAvailable);
        }
        setAnimal(data);
      } catch (err) {
        setAnimalError(err instanceof Error ? err.message : COMMON.error);
      } finally {
        setIsLoadingAnimal(false);
      }
    }

    fetchAnimal();
  }, [params.id]);

  const updateField = useCallback(
    <K extends keyof FormData>(field: K, value: FormData[K]) => {
      setForm((prev) => ({ ...prev, [field]: value }));
      // Clear field error on change
      if (field in errors) {
        setErrors((prev) => {
          const next = { ...prev };
          delete next[field as keyof FormErrors];
          return next;
        });
      }
    },
    [errors]
  );

  function validateStep(s: number): boolean {
    const newErrors: FormErrors = {};

    if (s === 1) {
      if (!form.fullName.trim()) {
        newErrors.fullName = ADOPTION_FORM.nameRequired;
      } else if (form.fullName.trim().length > 255) {
        newErrors.fullName = ADOPTION_FORM.nameTooLong;
      }
      if (!form.email.trim()) {
        newErrors.email = ADOPTION_FORM.emailRequired;
      } else if (!EMAIL_REGEX.test(form.email.trim())) {
        newErrors.email = ADOPTION_FORM.emailInvalid;
      }
      if (form.phone && form.phone.length > 50) {
        newErrors.phone = ADOPTION_FORM.phoneTooLong;
      }
    }

    if (s === 2) {
      if (form.message && form.message.length > MAX_MESSAGE_LENGTH) {
        newErrors.message = ADOPTION_FORM.messageTooLong(MAX_MESSAGE_LENGTH);
      }
    }

    if (s === 3) {
      if (!form.gdprConsent) {
        newErrors.gdprConsent = ADOPTION_FORM.gdprRequired;
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  function goNext() {
    if (validateStep(step) && step < TOTAL_STEPS) {
      setStep(step + 1);
    }
  }

  function goPrev() {
    if (step > 1) {
      setStep(step - 1);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!validateStep(3) || !animal) return;

    setIsSubmitting(true);
    try {
      await submitAdoptionApplication({
        animal_id: animal.id,
        full_name: form.fullName.trim(),
        email: form.email.trim(),
        phone: form.phone.trim() || undefined,
        message: [form.message.trim(), form.livingSituation.trim()].filter(Boolean).join("\n\n---\n\n") || undefined,
        gdpr_consent: true,
      });
      clearFormData(params.id);
      setIsSuccess(true);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError(ADOPTION_FORM.submitError);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  // --- Loading ---
  if (isLoadingAnimal) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#E8622A] border-r-transparent" />
        <p className="mt-3 text-gray-500">{COMMON.loading}</p>
      </div>
    );
  }

  // --- Animal error ---
  if (animalError || !animal) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 mb-4">{animalError ?? ANIMAL_DETAIL.notFound}</p>
        <Link href="/animals" className="text-[#E8622A] hover:underline font-medium">
          {ANIMAL_DETAIL.backToAnimals}
        </Link>
      </div>
    );
  }

  // --- Success ---
  if (isSuccess) {
    const whatsappMessage = encodeURIComponent(`Hola! Acabo de enviar una solicitud de adopcion para ${animal.name}.`);
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-xl p-8 border border-green-200">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">
            {ADOPTION_FORM.successTitle}
          </h1>
          <p className="text-gray-600 mb-6">
            {ADOPTION_FORM.successMessage(animal.name, form.email)}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href={`${WHATSAPP_BASE}?text=${whatsappMessage}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center gap-2 bg-[#25D366] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#1fb855] transition-colors"
            >
              <MessageCircle className="h-5 w-5" />
              {ADOPTION_FORM.whatsappConfirm}
            </a>
            <Link
              href={`/animals/${animal.id}`}
              className="px-6 py-2.5 bg-[#E8622A] text-white rounded-lg font-medium hover:bg-[#d4571f] transition-colors"
            >
              {ADOPTION_FORM.backTo(animal.name)}
            </Link>
            <Link
              href="/animals"
              className="px-6 py-2.5 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              {ADOPTION_FORM.browseMore}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // --- Multi-step Form ---
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/animals" className="hover:text-[#E8622A] transition-colors">
          {ANIMAL_DETAIL.breadcrumbAnimals}
        </Link>
        <span className="mx-2">/</span>
        <Link href={`/animals/${animal.id}`} className="hover:text-[#E8622A] transition-colors">
          {animal.name}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{ADOPTION_FORM.breadcrumbApply}</span>
      </nav>

      {/* Animal Summary */}
      <div className="flex items-center gap-4 bg-white rounded-lg border border-gray-100 p-4 mb-6 shadow-sm">
        {animal.primary_photo_url ? (
          <Image
            src={animal.primary_photo_url}
            alt={animal.name}
            width={64}
            height={64}
            className="w-16 h-16 rounded-lg object-cover"
            sizes="64px"
          />
        ) : (
          <AnimalPlaceholder
            species={animal.species}
            className="w-16 h-16 rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center"
          />
        )}
        <div>
          <h2 className="font-semibold text-gray-900">{animal.name}</h2>
          <p className="text-sm text-gray-500">{SPECIES_LABELS[animal.species] ?? animal.species}</p>
        </div>
      </div>

      {/* Form Header */}
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
        {ADOPTION_FORM.title}
      </h1>
      <p className="text-gray-500 mb-6">
        {ADOPTION_FORM.subtitle(animal.name)}
      </p>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            {ADOPTION_FORM.stepOf(step, TOTAL_STEPS)}
          </span>
          <span className="text-sm text-gray-400">
            {step === 1 ? ADOPTION_FORM.stepPersonal : step === 2 ? ADOPTION_FORM.stepHome : ADOPTION_FORM.stepConsent}
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#E8622A] rounded-full transition-all duration-300"
            style={{ width: `${(step / TOTAL_STEPS) * 100}%` }}
          />
        </div>
      </div>

      {/* Submission Error */}
      {submitError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
          {submitError}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* Step 1: Personal Info */}
        {step === 1 && (
          <fieldset disabled={isSubmitting}>
            <div className="space-y-5">
              {/* Full Name */}
              <div>
                <label htmlFor="fullName" className="block text-sm font-medium text-gray-700 mb-1">
                  {ADOPTION_FORM.fullName} <span className="text-red-500">{ADOPTION_FORM.required}</span>
                </label>
                <input
                  id="fullName"
                  type="text"
                  value={form.fullName}
                  onChange={(e) => updateField("fullName", e.target.value)}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
                    errors.fullName ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder={ADOPTION_FORM.fullNamePlaceholder}
                  maxLength={255}
                  aria-invalid={!!errors.fullName}
                  aria-describedby={errors.fullName ? "fullName-error" : undefined}
                />
                {errors.fullName && (
                  <p id="fullName-error" className="mt-1 text-sm text-red-600" role="alert">{errors.fullName}</p>
                )}
              </div>

              {/* Email */}
              <div>
                <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                  {ADOPTION_FORM.email} <span className="text-red-500">{ADOPTION_FORM.required}</span>
                </label>
                <input
                  id="email"
                  type="email"
                  inputMode="email"
                  value={form.email}
                  onChange={(e) => updateField("email", e.target.value)}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
                    errors.email ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder={ADOPTION_FORM.emailPlaceholder}
                  aria-invalid={!!errors.email}
                  aria-describedby={errors.email ? "email-error" : undefined}
                />
                {errors.email && (
                  <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">{errors.email}</p>
                )}
              </div>

              {/* Phone */}
              <div>
                <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                  {ADOPTION_FORM.phone}{" "}
                  <span className="text-gray-400 font-normal">{ADOPTION_FORM.phoneOptional}</span>
                </label>
                <input
                  id="phone"
                  type="tel"
                  inputMode="tel"
                  value={form.phone}
                  onChange={(e) => updateField("phone", e.target.value)}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
                    errors.phone ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder={ADOPTION_FORM.phonePlaceholder}
                  maxLength={50}
                  aria-invalid={!!errors.phone}
                  aria-describedby={errors.phone ? "phone-error" : undefined}
                />
                {errors.phone && (
                  <p id="phone-error" className="mt-1 text-sm text-red-600" role="alert">{errors.phone}</p>
                )}
              </div>
            </div>
          </fieldset>
        )}

        {/* Step 2: About Your Home */}
        {step === 2 && (
          <fieldset disabled={isSubmitting}>
            <div className="space-y-5">
              <div>
                <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
                  {ADOPTION_FORM.message}{" "}
                  <span className="text-gray-400 font-normal">{ADOPTION_FORM.messageOptional}</span>
                </label>
                <textarea
                  id="message"
                  value={form.message}
                  onChange={(e) => updateField("message", e.target.value)}
                  rows={4}
                  className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors resize-y ${
                    errors.message ? "border-red-300" : "border-gray-300"
                  }`}
                  placeholder={ADOPTION_FORM.messagePlaceholder}
                  maxLength={MAX_MESSAGE_LENGTH}
                  aria-invalid={!!errors.message}
                  aria-describedby={errors.message ? "message-error" : undefined}
                />
                <div className="flex justify-between mt-1">
                  {errors.message ? (
                    <p id="message-error" className="text-sm text-red-600" role="alert">{errors.message}</p>
                  ) : (
                    <span />
                  )}
                  <p className="text-xs text-gray-400">
                    {form.message.length}/{MAX_MESSAGE_LENGTH}
                  </p>
                </div>
              </div>

              <div>
                <label htmlFor="livingSituation" className="block text-sm font-medium text-gray-700 mb-1">
                  {ADOPTION_FORM.livingSituation}{" "}
                  <span className="text-gray-400 font-normal">{ADOPTION_FORM.phoneOptional}</span>
                </label>
                <textarea
                  id="livingSituation"
                  value={form.livingSituation}
                  onChange={(e) => updateField("livingSituation", e.target.value)}
                  rows={3}
                  className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors resize-y"
                  placeholder={ADOPTION_FORM.livingSituationPlaceholder}
                />
              </div>
            </div>
          </fieldset>
        )}

        {/* Step 3: Consent & Review */}
        {step === 3 && (
          <fieldset disabled={isSubmitting}>
            <div className="space-y-6">
              {/* Review Summary */}
              <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-700 mb-3">{ADOPTION_FORM.reviewTitle}</h3>
                <dl className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <dt className="text-gray-500">{ADOPTION_FORM.fullName}</dt>
                    <dd className="text-gray-900 font-medium">{form.fullName}</dd>
                  </div>
                  <div className="flex justify-between">
                    <dt className="text-gray-500">{ADOPTION_FORM.email}</dt>
                    <dd className="text-gray-900 font-medium">{form.email}</dd>
                  </div>
                  {form.phone && (
                    <div className="flex justify-between">
                      <dt className="text-gray-500">{ADOPTION_FORM.phone}</dt>
                      <dd className="text-gray-900 font-medium">{form.phone}</dd>
                    </div>
                  )}
                </dl>
              </div>

              {/* GDPR Consent */}
              <div
                className={`p-4 rounded-lg border ${
                  errors.gdprConsent ? "bg-red-50 border-red-200" : "bg-gray-50 border-gray-200"
                }`}
              >
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={form.gdprConsent}
                    onChange={(e) => updateField("gdprConsent", e.target.checked)}
                    className="mt-1 h-4 w-4 rounded border-gray-300 text-[#E8622A] focus:ring-[#E8622A]"
                    aria-invalid={!!errors.gdprConsent}
                    aria-describedby={errors.gdprConsent ? "gdpr-error" : undefined}
                  />
                  <div>
                    <p className="text-sm text-gray-700">
                      <span className="font-medium">{ADOPTION_FORM.gdprTitle}</span>{" "}
                      <span className="text-red-500">{ADOPTION_FORM.required}</span>
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {ADOPTION_FORM.gdprText}
                    </p>
                  </div>
                </label>
                {errors.gdprConsent && (
                  <p id="gdpr-error" className="mt-2 text-sm text-red-600" role="alert">{errors.gdprConsent}</p>
                )}
              </div>
            </div>
          </fieldset>
        )}

        {/* Navigation */}
        <div className="flex gap-3 pt-2">
          {step > 1 && (
            <button
              type="button"
              onClick={goPrev}
              disabled={isSubmitting}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {ADOPTION_FORM.prevStep}
            </button>
          )}

          {step < TOTAL_STEPS ? (
            <button
              type="button"
              onClick={goNext}
              className="flex-1 bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
            >
              {ADOPTION_FORM.nextStep}
            </button>
          ) : (
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex-1 bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isSubmitting ? ADOPTION_FORM.submitting : ADOPTION_FORM.submit}
            </button>
          )}

          {step === 1 && (
            <Link
              href={`/animals/${animal.id}`}
              className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-center"
            >
              {ADOPTION_FORM.cancel}
            </Link>
          )}
        </div>
      </form>
    </div>
  );
}
