"use client";

import { useEffect, useState, useCallback, useMemo } from "react";
import { useParams, useRouter } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import {
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowLeft,
  Loader2,
  ClipboardCheck,
} from "lucide-react";
import type {
  Animal,
  PreQualifyQuestion,
  PreQualifyResult,
} from "@/types/api";
import {
  getAnimalPublic,
  getPreQualifyQuestions,
  submitPreQualification,
} from "@/lib/public-api";
import { ANIMAL_DETAIL, COMMON, SPECIES_LABELS, PRE_QUALIFY } from "@/lib/strings";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";

// --- Constants ---
const STORAGE_KEY_PREFIX = "refugio_prequal_";
const RESULT_STORAGE_KEY = "refugio_prequal_result_";
const MAX_CHILD_AGE = 18;
const MAX_HOURS_ALONE = 24;

// --- Types ---
type FieldValue =
  | string
  | number
  | boolean
  | string[]
  | null;

type FormValues = Record<string, FieldValue>;
type FormErrors = Record<string, string>;

// --- LocalStorage helpers ---
function loadSavedValues(animalId: string): FormValues {
  if (typeof window === "undefined") return {};
  try {
    const stored = localStorage.getItem(`${STORAGE_KEY_PREFIX}${animalId}`);
    if (stored) return JSON.parse(stored) as FormValues;
  } catch {
    // corrupted data, start fresh
  }
  return {};
}

function saveValues(animalId: string, values: FormValues): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(
      `${STORAGE_KEY_PREFIX}${animalId}`,
      JSON.stringify(values)
    );
  } catch {
    // storage full, fail silently
  }
}

function clearSavedValues(animalId: string): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.removeItem(`${STORAGE_KEY_PREFIX}${animalId}`);
  } catch {
    // fail silently
  }
}

// --- Field validation ---
function validateField(
  question: PreQualifyQuestion,
  value: FieldValue
): string | null {
  const { requirement_type, is_mandatory } = question;

  if (is_mandatory) {
    if (value === null || value === undefined || value === "") {
      return PRE_QUALIFY.fieldRequired;
    }
    if (Array.isArray(value) && value.length === 0) {
      return PRE_QUALIFY.fieldRequired;
    }
  }

  // Type-specific validation
  if (requirement_type === "no_children_under" && typeof value === "number") {
    if (value < 0 || value > MAX_CHILD_AGE) return PRE_QUALIFY.ageRange;
  }
  if (requirement_type === "max_hours_alone" && typeof value === "number") {
    if (value < 0 || value > MAX_HOURS_ALONE) return PRE_QUALIFY.hoursRange;
  }
  if (requirement_type === "income_requirement" && typeof value === "number") {
    if (value <= 0) return PRE_QUALIFY.amountPositive;
  }

  return null;
}

// --- Build initial value for a question ---
function getInitialValue(requirementType: string): FieldValue {
  switch (requirementType) {
    case "yard_required":
    case "experience_required":
    case "housing_status":
      return "";
    case "no_children_under":
      return null;
    case "home_type":
    case "other_pets_ok":
      return [];
    case "max_hours_alone":
      return 8;
    case "income_requirement":
      return null;
    default:
      return "";
  }
}

// --- Build the answer dict for API submission ---
function buildAnswers(
  questions: PreQualifyQuestion[],
  values: FormValues
): Record<string, Record<string, unknown>> {
  const answers: Record<string, Record<string, unknown>> = {};
  for (const q of questions) {
    const val = values[q.id];
    if (val !== null && val !== undefined && val !== "") {
      answers[q.requirement_type] = { value: val };
    }
  }
  return answers;
}

// --- Field Components ---

interface FieldProps {
  question: PreQualifyQuestion;
  value: FieldValue;
  error: string | undefined;
  onChange: (questionId: string, value: FieldValue) => void;
}

function RadioField({ question, value, error, onChange }: FieldProps) {
  const optionsMap: Record<string, Record<string, string>> = {
    yard_required: PRE_QUALIFY.yardOptions,
    experience_required: PRE_QUALIFY.experienceOptions,
    housing_status: PRE_QUALIFY.housingStatusOptions,
  };
  const options = optionsMap[question.requirement_type] ?? {};

  return (
    <div role="radiogroup" aria-labelledby={`label-${question.id}`}>
      <div className="space-y-2">
        {Object.entries(options).map(([key, label]) => (
          <label
            key={key}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              value === key
                ? "border-[#E8622A] bg-orange-50"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input
              type="radio"
              name={question.id}
              value={key}
              checked={value === key}
              onChange={() => onChange(question.id, key)}
              className="h-4 w-4 text-[#E8622A] focus:ring-[#E8622A] border-gray-300"
              aria-invalid={!!error}
            />
            <span className="text-sm text-gray-700">{label}</span>
          </label>
        ))}
      </div>
    </div>
  );
}

function CheckboxField({ question, value, error, onChange }: FieldProps) {
  const currentValues = Array.isArray(value) ? value : [];

  const optionsMap: Record<string, Record<string, string>> = {
    home_type: PRE_QUALIFY.homeTypeOptions,
    other_pets_ok: PRE_QUALIFY.petOptions,
  };
  const options = optionsMap[question.requirement_type] ?? {};

  const noneLabel =
    question.requirement_type === "other_pets_ok"
      ? PRE_QUALIFY.noPets
      : undefined;

  function handleToggle(key: string) {
    if (key === "__none__") {
      onChange(question.id, []);
      return;
    }
    const next = currentValues.includes(key)
      ? currentValues.filter((v) => v !== key)
      : [...currentValues, key];
    onChange(question.id, next);
  }

  return (
    <div role="group" aria-labelledby={`label-${question.id}`}>
      <div className="space-y-2">
        {Object.entries(options).map(([key, label]) => (
          <label
            key={key}
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              currentValues.includes(key)
                ? "border-[#E8622A] bg-orange-50"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input
              type="checkbox"
              checked={currentValues.includes(key)}
              onChange={() => handleToggle(key)}
              className="h-4 w-4 rounded text-[#E8622A] focus:ring-[#E8622A] border-gray-300"
              aria-invalid={!!error}
            />
            <span className="text-sm text-gray-700">{label}</span>
          </label>
        ))}
        {noneLabel && (
          <label
            className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
              currentValues.length === 0
                ? "border-[#E8622A] bg-orange-50"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input
              type="checkbox"
              checked={currentValues.length === 0}
              onChange={() => handleToggle("__none__")}
              className="h-4 w-4 rounded text-[#E8622A] focus:ring-[#E8622A] border-gray-300"
            />
            <span className="text-sm text-gray-700">{noneLabel}</span>
          </label>
        )}
      </div>
    </div>
  );
}

function NumberField({ question, value, error, onChange }: FieldProps) {
  const hasNoChildren =
    question.requirement_type === "no_children_under" && value === null;

  return (
    <div>
      {question.requirement_type === "no_children_under" && (
        <label className="flex items-center gap-3 mb-3 p-3 rounded-lg border cursor-pointer transition-colors border-gray-200 hover:border-gray-300">
          <input
            type="checkbox"
            checked={hasNoChildren}
            onChange={() =>
              onChange(question.id, hasNoChildren ? 0 : null)
            }
            className="h-4 w-4 rounded text-[#E8622A] focus:ring-[#E8622A] border-gray-300"
          />
          <span className="text-sm text-gray-700">
            {PRE_QUALIFY.noChildren}
          </span>
        </label>
      )}
      {!hasNoChildren && (
        <input
          type="number"
          id={`field-${question.id}`}
          value={typeof value === "number" ? value : ""}
          onChange={(e) => {
            const parsed = e.target.value === "" ? null : Number(e.target.value);
            onChange(question.id, parsed);
          }}
          min={0}
          max={
            question.requirement_type === "no_children_under"
              ? MAX_CHILD_AGE
              : question.requirement_type === "income_requirement"
                ? undefined
                : MAX_HOURS_ALONE
          }
          className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
            error ? "border-red-300" : "border-gray-300"
          }`}
          placeholder={
            question.requirement_type === "income_requirement"
              ? PRE_QUALIFY.currencyPlaceholder
              : ""
          }
          aria-invalid={!!error}
          aria-describedby={error ? `error-${question.id}` : undefined}
        />
      )}
    </div>
  );
}

function SliderField({ question, value, error, onChange }: FieldProps) {
  const numValue = typeof value === "number" ? value : 8;

  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">0h</span>
        <span className="text-lg font-semibold text-[#E8622A]">
          {PRE_QUALIFY.hoursLabel(numValue)}
        </span>
        <span className="text-sm text-gray-500">24h</span>
      </div>
      <input
        type="range"
        id={`field-${question.id}`}
        min={0}
        max={MAX_HOURS_ALONE}
        step={1}
        value={numValue}
        onChange={(e) => onChange(question.id, Number(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-[#E8622A]"
        aria-invalid={!!error}
        aria-describedby={error ? `error-${question.id}` : undefined}
        aria-valuemin={0}
        aria-valuemax={MAX_HOURS_ALONE}
        aria-valuenow={numValue}
        aria-valuetext={PRE_QUALIFY.hoursLabel(numValue)}
      />
    </div>
  );
}

// --- Render the right field for a question ---
function renderField(props: FieldProps) {
  const { question } = props;
  switch (question.requirement_type) {
    case "yard_required":
    case "experience_required":
    case "housing_status":
      return <RadioField {...props} />;
    case "home_type":
    case "other_pets_ok":
      return <CheckboxField {...props} />;
    case "max_hours_alone":
      return <SliderField {...props} />;
    case "no_children_under":
    case "income_requirement":
      return <NumberField {...props} />;
    default:
      // Fallback: text input
      return (
        <input
          type="text"
          id={`field-${question.id}`}
          value={typeof props.value === "string" ? props.value : ""}
          onChange={(e) => props.onChange(question.id, e.target.value)}
          className={`w-full px-4 py-2.5 border rounded-lg focus:ring-2 focus:ring-[#E8622A]/30 focus:border-[#E8622A] outline-none transition-colors ${
            props.error ? "border-red-300" : "border-gray-300"
          }`}
          aria-invalid={!!props.error}
        />
      );
  }
}

// --- Field validity icon ---
function FieldStatus({
  value,
  error,
  isMandatory,
}: {
  value: FieldValue;
  error: string | undefined;
  isMandatory: boolean;
}) {
  if (error) {
    return <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" aria-label="Invalido" />;
  }
  const hasValue =
    value !== null &&
    value !== undefined &&
    value !== "" &&
    !(Array.isArray(value) && value.length === 0);

  if (hasValue) {
    return <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0" aria-label="Valido" />;
  }
  if (isMandatory) {
    return <AlertTriangle className="h-5 w-5 text-amber-400 flex-shrink-0" aria-label="Pendiente" />;
  }
  return null;
}

// =======================
// Main Page Component
// =======================
export default function PreQualifyPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();

  // Animal data
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoadingAnimal, setIsLoadingAnimal] = useState(true);
  const [animalError, setAnimalError] = useState<string | null>(null);

  // Questions
  const [questions, setQuestions] = useState<PreQualifyQuestion[]>([]);
  const [isLoadingQuestions, setIsLoadingQuestions] = useState(true);
  const [questionsError, setQuestionsError] = useState<string | null>(null);

  // Form state
  const [values, setValues] = useState<FormValues>({});
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Set<string>>(new Set());

  // Submission
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<PreQualifyResult | null>(null);

  // --- Fetch animal ---
  useEffect(() => {
    if (!params.id) return;
    async function fetchAnimal() {
      setIsLoadingAnimal(true);
      setAnimalError(null);
      try {
        const data = await getAnimalPublic(params.id);
        setAnimal(data);
      } catch (err) {
        setAnimalError(err instanceof Error ? err.message : COMMON.error);
      } finally {
        setIsLoadingAnimal(false);
      }
    }
    fetchAnimal();
  }, [params.id]);

  // --- Fetch questions ---
  useEffect(() => {
    if (!params.id) return;
    async function fetchQuestions() {
      setIsLoadingQuestions(true);
      setQuestionsError(null);
      try {
        const data = await getPreQualifyQuestions(params.id);
        setQuestions(data.questions);
        // Initialize form values from saved + defaults
        const saved = loadSavedValues(params.id);
        const initial: FormValues = {};
        for (const q of data.questions) {
          initial[q.id] =
            saved[q.id] !== undefined ? saved[q.id] : getInitialValue(q.requirement_type);
        }
        setValues(initial);
      } catch (err) {
        setQuestionsError(
          err instanceof Error ? err.message : PRE_QUALIFY.loadError
        );
      } finally {
        setIsLoadingQuestions(false);
      }
    }
    fetchQuestions();
  }, [params.id]);

  // --- Auto-save values ---
  useEffect(() => {
    if (params.id && questions.length > 0 && !result) {
      saveValues(params.id, values);
    }
  }, [values, params.id, questions.length, result]);

  // --- Field change handler ---
  const handleFieldChange = useCallback(
    (questionId: string, value: FieldValue) => {
      setValues((prev) => ({ ...prev, [questionId]: value }));
      setTouched((prev) => new Set(prev).add(questionId));
      // Clear error on change
      setErrors((prev) => {
        if (!prev[questionId]) return prev;
        const next = { ...prev };
        delete next[questionId];
        return next;
      });
    },
    []
  );

  // --- Progress calculation ---
  const progress = useMemo(() => {
    if (questions.length === 0) return 0;
    let filled = 0;
    for (const q of questions) {
      const val = values[q.id];
      const hasValue =
        val !== null &&
        val !== undefined &&
        val !== "" &&
        !(Array.isArray(val) && val.length === 0);
      if (hasValue) filled++;
    }
    return Math.round((filled / questions.length) * 100);
  }, [questions, values]);

  // --- Form is complete (all mandatory fields filled + valid) ---
  const isFormComplete = useMemo(() => {
    for (const q of questions) {
      if (q.is_mandatory) {
        const val = values[q.id];
        const fieldError = validateField(q, val);
        if (fieldError) return false;
      }
    }
    return questions.length > 0;
  }, [questions, values]);

  // --- Validate all fields ---
  function validateAll(): boolean {
    const newErrors: FormErrors = {};
    for (const q of questions) {
      const fieldError = validateField(q, values[q.id]);
      if (fieldError) {
        newErrors[q.id] = fieldError;
      }
    }
    setErrors(newErrors);
    setTouched(new Set(questions.map((q) => q.id)));
    return Object.keys(newErrors).length === 0;
  }

  // --- Submit ---
  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitError(null);

    if (!validateAll() || !animal) return;

    setIsSubmitting(true);
    try {
      const answers = buildAnswers(questions, values);
      const qualResult = await submitPreQualification({
        animal_id: animal.id,
        answers,
      });
      // Store result in sessionStorage for the dedicated result page
      try {
        sessionStorage.setItem(
          `${RESULT_STORAGE_KEY}${params.id}`,
          JSON.stringify(qualResult)
        );
      } catch {
        // sessionStorage unavailable — fall back to inline result
      }
      setResult(qualResult);
      clearSavedValues(params.id);
      // Navigate to dedicated result page
      router.push(`/animals/${params.id}/pre-qualify/result`);
    } catch (err) {
      setSubmitError(
        err instanceof Error ? err.message : PRE_QUALIFY.submitError
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  // --- Retry loading questions ---
  function retryLoadQuestions() {
    setQuestionsError(null);
    setIsLoadingQuestions(true);
    getPreQualifyQuestions(params.id)
      .then((data) => {
        setQuestions(data.questions);
        const saved = loadSavedValues(params.id);
        const initial: FormValues = {};
        for (const q of data.questions) {
          initial[q.id] =
            saved[q.id] !== undefined
              ? saved[q.id]
              : getInitialValue(q.requirement_type);
        }
        setValues(initial);
      })
      .catch((err) => {
        setQuestionsError(
          err instanceof Error ? err.message : PRE_QUALIFY.loadError
        );
      })
      .finally(() => setIsLoadingQuestions(false));
  }

  // --- Loading state ---
  if (isLoadingAnimal || isLoadingQuestions) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#E8622A] border-r-transparent" />
        <p className="mt-3 text-gray-500">
          {isLoadingQuestions ? PRE_QUALIFY.loadingQuestions : COMMON.loading}
        </p>
      </div>
    );
  }

  // --- Animal error ---
  if (animalError || !animal) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 mb-4">
          {animalError ?? ANIMAL_DETAIL.notFound}
        </p>
        <Link
          href="/animals"
          className="text-[#E8622A] hover:underline font-medium"
        >
          {ANIMAL_DETAIL.backToAnimals}
        </Link>
      </div>
    );
  }

  // --- Questions error ---
  if (questionsError) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <p className="text-red-600 mb-4">{questionsError}</p>
        <button
          onClick={retryLoadQuestions}
          className="px-6 py-2.5 bg-[#E8622A] text-white rounded-lg font-medium hover:bg-[#d4571f] transition-colors"
        >
          {PRE_QUALIFY.retryButton}
        </button>
      </div>
    );
  }

  // --- No questions (animal has no requirements) ---
  if (questions.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-16 text-center">
        <div className="bg-green-50 rounded-xl p-8 border border-green-200">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-green-100 mb-4">
            <CheckCircle className="h-8 w-8 text-green-600" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-3">
            {animal.name}
          </h1>
          <p className="text-gray-600 mb-6">{PRE_QUALIFY.noQuestions}</p>
          <Link
            href={`/animals/${animal.id}/apply`}
            className="inline-block px-6 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
          >
            {PRE_QUALIFY.applyDirectly}
          </Link>
        </div>
      </div>
    );
  }

  // --- Result page ---
  if (result) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {/* Animal summary */}
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

        {/* Score + status */}
        <div
          className={`rounded-xl p-8 border mb-6 text-center ${
            result.qualified
              ? "bg-green-50 border-green-200"
              : "bg-amber-50 border-amber-200"
          }`}
        >
          <div
            className={`inline-flex items-center justify-center w-16 h-16 rounded-full mb-4 ${
              result.qualified ? "bg-green-100" : "bg-amber-100"
            }`}
          >
            {result.qualified ? (
              <CheckCircle className="h-8 w-8 text-green-600" />
            ) : (
              <AlertTriangle className="h-8 w-8 text-amber-600" />
            )}
          </div>
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            {result.qualified
              ? "Sos compatible!"
              : "Hay algunos requisitos que no se cumplen"}
          </h1>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/80 border border-gray-200 mb-4">
            <ClipboardCheck className="h-4 w-4 text-gray-500" />
            <span className="text-sm font-medium text-gray-700">
              Puntaje: {result.score}/100
            </span>
          </div>
          {result.estimated_wait_time && (
            <p className="text-sm text-gray-500">
              Tiempo estimado de espera: {result.estimated_wait_time}
            </p>
          )}
        </div>

        {/* Failed requirements */}
        {result.failed_requirements.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Requisitos no cumplidos
            </h2>
            <div className="space-y-2">
              {result.failed_requirements.map((req, idx) => (
                <div
                  key={idx}
                  className={`flex items-start gap-3 p-3 rounded-lg border ${
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
                    <p className="text-sm font-medium text-gray-700">
                      {PRE_QUALIFY.fieldLabels[req.requirement_type] ??
                        req.requirement_type}
                    </p>
                    <p className="text-sm text-gray-600">{req.message}</p>
                    {req.is_mandatory && (
                      <span className="inline-block mt-1 text-xs font-medium text-red-600">
                        {PRE_QUALIFY.mandatoryBadge}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Suggested animals */}
        {result.suggested_animals.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Otros animales que podrian ser compatibles
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {result.suggested_animals.map((sa) => (
                <Link
                  key={sa.id}
                  href={`/animals/${sa.id}`}
                  className="flex items-center gap-3 p-3 rounded-lg border border-gray-200 hover:border-[#E8622A] transition-colors"
                >
                  {sa.photo_url ? (
                    <Image
                      src={sa.photo_url}
                      alt={sa.name}
                      width={48}
                      height={48}
                      className="w-12 h-12 rounded-lg object-cover"
                      sizes="48px"
                    />
                  ) : (
                    <div className="w-12 h-12 rounded-lg bg-gray-100 flex items-center justify-center text-gray-400 text-xs">
                      {sa.species.charAt(0).toUpperCase()}
                    </div>
                  )}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {sa.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {SPECIES_LABELS[sa.species as keyof typeof SPECIES_LABELS] ??
                        sa.species}{" "}
                      — {sa.match_score}% compatible
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex flex-col sm:flex-row gap-3">
          {result.qualified && (
            <Link
              href={`/animals/${animal.id}/apply`}
              className="flex-1 text-center px-6 py-3 bg-[#E8622A] text-white rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
            >
              Solicitar adopcion
            </Link>
          )}
          <Link
            href={`/animals/${animal.id}`}
            className="flex-1 text-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {PRE_QUALIFY.backToAnimal(animal.name)}
          </Link>
          {!result.qualified && (
            <button
              onClick={() => {
                setResult(null);
                setSubmitError(null);
              }}
              className="flex-1 text-center px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              Modificar respuestas
            </button>
          )}
        </div>
      </div>
    );
  }

  // --- Form ---
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500" aria-label="Breadcrumb">
        <Link
          href="/animals"
          className="hover:text-[#E8622A] transition-colors"
        >
          {ANIMAL_DETAIL.breadcrumbAnimals}
        </Link>
        <span className="mx-2">/</span>
        <Link
          href={`/animals/${animal.id}`}
          className="hover:text-[#E8622A] transition-colors"
        >
          {animal.name}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{PRE_QUALIFY.breadcrumb}</span>
      </nav>

      {/* Animal summary */}
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

      {/* Title */}
      <h1 className="text-2xl md:text-3xl font-bold text-gray-900 mb-2">
        {PRE_QUALIFY.title}
      </h1>
      <p className="text-gray-500 mb-6">{PRE_QUALIFY.subtitle(animal.name)}</p>

      {/* Progress bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            {PRE_QUALIFY.progressLabel(progress)}
          </span>
        </div>
        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-[#E8622A] rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
            role="progressbar"
            aria-valuenow={progress}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={PRE_QUALIFY.progressLabel(progress)}
          />
        </div>
      </div>

      {/* Submission error */}
      {submitError && (
        <div
          className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm"
          role="alert"
        >
          {submitError}
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6" noValidate>
        {questions.map((question) => {
          const fieldError = touched.has(question.id)
            ? errors[question.id]
            : undefined;
          const label =
            PRE_QUALIFY.fieldLabels[question.requirement_type] ??
            question.human_readable_description;
          const helpText =
            PRE_QUALIFY.fieldHelp[question.requirement_type] ?? null;

          return (
            <div
              key={question.id}
              className="bg-white rounded-lg border border-gray-100 p-5 shadow-sm"
            >
              {/* Label row */}
              <div className="flex items-center justify-between mb-1">
                <label
                  id={`label-${question.id}`}
                  htmlFor={`field-${question.id}`}
                  className="text-sm font-medium text-gray-700"
                >
                  {label}
                </label>
                <div className="flex items-center gap-2">
                  {question.is_mandatory ? (
                    <span className="text-xs font-medium text-red-500">
                      {PRE_QUALIFY.mandatoryBadge}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-400">
                      {PRE_QUALIFY.optionalBadge}
                    </span>
                  )}
                  <FieldStatus
                    value={values[question.id]}
                    error={fieldError}
                    isMandatory={question.is_mandatory}
                  />
                </div>
              </div>

              {/* Help text */}
              {helpText && (
                <p
                  id={`help-${question.id}`}
                  className="text-xs text-gray-400 mb-3"
                >
                  {helpText}
                </p>
              )}

              {/* Field */}
              {renderField({
                question,
                value: values[question.id],
                error: fieldError,
                onChange: handleFieldChange,
              })}

              {/* Error */}
              {fieldError && (
                <p
                  id={`error-${question.id}`}
                  className="mt-2 text-sm text-red-600"
                  role="alert"
                >
                  {fieldError}
                </p>
              )}
            </div>
          );
        })}

        {/* Actions */}
        <div className="flex gap-3 pt-2">
          <button
            type="button"
            onClick={() => router.push(`/animals/${animal.id}`)}
            className="px-6 py-3 bg-gray-100 text-gray-700 rounded-lg font-medium hover:bg-gray-200 transition-colors inline-flex items-center gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            {PRE_QUALIFY.backToAnimal(animal.name)}
          </button>
          <button
            type="submit"
            disabled={!isFormComplete || isSubmitting}
            className="flex-1 bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] disabled:opacity-50 disabled:cursor-not-allowed transition-colors inline-flex items-center justify-center gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                {PRE_QUALIFY.submitting}
              </>
            ) : (
              <>
                <ClipboardCheck className="h-5 w-5" />
                {PRE_QUALIFY.submitButton}
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
