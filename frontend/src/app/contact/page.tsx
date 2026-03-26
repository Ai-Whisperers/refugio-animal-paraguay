"use client";

import { useState } from "react";
import { MessageCircle, Mail, MapPin, Clock, CheckCircle } from "lucide-react";
import { api, ApiClientError } from "@/lib/api";
import { CONTACT, COMMON } from "@/lib/strings";

const SUBJECT_MIN_LENGTH = 10;
const MESSAGE_MIN_LENGTH = 20;
const MESSAGE_MAX_LENGTH = 5000;
const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "595981000000";
const WHATSAPP_URL = `https://wa.me/${WHATSAPP_NUMBER.replace(/\s/g, "")}`;

interface FormErrors {
  visitor_name?: string;
  visitor_email?: string;
  subject?: string;
  message?: string;
}

const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

interface ContactResponse {
  id: string;
  form_type: string;
  submitted_at: string;
  message: string;
}

export default function ContactPage() {
  const [visitorName, setVisitorName] = useState("");
  const [visitorEmail, setVisitorEmail] = useState("");
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [isSuccess, setIsSuccess] = useState(false);

  function validateForm(): boolean {
    const newErrors: FormErrors = {};

    if (!visitorName.trim() || visitorName.trim().length < 3) {
      newErrors.visitor_name = "El nombre debe tener al menos 3 caracteres.";
    } else if (visitorName.trim().length > 100) {
      newErrors.visitor_name = "El nombre debe tener 100 caracteres o menos.";
    }

    if (!visitorEmail.trim()) {
      newErrors.visitor_email = "El correo electronico es obligatorio.";
    } else if (!EMAIL_REGEX.test(visitorEmail.trim())) {
      newErrors.visitor_email = "Por favor ingresa un correo electronico valido.";
    }

    if (!subject.trim() || subject.trim().length < SUBJECT_MIN_LENGTH) {
      newErrors.subject = `El asunto debe tener al menos ${SUBJECT_MIN_LENGTH} caracteres.`;
    } else if (subject.trim().length > 200) {
      newErrors.subject = "El asunto debe tener 200 caracteres o menos.";
    }

    if (!message.trim() || message.trim().length < MESSAGE_MIN_LENGTH) {
      newErrors.message = `El mensaje debe tener al menos ${MESSAGE_MIN_LENGTH} caracteres.`;
    } else if (message.trim().length > MESSAGE_MAX_LENGTH) {
      newErrors.message = `El mensaje debe tener ${MESSAGE_MAX_LENGTH} caracteres o menos.`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await api.post<ContactResponse>(
        "/public/contact",
        {
          visitor_name: visitorName.trim(),
          visitor_email: visitorEmail.trim(),
          subject: subject.trim(),
          message: message.trim(),
        },
        { requiresAuth: false }
      );
      setIsSuccess(true);
    } catch (err) {
      if (err instanceof ApiClientError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError(COMMON.error);
      }
    } finally {
      setIsSubmitting(false);
    }
  }

  if (isSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-xl p-8 border border-green-200">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">
            {CONTACT.successTitle}
          </h1>
          <p className="text-gray-600 mb-6">
            {CONTACT.successMessage}
          </p>
          <button
            onClick={() => {
              setIsSuccess(false);
              setVisitorName("");
              setVisitorEmail("");
              setSubject("");
              setMessage("");
            }}
            className="px-6 py-2 bg-[#E8622A] text-white rounded-lg font-medium hover:bg-[#d4571f] transition-colors"
          >
            {CONTACT.sendAnother}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-3">
          {CONTACT.title}
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">
          {CONTACT.subtitle}
        </p>
      </div>

      {/* WhatsApp Primary CTA */}
      <div className="bg-[#25D366]/10 border border-[#25D366]/30 rounded-xl p-6 mb-8 text-center">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-[#25D366] text-white mb-4">
          <MessageCircle className="h-7 w-7" />
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {CONTACT.whatsappTitle}
        </h2>
        <p className="text-gray-600 mb-4">
          {CONTACT.whatsappSubtitle}
        </p>
        <a
          href={`${WHATSAPP_URL}?text=${encodeURIComponent("Hola! Tengo una consulta sobre el refugio.")}`}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center justify-center gap-2 bg-[#25D366] text-white px-8 py-3 rounded-lg font-semibold hover:bg-[#1fb855] transition-colors text-lg"
        >
          <MessageCircle className="h-5 w-5" />
          {CONTACT.whatsappCta}
        </a>
        <p className="text-sm text-gray-500 mt-3">
          {CONTACT.whatsappNumber}
        </p>
      </div>

      {/* Contact Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <MapPin className="h-6 w-6 text-[#E8622A] mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-900">{CONTACT.locationLabel}</p>
          <p className="text-xs text-gray-500">Asuncion, Paraguay</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <Clock className="h-6 w-6 text-[#E8622A] mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-900">{CONTACT.hoursLabel}</p>
          <p className="text-xs text-gray-500">Lunes a Sabado: 8:00 - 17:00</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <Mail className="h-6 w-6 text-[#E8622A] mx-auto mb-2" />
          <p className="text-sm font-medium text-gray-900">{CONTACT.emailLabel}</p>
          <p className="text-xs text-gray-500">contacto@refugio.org.py</p>
        </div>
      </div>

      {/* Email Form (secondary) */}
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-gray-900 mb-1">
          {CONTACT.emailFormTitle}
        </h2>
        <p className="text-sm text-gray-500">{CONTACT.emailFormSubtitle}</p>
      </div>

      {submitError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm" role="alert">
          {submitError}
        </div>
      )}

      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 sm:p-8 space-y-6"
        noValidate
      >
        {/* Name */}
        <div>
          <label htmlFor="visitor_name" className="block text-sm font-medium text-gray-700 mb-1">
            {CONTACT.fullName} <span className="text-red-500">*</span>
          </label>
          <input
            id="visitor_name"
            type="text"
            value={visitorName}
            onChange={(e) => setVisitorName(e.target.value)}
            className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
              errors.visitor_name ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Maria Garcia"
            maxLength={100}
            aria-invalid={!!errors.visitor_name}
            aria-describedby={errors.visitor_name ? "name-error" : undefined}
          />
          {errors.visitor_name && (
            <p id="name-error" className="mt-1 text-sm text-red-600" role="alert">{errors.visitor_name}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="visitor_email" className="block text-sm font-medium text-gray-700 mb-1">
            {CONTACT.email} <span className="text-red-500">*</span>
          </label>
          <input
            id="visitor_email"
            type="email"
            inputMode="email"
            value={visitorEmail}
            onChange={(e) => setVisitorEmail(e.target.value)}
            className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
              errors.visitor_email ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="maria@ejemplo.com"
            aria-invalid={!!errors.visitor_email}
            aria-describedby={errors.visitor_email ? "email-error" : undefined}
          />
          {errors.visitor_email && (
            <p id="email-error" className="mt-1 text-sm text-red-600" role="alert">{errors.visitor_email}</p>
          )}
        </div>

        {/* Subject */}
        <div>
          <label htmlFor="subject" className="block text-sm font-medium text-gray-700 mb-1">
            {CONTACT.subject} <span className="text-red-500">*</span>
          </label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
              errors.subject ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Consulta sobre requisitos de adopcion"
            maxLength={200}
            aria-invalid={!!errors.subject}
            aria-describedby={errors.subject ? "subject-error" : undefined}
          />
          {errors.subject && (
            <p id="subject-error" className="mt-1 text-sm text-red-600" role="alert">{errors.subject}</p>
          )}
        </div>

        {/* Message */}
        <div>
          <label htmlFor="message" className="block text-sm font-medium text-gray-700 mb-1">
            {CONTACT.message} <span className="text-red-500">*</span>
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
            className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors resize-y ${
              errors.message ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Contanos como te podemos ayudar..."
            maxLength={MESSAGE_MAX_LENGTH}
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
              {message.length}/{MESSAGE_MAX_LENGTH}
            </p>
          </div>
        </div>

        {/* Submit */}
        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? CONTACT.submitting : CONTACT.submit}
        </button>
      </form>
    </div>
  );
}
