"use client";

import { useState } from "react";
import { api, ApiClientError } from "@/lib/api";
import { CONTACT, COMMON } from "@/lib/strings";

const SUBJECT_MIN_LENGTH = 10;
const MESSAGE_MIN_LENGTH = 20;
const MESSAGE_MAX_LENGTH = 5000;

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
      newErrors.visitor_name = "Name must be at least 3 characters.";
    } else if (visitorName.trim().length > 100) {
      newErrors.visitor_name = "Name must be 100 characters or fewer.";
    }

    if (!visitorEmail.trim()) {
      newErrors.visitor_email = "Email address is required.";
    } else if (!EMAIL_REGEX.test(visitorEmail.trim())) {
      newErrors.visitor_email = "Please enter a valid email address.";
    }

    if (!subject.trim() || subject.trim().length < SUBJECT_MIN_LENGTH) {
      newErrors.subject = `Subject must be at least ${SUBJECT_MIN_LENGTH} characters.`;
    } else if (subject.trim().length > 200) {
      newErrors.subject = "Subject must be 200 characters or fewer.";
    }

    if (!message.trim() || message.trim().length < MESSAGE_MIN_LENGTH) {
      newErrors.message = `Message must be at least ${MESSAGE_MIN_LENGTH} characters.`;
    } else if (message.trim().length > MESSAGE_MAX_LENGTH) {
      newErrors.message = `Message must be ${MESSAGE_MAX_LENGTH} characters or fewer.`;
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

  // --- Success state ---
  if (isSuccess) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-xl p-8 border border-green-200">
          <p className="text-5xl mb-4">{"\u{1F4EC}"}</p>
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-3">
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
            className="px-6 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition-colors"
          >
            {CONTACT.sendAnother}
          </button>
        </div>
      </div>
    );
  }

  // --- Form ---
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="text-center mb-10">
        <h1 className="text-3xl md:text-4xl font-heading font-bold text-gray-900 mb-3">
          {CONTACT.title}
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">
          {CONTACT.subtitle}
        </p>
      </div>

      {/* Contact Info Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-10">
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-2xl mb-1">{"\u{1F4CD}"}</p>
          <p className="text-sm font-medium text-gray-900">Location</p>
          <p className="text-xs text-gray-500">Asuncion, Paraguay</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-2xl mb-1">{"\u{1F4E7}"}</p>
          <p className="text-sm font-medium text-gray-900">Email</p>
          <p className="text-xs text-gray-500">info@refugioanimal.py</p>
        </div>
        <div className="bg-gray-50 rounded-lg p-4 text-center">
          <p className="text-2xl mb-1">{"\u{1F4F1}"}</p>
          <p className="text-sm font-medium text-gray-900">WhatsApp</p>
          <p className="text-xs text-gray-500">+595 981 000 000</p>
        </div>
      </div>

      {/* Submission Error */}
      {submitError && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {submitError}
        </div>
      )}

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 sm:p-8 space-y-6"
        noValidate
      >
        {/* Name */}
        <div>
          <label
            htmlFor="visitor_name"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {CONTACT.fullName} <span className="text-red-500">*</span>
          </label>
          <input
            id="visitor_name"
            type="text"
            value={visitorName}
            onChange={(e) => setVisitorName(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.visitor_name ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Maria Garcia"
            maxLength={100}
          />
          {errors.visitor_name && (
            <p className="mt-1 text-sm text-red-600">{errors.visitor_name}</p>
          )}
        </div>

        {/* Email */}
        <div>
          <label
            htmlFor="visitor_email"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {CONTACT.email} <span className="text-red-500">*</span>
          </label>
          <input
            id="visitor_email"
            type="email"
            value={visitorEmail}
            onChange={(e) => setVisitorEmail(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.visitor_email ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="maria@example.com"
          />
          {errors.visitor_email && (
            <p className="mt-1 text-sm text-red-600">{errors.visitor_email}</p>
          )}
        </div>

        {/* Subject */}
        <div>
          <label
            htmlFor="subject"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {CONTACT.subject} <span className="text-red-500">*</span>
          </label>
          <input
            id="subject"
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors ${
              errors.subject ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Question about adoption requirements"
            maxLength={200}
          />
          {errors.subject && (
            <p className="mt-1 text-sm text-red-600">{errors.subject}</p>
          )}
        </div>

        {/* Message */}
        <div>
          <label
            htmlFor="message"
            className="block text-sm font-medium text-gray-700 mb-1"
          >
            {CONTACT.message} <span className="text-red-500">*</span>
          </label>
          <textarea
            id="message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={5}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 outline-none transition-colors resize-y ${
              errors.message ? "border-red-300" : "border-gray-300"
            }`}
            placeholder="Tell us how we can help..."
            maxLength={MESSAGE_MAX_LENGTH}
          />
          <div className="flex justify-between mt-1">
            {errors.message ? (
              <p className="text-sm text-red-600">{errors.message}</p>
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
          className="w-full bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isSubmitting ? CONTACT.submitting : CONTACT.submit}
        </button>
      </form>
    </div>
  );
}
