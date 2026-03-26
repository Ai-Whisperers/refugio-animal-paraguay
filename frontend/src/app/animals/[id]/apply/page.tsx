"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import type { Animal } from "@/types/api";
import { getAnimalPublic, submitAdoptionApplication } from "@/lib/public-api";
import { ApiClientError } from "@/lib/api";
import { speciesEmoji } from "@/lib/animal-utils";
import { ADOPTION_FORM, ANIMAL_DETAIL, COMMON } from "@/lib/strings";

/** Validation errors per field. */
interface FormErrors {
  full_name?: string;
  email?: string;
  phone?: string;
  message?: string;
  gdpr_consent?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MAX_MESSAGE_LENGTH = 2000;

export default function AdoptionApplicationPage() {
  const params = useParams<{ id: string }>();
  // Animal data
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoadingAnimal, setIsLoadingAnimal] = useState(true);
  const [animalError, setAnimalError] = useState<string | null>(null);

  // Form state
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [message, setMessage] = useState("");
  const [gdprConsent, setGdprConsent] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  // Fetch animal data
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
        setAnimalError(
          err instanceof Error ? err.message : COMMON.error
        );
      } finally {
        setIsLoadingAnimal(false);
      }
    }

    fetchAnimal();
  }, [params.id]);

  function validateForm(): boolean {
    const newErrors: FormErrors = {};

    if (!fullName.trim()) {
      newErrors.full_name = ADOPTION_FORM.nameRequired;
    } else if (fullName.trim().length > 255) {
      newErrors.full_name = ADOPTION_FORM.nameTooLong;
    }

    if (!email.trim()) {
      newErrors.email = ADOPTION_FORM.emailRequired;
    } else if (!EMAIL_REGEX.test(email.trim())) {
      newErrors.email = ADOPTION_FORM.emailInvalid;
    }

    if (phone && phone.length > 50) {
      newErrors.phone = ADOPTION_FORM.phoneTooLong;
    }

    if (message && message.length > MAX_MESSAGE_LENGTH) {
      newErrors.message = ADOPTION_FORM.messageTooLong(MAX_MESSAGE_LENGTH);
    }

    if (!gdprConsent) {
      newErrors.gdpr_consent = ADOPTION_FORM.gdprRequired;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!validateForm() || !animal) return;

    setIsSubmitting(true);
    try {
      await submitAdoptionApplication({
        animal_id: animal.id,
        full_name: fullName.trim(),
        email: email.trim(),
        phone: phone.trim() || undefined,
        message: message.trim() || undefined,
        gdpr_consent: true,
      });
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

  // --- Loading state ---
  if (isLoadingAnimal) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-r-transparent" />
        <p className="mt-3 text-gray-500">{COMMON.loading}</p>
      </div>
    );
  }

  // --- Error loading animal ---
  if (animalError || !animal) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-5xl mb-4">{COMMON.paw}</p>
        <p className="text-red-600 mb-4">{animalError ?? ANIMAL_DETAIL.notFound}</p>
        <Link
          href="/animals"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          {ANIMAL_DETAIL.backToAnimals}
        </Link>
      </div>
    );
  }

  // --- Success state ---
  if (isSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-xl p-8 border border-green-200">
          <p className="text-5xl mb-4">{"\u{1F389}"}</p>
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-3">
            {ADOPTION_FORM.successTitle}
          </h1>
          <p className="text-gray-600 mb-6">
            {ADOPTION_FORM.successMessage(animal.name, email)}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link
              href={`/animals/${animal.id}`}
              className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
            >
              {ADOPTION_FORM.backTo(animal.name)}
            </Link>
            <Link
              href="/animals"
              className="px-6 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              {ADOPTION_FORM.browseMore}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // --- Application form ---
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/animals" className="hover:text-primary-600">
          {ANIMAL_DETAIL.breadcrumbAnimals}
        </Link>
        <span className="mx-2">/</span>
        <Link
          href={`/animals/${animal.id}`}
          className="hover:text-primary-600"
        >
          {animal.name}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Apply</span>
      </nav>

      {/* Animal Summary Card */}
      <div className="flex items-center gap-4 bg-white rounded-lg border border-gray-100 p-4 mb-8 shadow-sm">
        {animal.primary_photo_url ? (
          <Image
            src={animal.primary_photo_url}
            alt={animal.name}
            width={64}
            height={64}
            className="w-16 h-16 rounded-lg object-cover"
            unoptimized
          />
        ) : (
          <div className="w-16 h-16 rounded-lg bg-gray-100 flex items-center justify-center text-2xl">
            {speciesEmoji(animal.species)}
          </div>
        )}
        <div>
          <h2 className="font-semibold text-gray-900">{animal.name}</h2>
          <p className="text-sm text-gray-500 capitalize">{animal.species}</p>
        </div>
      </div>

      {/* Form Header */}
      <h1 className="text-2xl md:text-3xl font-heading font-bold text-gray-900 mb-2">
        {ADOPTION_FORM.title}
      </h1>
      <p className="text-gray-500 mb-8">
        {ADOPTION_FORM.subtitle(animal.name)}
      </p>

      {/* Submission Error */}
      {submitError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {submitError}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {/* Full Name */}
        <div>
          <label
            htmlFor="full_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {ADOPTION_FORM.fullName} <span className="text-red-500">{ADOPTION_FORM.required}</span>
          </label>
          <input
            id="full_name"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.full_name ? "border-red-300" : "border-gray-300"
            }`}
            placeholder={ADOPTION_FORM.fullNamePlaceholder}
            maxLength={255}
          />
          {errors.full_name && (
            <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {ADOPTION_FORM.email} <span className="text-red-500">{ADOPTION_FORM.required}</span>
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.email ? "border-red-300" : "border-gray-300"
            }`}
            placeholder={ADOPTION_FORM.emailPlaceholder}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email}</p>
          )}
        </div>

        {/* Phone (optional) */}
        <div>
          <label
            htmlFor="phone"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {ADOPTION_FORM.phone}{" "}
            <span className="text-gray-400 font-normal">{ADOPTION_FORM.phoneOptional}</span>
          </label>
          <input
            id="phone"
            type="tel"
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.phone ? "border-red-300" : "border-gray-300"
            }`}
            placeholder={ADOPTION_FORM.phonePlaceholder}
            maxLength={50}
          />
          {errors.phone && (
            <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
          )}
        </div>

        {/* Message (optional) */}
        <div>
          <label
            htmlFor="message"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {ADOPTION_FORM.message}{" "}
            <span className="text-gray-400 font-normal">{ADOPTION_FORM.messageOptional}</span>
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={4}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors resize-y ${
              errors.message ? "border-red-300" : "border-gray-300"
            }`}
            placeholder={ADOPTION_FORM.messagePlaceholder}
            maxLength={MAX_MESSAGE_LENGTH}
          />
          <div className="flex justify-between mt-1">
            {errors.message ? (
              <p className="text-sm text-red-600">{errors.message}</p>
            ) : (
              <span />
            )}
            <p className="text-xs text-gray-400">
              {message.length}/{MAX_MESSAGE_LENGTH}
            </p>
          </div>
        </div>

        {/* GDPR Consent */}
        <div
          className={`p-4 rounded-lg border ${
            errors.gdpr_consent
              ? "bg-red-50 border-red-200"
              : "bg-gray-50 border-gray-200"
          }`}
        >
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={gdprConsent}
              onChange={(e) => setGdprConsent(e.target.checked)}
              className="mt-1 h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
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
          {errors.gdpr_consent && (
            <p className="mt-2 text-sm text-red-600">{errors.gdpr_consent}</p>
          )}
        </div>

        {/* Submit */}
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? ADOPTION_FORM.submitting : ADOPTION_FORM.submit}
          </button>
          <Link
            href={`/animals/${animal.id}`}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-center"
          >
            {ADOPTION_FORM.cancel}
          </Link>
        </div>
      </form>
    </div>
  );
}
