"use client";

import { useState, useRef, useCallback } from "react";
import {
  Upload,
  Trash2,
  Star,
  GripVertical,
  Loader2,
  ImagePlus,
  AlertCircle,
  X,
} from "lucide-react";
import { api } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";
import type { AnimalPhoto } from "@/types/api";

/** Spanish UI strings. */
const S = {
  title: "Galeria de Fotos",
  upload: "Subir Foto",
  uploading: "Subiendo...",
  setPrimary: "Establecer como principal",
  isPrimary: "Foto principal",
  delete: "Eliminar",
  deleteConfirm: "Eliminar esta foto?",
  noPhotos: "Sin fotos. Sube la primera foto de este animal.",
  dragHint: "Arrastra para reordenar",
  uploadHint: "JPG, PNG o WebP. Maximo 10MB.",
  uploadError: "Error al subir la foto",
  deleteError: "Error al eliminar la foto",
  caption: "Descripcion",
  captionPlaceholder: "Descripcion opcional...",
  save: "Guardar",
  maxPhotos: "Maximo 10 fotos por animal",
} as const;

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const MAX_PHOTOS = 10;
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

interface MediaUploadResult {
  id: string;
  url: string;
  thumbnail_url: string | null;
  width: number;
  height: number;
  size_bytes: number;
  content_type: string;
  original_filename: string;
}

interface PhotoCreateResult {
  id: string;
  animal_id: string;
  url: string;
  caption: string | null;
  display_order: number;
  created_at: string;
}

interface PhotoGalleryManagerProps {
  animalId: string;
  animalName: string;
  photos: AnimalPhoto[];
  primaryPhotoUrl: string | null;
  onPhotosChanged: () => void;
}

export default function PhotoGalleryManager({
  animalId,
  animalName,
  photos,
  primaryPhotoUrl,
  onPhotosChanged,
}: PhotoGalleryManagerProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [settingPrimaryId, setSettingPrimaryId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [caption, setCaption] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const sortedPhotos = [...photos].sort(
    (a, b) => a.display_order - b.display_order
  );

  const canUpload = photos.length < MAX_PHOTOS;

  const handleFileSelect = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      // Reset input so the same file can be selected again
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      // Client-side validation
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError("Formato no soportado. Usa JPG, PNG o WebP.");
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        setError("El archivo es demasiado grande. Maximo 10MB.");
        return;
      }

      setError(null);
      setIsUploading(true);

      try {
        // Step 1: Upload file to media endpoint
        const formData = new FormData();
        formData.append("file", file);

        const token = getAccessToken();
        const uploadResponse = await fetch(`${API_BASE_URL}/api/media/upload`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });

        if (!uploadResponse.ok) {
          const errBody = await uploadResponse.json().catch(() => null);
          throw new Error(
            errBody?.message ?? errBody?.detail ?? S.uploadError
          );
        }

        const mediaResult =
          (await uploadResponse.json()) as MediaUploadResult;

        // Step 2: Attach photo to animal
        const nextOrder =
          sortedPhotos.length > 0
            ? sortedPhotos[sortedPhotos.length - 1].display_order + 1
            : 0;

        await api.post<PhotoCreateResult>(`/animals/${animalId}/photos`, {
          url: mediaResult.url,
          caption: caption.trim() || null,
          display_order: nextOrder,
        });

        // Step 3: If this is the first photo, set it as primary
        if (photos.length === 0) {
          await api.patch(`/animals/${animalId}`, {
            primary_photo_url: mediaResult.url,
          });
        }

        setCaption("");
        onPhotosChanged();
      } catch (err) {
        setError(
          err instanceof Error ? err.message : S.uploadError
        );
      } finally {
        setIsUploading(false);
      }
    },
    [animalId, caption, photos.length, sortedPhotos, onPhotosChanged]
  );

  const handleDelete = useCallback(
    async (photoId: string, photoUrl: string) => {
      if (!window.confirm(S.deleteConfirm)) return;

      setDeletingId(photoId);
      setError(null);

      try {
        await api.delete(`/animals/${animalId}/photos/${photoId}`);

        // If deleted photo was the primary, clear or set next photo as primary
        if (photoUrl === primaryPhotoUrl) {
          const remaining = photos.filter((p) => p.id !== photoId);
          const newPrimary =
            remaining.length > 0 ? remaining[0].url : null;
          await api.patch(`/animals/${animalId}`, {
            primary_photo_url: newPrimary,
          });
        }

        onPhotosChanged();
      } catch {
        setError(S.deleteError);
      } finally {
        setDeletingId(null);
      }
    },
    [animalId, photos, primaryPhotoUrl, onPhotosChanged]
  );

  const handleSetPrimary = useCallback(
    async (photoUrl: string, photoId: string) => {
      setSettingPrimaryId(photoId);
      setError(null);

      try {
        await api.patch(`/animals/${animalId}`, {
          primary_photo_url: photoUrl,
        });
        onPhotosChanged();
      } catch {
        setError("Error al establecer foto principal");
      } finally {
        setSettingPrimaryId(null);
      }
    },
    [animalId, onPhotosChanged]
  );

  return (
    <div className="rounded-lg border border-warm-border bg-warm-surface p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-warm-text-primary">
          {S.title}
        </h2>
        <span className="text-xs text-warm-text-tertiary">
          {photos.length}/{MAX_PHOTOS}
        </span>
      </div>

      {/* Error banner */}
      {error && (
        <div className="mb-4 flex items-center gap-2 rounded-lg bg-red-50 border border-red-200 px-3 py-2">
          <AlertCircle className="h-4 w-4 text-red-500 flex-shrink-0" />
          <p className="text-sm text-red-700 flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-red-400 hover:text-red-600">
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Photo grid */}
      {sortedPhotos.length > 0 ? (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
          {sortedPhotos.map((photo) => {
            const isPrimary = photo.url === primaryPhotoUrl;
            const isDeleting = deletingId === photo.id;
            const isSettingPrimary = settingPrimaryId === photo.id;

            return (
              <div
                key={photo.id}
                className={`relative group rounded-lg overflow-hidden border-2 transition-colors ${
                  isPrimary
                    ? "border-primary-500"
                    : "border-transparent hover:border-warm-border"
                }`}
              >
                <img
                  src={photo.url}
                  alt={photo.caption ?? animalName}
                  className="aspect-square w-full object-cover"
                />

                {/* Primary badge */}
                {isPrimary && (
                  <div className="absolute top-2 left-2 flex items-center gap-1 rounded-full bg-primary-600 px-2 py-0.5 text-xs font-medium text-white">
                    <Star className="h-3 w-3" />
                    Principal
                  </div>
                )}

                {/* Caption overlay */}
                {photo.caption && (
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-2 py-1.5">
                    <p className="text-xs text-white truncate">
                      {photo.caption}
                    </p>
                  </div>
                )}

                {/* Action overlay (visible on hover) */}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors flex items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
                  {!isPrimary && (
                    <button
                      onClick={() => handleSetPrimary(photo.url, photo.id)}
                      disabled={isSettingPrimary}
                      className="rounded-full bg-white/90 p-2 text-warm-text-primary hover:bg-white transition-colors shadow-sm"
                      title={S.setPrimary}
                    >
                      {isSettingPrimary ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Star className="h-4 w-4" />
                      )}
                    </button>
                  )}
                  <button
                    onClick={() => handleDelete(photo.id, photo.url)}
                    disabled={isDeleting}
                    className="rounded-full bg-red-500/90 p-2 text-white hover:bg-red-600 transition-colors shadow-sm"
                    title={S.delete}
                  >
                    {isDeleting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="h-4 w-4" />
                    )}
                  </button>
                </div>

                {/* Order indicator */}
                <div className="absolute top-2 right-2 rounded-full bg-black/50 px-1.5 py-0.5 text-xs text-white font-medium">
                  {photo.display_order + 1}
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center rounded-lg bg-warm-bg py-8 mb-4">
          <ImagePlus className="h-10 w-10 text-warm-text-tertiary mb-2" />
          <p className="text-sm text-warm-text-tertiary">{S.noPhotos}</p>
        </div>
      )}

      {/* Upload section */}
      {canUpload ? (
        <div className="space-y-3">
          <div>
            <label
              htmlFor="photo-caption"
              className="block text-xs font-medium text-warm-text-secondary mb-1"
            >
              {S.caption}
            </label>
            <input
              id="photo-caption"
              type="text"
              value={caption}
              onChange={(e) => setCaption(e.target.value)}
              placeholder={S.captionPlaceholder}
              className="w-full rounded-lg border border-warm-border bg-white px-3 py-2 text-sm text-warm-text-primary placeholder:text-warm-text-tertiary focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              disabled={isUploading}
            />
          </div>

          <div className="flex items-center gap-3">
            <input
              ref={fileInputRef}
              type="file"
              accept={ACCEPTED_TYPES.join(",")}
              onChange={handleFileSelect}
              className="hidden"
              id="photo-upload"
              disabled={isUploading}
            />
            <label
              htmlFor="photo-upload"
              className={`inline-flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors cursor-pointer ${
                isUploading
                  ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                  : "bg-primary-600 text-white hover:bg-primary-700"
              }`}
            >
              {isUploading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  {S.uploading}
                </>
              ) : (
                <>
                  <Upload className="h-4 w-4" />
                  {S.upload}
                </>
              )}
            </label>
            <span className="text-xs text-warm-text-tertiary">
              {S.uploadHint}
            </span>
          </div>
        </div>
      ) : (
        <p className="text-xs text-warm-text-tertiary text-center">
          {S.maxPhotos}
        </p>
      )}
    </div>
  );
}
