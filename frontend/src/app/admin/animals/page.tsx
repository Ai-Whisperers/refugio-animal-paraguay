"use client";

/**
 * Animals management page for staff admin panel.
 * Lists animals with filters, supports create/edit/delete operations.
 */

import { useCallback, useEffect, useState } from "react";
import type {
  Animal,
  AnimalCreate,
  AnimalUpdate,
  AnimalSpecies,
  AnimalStatus,
} from "@/types/api";
import {
  listAnimals,
  createAnimal,
  updateAnimal,
  deleteAnimal,
} from "@/lib/admin-api";
import StatusBadge from "@/components/admin/StatusBadge";
import AnimalFormModal from "@/components/admin/AnimalFormModal";
import ConfirmDialog from "@/components/admin/ConfirmDialog";

const SPECIES_FILTER_OPTIONS: Array<{ value: AnimalSpecies | ""; label: string }> = [
  { value: "", label: "All Species" },
  { value: "dog", label: "Dog" },
  { value: "cat", label: "Cat" },
  { value: "bird", label: "Bird" },
  { value: "rabbit", label: "Rabbit" },
  { value: "other", label: "Other" },
];

const STATUS_FILTER_OPTIONS: Array<{ value: AnimalStatus | ""; label: string }> = [
  { value: "", label: "All Statuses" },
  { value: "intake", label: "Intake" },
  { value: "available", label: "Available" },
  { value: "adopted", label: "Adopted" },
  { value: "fostered", label: "Fostered" },
  { value: "medical_hold", label: "Medical Hold" },
  { value: "reserved", label: "Reserved" },
];

const PAGE_SIZE = 20;

export default function AnimalsPage() {
  const [animals, setAnimals] = useState<Animal[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [speciesFilter, setSpeciesFilter] = useState<AnimalSpecies | "">("");
  const [statusFilter, setStatusFilter] = useState<AnimalStatus | "">("");
  const [page, setPage] = useState(0);

  // Modal state
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingAnimal, setEditingAnimal] = useState<Animal | null>(null);
  const [deletingAnimal, setDeletingAnimal] = useState<Animal | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchAnimals = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await listAnimals({
        species: speciesFilter || undefined,
        status: statusFilter || undefined,
        offset: page * PAGE_SIZE,
        limit: PAGE_SIZE,
      });
      setAnimals(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load animals");
    } finally {
      setIsLoading(false);
    }
  }, [speciesFilter, statusFilter, page]);

  useEffect(() => {
    fetchAnimals();
  }, [fetchAnimals]);

  const handleCreate = () => {
    setEditingAnimal(null);
    setIsFormOpen(true);
  };

  const handleEdit = (animal: Animal) => {
    setEditingAnimal(animal);
    setIsFormOpen(true);
  };

  const handleFormSubmit = async (data: AnimalCreate | AnimalUpdate) => {
    if (editingAnimal) {
      await updateAnimal(editingAnimal.id, data as AnimalUpdate);
    } else {
      await createAnimal(data as AnimalCreate);
    }
    await fetchAnimals();
  };

  const handleDeleteConfirm = async () => {
    if (!deletingAnimal) return;
    setIsDeleting(true);
    try {
      await deleteAnimal(deletingAnimal.id);
      setDeletingAnimal(null);
      await fetchAnimals();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete animal"
      );
    } finally {
      setIsDeleting(false);
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString("es-PY", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Animals</h1>
          <p className="text-sm text-gray-500">
            Manage shelter animal records
          </p>
        </div>
        <button
          onClick={handleCreate}
          className="px-4 py-2 text-sm font-medium text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors"
        >
          + Add Animal
        </button>
      </div>

      {/* Filters */}
      <div className="flex space-x-4 mb-6">
        <select
          value={speciesFilter}
          onChange={(e) => {
            setSpeciesFilter(e.target.value as AnimalSpecies | "");
            setPage(0);
          }}
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {SPECIES_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value as AnimalStatus | "");
            setPage(0);
          }}
          className="px-3 py-2 border border-gray-300 rounded-md shadow-sm text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
        >
          {STATUS_FILTER_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md text-sm">
          {error}
          <button
            onClick={() => setError(null)}
            className="ml-2 text-red-500 hover:text-red-700"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Table */}
      <div className="bg-white shadow-sm rounded-lg border border-gray-200 overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-2 text-sm text-gray-500">Loading animals...</p>
          </div>
        ) : animals.length === 0 ? (
          <div className="p-8 text-center text-gray-500">
            <p>No animals found.</p>
            <button
              onClick={handleCreate}
              className="mt-2 text-primary-600 hover:text-primary-700 text-sm font-medium"
            >
              Add the first animal
            </button>
          </div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Species
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {animals.map((animal) => (
                <tr key={animal.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="text-sm font-medium text-gray-900">
                      {animal.name}
                    </div>
                    {animal.description && (
                      <div className="text-sm text-gray-500 truncate max-w-xs">
                        {animal.description}
                      </div>
                    )}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                    {animal.species}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <StatusBadge status={animal.status} />
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(animal.created_at)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                    <button
                      onClick={() => handleEdit(animal)}
                      className="text-primary-600 hover:text-primary-700 font-medium mr-4"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => setDeletingAnimal(animal)}
                      className="text-red-600 hover:text-red-700 font-medium"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!isLoading && animals.length > 0 && (
        <div className="flex items-center justify-between mt-4">
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Previous
          </button>
          <span className="text-sm text-gray-500">Page {page + 1}</span>
          <button
            onClick={() => setPage((p) => p + 1)}
            disabled={animals.length < PAGE_SIZE}
            className="px-3 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
          >
            Next
          </button>
        </div>
      )}

      {/* Modals */}
      <AnimalFormModal
        isOpen={isFormOpen}
        animal={editingAnimal}
        onSubmit={handleFormSubmit}
        onClose={() => {
          setIsFormOpen(false);
          setEditingAnimal(null);
        }}
      />

      <ConfirmDialog
        isOpen={!!deletingAnimal}
        title="Delete Animal"
        message={`Are you sure you want to delete "${deletingAnimal?.name}"? This action cannot be undone.`}
        confirmLabel="Delete"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeletingAnimal(null)}
        isLoading={isDeleting}
      />
    </div>
  );
}
