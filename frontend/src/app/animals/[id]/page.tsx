"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import type { Animal, AnimalStatus } from "@/types/api";
import { getAnimalPublic } from "@/lib/public-api";

const STATUS_LABELS: Record<AnimalStatus, string> = {
  intake: "New Arrival",
  quarantine: "Quarantine",
  available: "Available for Adoption",
  foster: "In Foster Care",
  under_treatment: "Under Medical Treatment",
  adopted: "Adopted",
  deceased: "Deceased",
};

function statusBadgeClass(status: AnimalStatus): string {
  switch (status) {
    case "available":
      return "bg-green-100 text-green-800";
    case "adopted":
      return "bg-blue-100 text-blue-800";
    case "foster":
      return "bg-purple-100 text-purple-800";
    case "under_treatment":
      return "bg-yellow-100 text-yellow-800";
    case "quarantine":
      return "bg-red-100 text-red-800";
    case "intake":
      return "bg-gray-100 text-gray-800";
    default:
      return "bg-gray-100 text-gray-600";
  }
}

function calculateAge(birthDate: string): string {
  const birth = new Date(birthDate);
  const now = new Date();
  const months =
    (now.getFullYear() - birth.getFullYear()) * 12 +
    (now.getMonth() - birth.getMonth());

  if (months < 1) return "Less than 1 month old";
  if (months < 12) return `${months} month${months === 1 ? "" : "s"} old`;

  const years = Math.floor(months / 12);
  const remaining = months % 12;
  if (remaining === 0) return `${years} year${years === 1 ? "" : "s"} old`;
  return `${years} year${years === 1 ? "" : "s"}, ${remaining} month${remaining === 1 ? "" : "s"} old`;
}

export default function AnimalDetailPage() {
  const params = useParams<{ id: string }>();
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!params.id) return;

    async function fetchAnimal() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getAnimalPublic(params.id);
        setAnimal(data);
      } catch (err) {
        setError(
          err instanceof Error ? err.message : "Failed to load animal details"
        );
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnimal();
  }, [params.id]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary-600 border-r-transparent" />
        <p className="mt-3 text-gray-500">Loading animal details...</p>
      </div>
    );
  }

  if (error || !animal) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <p className="text-5xl mb-4">🐾</p>
        <p className="text-red-600 mb-4">{error ?? "Animal not found"}</p>
        <Link
          href="/animals"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Back to Animals
        </Link>
      </div>
    );
  }

  const isAvailable = animal.status === "available";

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Breadcrumb */}
      <nav className="mb-6 text-sm text-gray-500">
        <Link href="/animals" className="hover:text-primary-600">
          Animals
        </Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{animal.name}</span>
      </nav>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {/* Photo Section */}
        <div className="relative">
          {animal.primary_photo_url ? (
            <Image
              src={animal.primary_photo_url}
              alt={animal.name}
              width={800}
              height={384}
              className="w-full h-64 md:h-96 object-cover"
              unoptimized
            />
          ) : (
            <div className="w-full h-64 md:h-96 bg-gray-100 flex items-center justify-center text-8xl">
              {animal.species === "dog"
                ? "🐕"
                : animal.species === "cat"
                  ? "🐈"
                  : "🐾"}
            </div>
          )}
        </div>

        {/* Gallery Thumbnails */}
        {animal.photos.length > 0 && (
          <div className="flex gap-2 px-6 py-3 bg-gray-50 overflow-x-auto">
            {animal.photos.map((photo) => (
              <Image
                key={photo.id}
                src={photo.url}
                alt={photo.caption ?? animal.name}
                width={80}
                height={80}
                className="w-20 h-20 object-cover rounded-lg border border-gray-200 flex-shrink-0"
                unoptimized
              />
            ))}
          </div>
        )}

        {/* Info Section */}
        <div className="p-6 md:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
            <h1 className="text-3xl font-heading font-bold text-gray-900">
              {animal.name}
            </h1>
            <span
              className={`inline-block text-sm px-3 py-1 rounded-full font-medium ${statusBadgeClass(animal.status)}`}
            >
              {STATUS_LABELS[animal.status]}
            </span>
          </div>

          {/* Details Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <DetailItem label="Species" value={animal.species} capitalize />
            {animal.birth_date && (
              <DetailItem label="Age" value={calculateAge(animal.birth_date)} />
            )}
            <DetailItem
              label="Arrived"
              value={new Date(animal.created_at).toLocaleDateString("en-US", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            />
          </div>

          {/* Description */}
          {animal.description && (
            <div className="mb-8">
              <h2 className="text-lg font-semibold text-gray-900 mb-2">
                About {animal.name}
              </h2>
              <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                {animal.description}
              </p>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3">
            {isAvailable ? (
              <Link
                href={`/animals/${animal.id}/apply`}
                className="inline-flex items-center justify-center bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
              >
                Apply to Adopt {animal.name}
              </Link>
            ) : (
              <div className="px-6 py-3 bg-gray-100 text-gray-500 rounded-lg text-center font-medium">
                This animal is not currently available for adoption
              </div>
            )}
            <Link
              href="/animals"
              className="inline-flex items-center justify-center bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
            >
              Back to Animals
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

function DetailItem({
  label,
  value,
  capitalize = false,
}: {
  label: string;
  value: string;
  capitalize?: boolean;
}) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
      <p
        className={`text-gray-900 font-medium ${capitalize ? "capitalize" : ""}`}
      >
        {value}
      </p>
    </div>
  );
}
