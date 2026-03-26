"use client";

/**
 * Modal form for creating or editing an animal record.
 * Uses controlled inputs with basic validation.
 */

import { useEffect, useState } from "react";
import type {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  AnimalSpecies,
  AnimalStatus,
} from "@/types/api";

const SPECIES_OPTIONS: AnimalSpecies[] = [
  "dog",
  "cat",
  "bird",
  "rabbit",
  "other",
];

const STATUS_OPTIONS: AnimalStatus[] = [
  "intake",
  "available",
  "adopted",
  "fostered",
  "medical_hold",
  "reserved",
];

interface AnimalFormModalProps {
  isOpen: boolean;
  animal?: Animal | null;
  onSubmit: (data: AnimalCreate | AnimalUpdate) => Promise<void>;
  onClose: () => void;
}

export default function AnimalFormModal({
  isOpen,
  animal,
  onSubmit,
  onClose,
}: AnimalFormModalProps) {
  const isEditing = !!animal;

  const [name, setName] = useState("");
  const [species, setSpecies] = useState<AnimalSpecies>("dog");
  const [animalStatus, setAnimalStatus] = useState<AnimalStatus>("intake");
  const [birthDate, setBirthDate] = useState("");
  const [description, setDescription] = useState("");
  const [photoUrl, setPhotoUrl] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Populate form when editing
  useEffect(() => {
    if (animal) {
      setName(animal.name);
      setSpecies(animal.species);
      setAnimalStatus(animal.status);
      setBirthDate(animal.birth_date ?? "");
      setDescription(animal.description ?? "");
      setPhotoUrl(animal.primary_photo_url ?? "");
    } else {
      setName("");
      setSpecies("dog");
      setAnimalStatus("intake");
      setBirthDate("");
      setDescription("");
      setPhotoUrl("");
    }
    setError(null);
  }, [animal, isOpen]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      if (isEditing) {
        const updateData: AnimalUpdate = {};
        if (name !== animal.name) updateData.name = name;
        if (species !== animal.species) updateData.species = species;
        if (animalStatus !== animal.status) updateData.status = animalStatus;
        if (birthDate !== (animal.birth_date ?? ""))
          updateData.birth_date = birthDate || null;
        if (description !== (animal.description ?? ""))
          updateData.description = description || null;
        if (photoUrl !== (animal.primary_photo_url ?? ""))
          updateData.primary_photo_url = photoUrl || null;
        await onSubmit(updateData);
      } else {
        const createData: AnimalCreate = {
          name,
          species,
          status: animalStatus,
          birth_date: birthDate || null,
          description: description || null,
          primary_photo_url: photoUrl || null,
        };
        await onSubmit(createData);
      }
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save animal");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="fixed inset-0 bg-black bg-opacity-50"
        onClick={onClose}
      />
      <div className="relative bg-white rounded-lg shadow-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">
            {isEditing ? "Edit Animal" : "Add New Animal"}
          </h2>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label
                htmlFor="animal-name"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Name *
              </label>
              <input
                id="animal-name"
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={isSubmitting}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label
                  htmlFor="animal-species"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Species
                </label>
                <select
                  id="animal-species"
                  value={species}
                  onChange={(e) => setSpecies(e.target.value as AnimalSpecies)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  disabled={isSubmitting}
                >
                  {SPECIES_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s.charAt(0).toUpperCase() + s.slice(1)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label
                  htmlFor="animal-status"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Status
                </label>
                <select
                  id="animal-status"
                  value={animalStatus}
                  onChange={(e) =>
                    setAnimalStatus(e.target.value as AnimalStatus)
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                  disabled={isSubmitting}
                >
                  {STATUS_OPTIONS.map((s) => (
                    <option key={s} value={s}>
                      {s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label
                htmlFor="animal-birth-date"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Birth Date
              </label>
              <input
                id="animal-birth-date"
                type="date"
                value={birthDate}
                onChange={(e) => setBirthDate(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label
                htmlFor="animal-description"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Description
              </label>
              <textarea
                id="animal-description"
                rows={3}
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                disabled={isSubmitting}
              />
            </div>

            <div>
              <label
                htmlFor="animal-photo"
                className="block text-sm font-medium text-gray-700 mb-1"
              >
                Photo URL
              </label>
              <input
                id="animal-photo"
                type="url"
                value={photoUrl}
                onChange={(e) => setPhotoUrl(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
                placeholder="https://example.com/photo.jpg"
                disabled={isSubmitting}
              />
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 disabled:opacity-50 transition-colors"
              >
                {isSubmitting
                  ? "Saving..."
                  : isEditing
                    ? "Save Changes"
                    : "Add Animal"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
