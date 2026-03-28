"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Share2,
  Printer,
  MessageCircle,
  Mail,
  Copy,
  Check,
  Star,
  ExternalLink,
} from "lucide-react";
import type { Animal, PreQualifyResult } from "@/types/api";
import { getAnimalPublic } from "@/lib/public-api";
import { SPECIES_LABELS, PRE_QUALIFY, PRE_QUALIFY_RESULT } from "@/lib/strings";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";

// --- Constants ---
const RESULT_STORAGE_KEY = "refugio_prequal_result_";
const WHATSAPP_BASE = "https://wa.me/595981000000";
const MIN_MATCH_SCORE = 70;
const MAX_ALTERNATIVES = 10;

// --- Helpers ---

function getResultFromStorage(animalId: string): PreQualifyResult | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(`${RESULT_STORAGE_KEY}${animalId}`);
    if (!raw) return null;
    return JSON.parse(raw) as PreQualifyResult;
  } catch {
    return null;
  }
}

function scoreColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-amber-600";
  return "text-red-600";
}

function scoreBgColor(score: number): string {
  if (score >= 80) return "bg-green-50 border-green-200";
  if (score >= 60) return "bg-amber-50 border-amber-200";
  return "bg-red-50 border-red-200";
}

function scoreRingColor(score: number): string {
  if (score >= 80) return "stroke-green-500";
  if (score >= 60) return "stroke-amber-500";
  return "stroke-red-500";
}

// --- Score Ring Component ---
function ScoreRing({ score }: { score: number }) {
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (score / 100) * circumference;

  return (
    <div className="relative w-36 h-36 mx-auto">
      <svg className="w-full h-full -rotate-90" viewBox="0 0 120 120">
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="8"
          className="text-gray-200"
        />
        <circle
          cx="60"
          cy="60"
          r={radius}
          fill="none"
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          className={`${scoreRingColor(score)} transition-all duration-1000 ease-out`}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${scoreColor(score)}`}>
          {score}
        </span>
        <span className="text-xs text-gray-400 uppercase tracking-wide">
          /100
        </span>
      </div>
    </div>
  );
}

// --- Share Dropdown ---
function ShareDropdown({
  animalName,
  animalId,
  qualified,
  score,
}: {
  animalName: string;
  animalId: string;
  qualified: boolean;
  score: number;
}) {
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

  const pageUrl =
    typeof window !== "undefined"
      ? `${window.location.origin}/animals/${animalId}/pre-qualify`
      : "";

  const message = qualified
    ? PRE_QUALIFY_RESULT.shareQualifiedMsg(animalName, score)
    : PRE_QUALIFY_RESULT.shareNotQualifiedMsg(score);

  const whatsappUrl = `${WHATSAPP_BASE}?text=${encodeURIComponent(`${message} ${pageUrl}`)}`;

  const emailSubject = encodeURIComponent(PRE_QUALIFY_RESULT.shareEmailSubject);
  const emailBody = encodeURIComponent(`${message}\n\n${pageUrl}`);
  const emailUrl = `mailto:?subject=${emailSubject}&body=${emailBody}`;

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(pageUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback: do nothing
    }
  }, [pageUrl]);

  return (
    <div className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-sm"
        aria-expanded={open}
        aria-haspopup="true"
      >
        <Share2 className="h-4 w-4" />
        {PRE_QUALIFY_RESULT.shareTitle}
      </button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setOpen(false)}
            aria-hidden="true"
          />
          {/* Dropdown */}
          <div className="absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 z-20 py-1">
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => setOpen(false)}
            >
              <MessageCircle className="h-4 w-4 text-[#25D366]" />
              {PRE_QUALIFY_RESULT.shareWhatsApp}
            </a>
            <a
              href={emailUrl}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              onClick={() => setOpen(false)}
            >
              <Mail className="h-4 w-4 text-blue-500" />
              {PRE_QUALIFY_RESULT.shareEmail}
            </a>
            <button
              onClick={() => {
                handleCopy();
                setOpen(false);
              }}
              className="flex items-center gap-3 px-4 py-2.5 text-sm text-gray-700 hover:bg-gray-50 transition-colors w-full text-left"
            >
              {copied ? (
                <Check className="h-4 w-4 text-green-500" />
              ) : (
                <Copy className="h-4 w-4 text-gray-400" />
              )}
              {copied
                ? PRE_QUALIFY_RESULT.shareCopied
                : PRE_QUALIFY_RESULT.shareCopyLink}
            </button>
          </div>
        </>
      )}
    </div>
  );
}

// --- Main Page ---
export default function PreQualifyResultPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  const [animal, setAnimal] = useState<Animal | null>(null);
  const [result, setResult] = useState<PreQualifyResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;

    const storedResult = getResultFromStorage(params.id);
    if (!storedResult) {
      setIsLoading(false);
      setError("no_result");
      return;
    }
    setResult(storedResult);

    async function fetchAnimal() {
      try {
        const data = await getAnimalPublic(params.id);
        setAnimal(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Error loading animal");
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnimal();
  }, [params.id]);

  const handlePrint = useCallback(() => {
    window.print();
  }, []);

  // Filter alternatives: >= MIN_MATCH_SCORE, limit MAX_ALTERNATIVES
  const filteredAlternatives = result
    ? result.suggested_animals
        .filter((a) => a.match_score >= MIN_MATCH_SCORE)
        .sort((a, b) => b.match_score - a.match_score)
        .slice(0, MAX_ALTERNATIVES)
    : [];

  // --- Loading ---
  if (isLoading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#E8622A] border-r-transparent" />
        <p className="mt-3 text-gray-500">{PRE_QUALIFY_RESULT.loading}</p>
      </div>
    );
  }

  // --- No result data ---
  if (error === "no_result" || !result) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-50 mb-4">
          <AlertTriangle className="h-8 w-8 text-[#E8622A]" />
        </div>
        <p className="text-gray-700 mb-4">{PRE_QUALIFY_RESULT.noData}</p>
        <Link
          href={`/animals/${params.id}/pre-qualify`}
          className="text-[#E8622A] hover:underline font-medium"
        >
          {PRE_QUALIFY_RESULT.goToPreQualify}
        </Link>
      </div>
    );
  }

  // --- Error loading animal ---
  if (error) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 mb-4">{error}</p>
        <Link
          href="/animals"
          className="text-[#E8622A] hover:underline font-medium"
        >
          {PRE_QUALIFY_RESULT.backToAnimals}
        </Link>
      </div>
    );
  }

  const animalName = animal?.name ?? "este animal";
  const isQualified = result.qualified;

  return (
    <>
      {/* Print-only header */}
      <div className="hidden print:block print:mb-6">
        <h1 className="text-2xl font-bold">{PRE_QUALIFY_RESULT.printTitle}</h1>
        <p className="text-sm text-gray-500">
          {animalName} — {new Date().toLocaleDateString("es-PY")}
        </p>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-24 md:pb-10 print:px-0 print:py-4">
        {/* Breadcrumb */}
        <nav className="mb-6 text-sm text-gray-500 print:hidden">
          <Link
            href="/animals"
            className="hover:text-[#E8622A] transition-colors"
          >
            Animales
          </Link>
          <span className="mx-2">/</span>
          <Link
            href={`/animals/${params.id}`}
            className="hover:text-[#E8622A] transition-colors"
          >
            {animalName}
          </Link>
          <span className="mx-2">/</span>
          <Link
            href={`/animals/${params.id}/pre-qualify`}
            className="hover:text-[#E8622A] transition-colors"
          >
            {PRE_QUALIFY.breadcrumb}
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">Resultado</span>
        </nav>

        {/* Animal summary card */}
        {animal && (
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
              <p className="text-sm text-gray-500">
                {SPECIES_LABELS[animal.species] ?? animal.species}
              </p>
            </div>
          </div>
        )}

        {/* Main result card */}
        <div
          className={`rounded-xl border mb-8 overflow-hidden ${
            isQualified
              ? "bg-green-50 border-green-200"
              : "bg-amber-50 border-amber-200"
          }`}
        >
          <div className="p-8 text-center">
            {/* Large icon */}
            <div
              className={`inline-flex items-center justify-center w-20 h-20 rounded-full mb-5 ${
                isQualified ? "bg-green-100" : "bg-amber-100"
              }`}
            >
              {isQualified ? (
                <CheckCircle className="h-10 w-10 text-green-600" />
              ) : (
                <AlertTriangle className="h-10 w-10 text-amber-600" />
              )}
            </div>

            {/* Title */}
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-2">
              {isQualified
                ? PRE_QUALIFY_RESULT.qualifiedTitle(animalName)
                : PRE_QUALIFY_RESULT.notQualifiedTitle}
            </h1>
            <p className="text-gray-600 max-w-lg mx-auto mb-6">
              {isQualified
                ? PRE_QUALIFY_RESULT.qualifiedSubtitle
                : PRE_QUALIFY_RESULT.notQualifiedSubtitle}
            </p>

            {/* Score ring */}
            <div className="mb-4">
              <p className="text-xs text-gray-400 uppercase tracking-wide mb-2">
                {PRE_QUALIFY_RESULT.scoreLabel}
              </p>
              <ScoreRing score={result.score} />
            </div>

            {/* Wait time */}
            {result.estimated_wait_time && (
              <p className="text-sm text-gray-500 mt-2">
                {PRE_QUALIFY_RESULT.waitTime(result.estimated_wait_time)}
              </p>
            )}
          </div>

          {/* Qualified action buttons */}
          {isQualified && (
            <div className="px-8 pb-8 flex flex-col sm:flex-row gap-3 justify-center">
              <Link
                href={`/animals/${params.id}/apply`}
                className="inline-flex items-center justify-center bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
              >
                {PRE_QUALIFY_RESULT.continueToApplication}
              </Link>
              <Link
                href="/animals"
                className="inline-flex items-center justify-center bg-white text-gray-700 border border-gray-200 px-6 py-3 rounded-lg font-medium hover:bg-gray-50 transition-colors"
              >
                {PRE_QUALIFY_RESULT.browseSimilar}
              </Link>
            </div>
          )}
        </div>

        {/* Failed requirements */}
        {result.failed_requirements.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              {PRE_QUALIFY_RESULT.failedRequirementsTitle}
            </h2>
            <div className="space-y-3">
              {result.failed_requirements.map((req, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-4 rounded-lg border ${
                    req.is_mandatory
                      ? "bg-red-50 border-red-200"
                      : "bg-amber-50 border-amber-200"
                  }`}
                >
                  {req.is_mandatory ? (
                    <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                  ) : (
                    <AlertTriangle className="h-5 w-5 text-amber-500 flex-shrink-0 mt-0.5" />
                  )}
                  <div>
                    <p className="text-sm font-medium text-gray-800">
                      {PRE_QUALIFY.fieldLabels[req.requirement_type] ??
                        req.requirement_type}
                    </p>
                    <p className="text-sm text-gray-600 mt-0.5">
                      {req.message}
                    </p>
                    {req.is_mandatory && (
                      <span className="inline-block mt-1.5 text-xs font-medium text-red-600 bg-red-100 px-2 py-0.5 rounded">
                        {PRE_QUALIFY.mandatoryBadge}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Alternative animals */}
        {!isQualified && (
          <div className="mb-8">
            <h2 className="text-lg font-semibold text-gray-900 mb-1">
              {PRE_QUALIFY_RESULT.alternativesTitle}
            </h2>
            {filteredAlternatives.length > 0 ? (
              <>
                <p className="text-sm text-gray-500 mb-4">
                  {PRE_QUALIFY_RESULT.alternativesSubtitle(
                    filteredAlternatives.length
                  )}
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {filteredAlternatives.map((sa) => (
                    <Link
                      key={sa.id}
                      href={`/animals/${sa.id}`}
                      className="group flex items-center gap-4 p-4 bg-white rounded-xl border border-gray-200 hover:border-[#E8622A] hover:shadow-md transition-all"
                    >
                      {sa.photo_url ? (
                        <Image
                          src={sa.photo_url}
                          alt={sa.name}
                          width={64}
                          height={64}
                          className="w-16 h-16 rounded-lg object-cover"
                          sizes="64px"
                        />
                      ) : (
                        <div className="w-16 h-16 rounded-lg bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center text-gray-400">
                          <Star className="h-6 w-6" />
                        </div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-semibold text-gray-900 truncate group-hover:text-[#E8622A] transition-colors">
                          {sa.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {SPECIES_LABELS[
                            sa.species as keyof typeof SPECIES_LABELS
                          ] ?? sa.species}
                        </p>
                        <div className="flex items-center gap-1.5 mt-1">
                          <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                sa.match_score >= 80
                                  ? "bg-green-500"
                                  : "bg-amber-500"
                              }`}
                              style={{ width: `${sa.match_score}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs font-medium ${scoreColor(sa.match_score)}`}
                          >
                            {PRE_QUALIFY_RESULT.matchScore(sa.match_score)}
                          </span>
                        </div>
                      </div>
                      <ExternalLink className="h-4 w-4 text-gray-300 group-hover:text-[#E8622A] transition-colors flex-shrink-0" />
                    </Link>
                  ))}
                </div>
              </>
            ) : (
              <p className="text-sm text-gray-500 mt-2">
                {PRE_QUALIFY_RESULT.noAlternatives}
              </p>
            )}
          </div>
        )}

        {/* Action bar */}
        <div className="flex flex-col sm:flex-row gap-3 print:hidden">
          {!isQualified && (
            <Link
              href={`/animals/${params.id}/pre-qualify`}
              className="inline-flex items-center justify-center gap-2 px-6 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              {PRE_QUALIFY_RESULT.tryAgain}
            </Link>
          )}
          <Link
            href={`/animals/${params.id}`}
            className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {PRE_QUALIFY_RESULT.backToAnimal(animalName)}
          </Link>
          <Link
            href="/animals"
            className="inline-flex items-center justify-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {PRE_QUALIFY_RESULT.backToAnimals}
          </Link>
        </div>

        {/* Utility bar: share + print */}
        <div className="flex items-center justify-end gap-2 mt-6 print:hidden">
          <ShareDropdown
            animalName={animalName}
            animalId={params.id}
            qualified={isQualified}
            score={result.score}
          />
          <button
            onClick={handlePrint}
            className="inline-flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors text-sm"
          >
            <Printer className="h-4 w-4" />
            {PRE_QUALIFY_RESULT.printResults}
          </button>
        </div>
      </div>

      {/* Mobile sticky CTA */}
      {isQualified && (
        <div className="fixed bottom-0 inset-x-0 p-4 bg-white/95 backdrop-blur-sm border-t shadow-lg z-20 md:hidden print:hidden">
          <Link
            href={`/animals/${params.id}/apply`}
            className="block text-center bg-[#E8622A] text-white px-4 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
          >
            {PRE_QUALIFY_RESULT.continueToApplication}
          </Link>
        </div>
      )}

      {/* Print styles */}
      <style jsx global>{`
        @media print {
          nav,
          header,
          footer,
          .print\\:hidden {
            display: none !important;
          }
          body {
            font-size: 12pt;
            color: #000;
          }
          .print\\:block {
            display: block !important;
          }
          a {
            text-decoration: none;
            color: inherit;
          }
        }
      `}</style>
    </>
  );
}
