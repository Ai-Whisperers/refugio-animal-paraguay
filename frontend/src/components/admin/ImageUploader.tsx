"use client";

import { useState, useRef, useCallback } from "react";
import { Upload, X, Loader2, AlertCircle, Image as ImageIcon } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

// --- Spanish labels ---
const S = {
  LABEL: "Imagen",
  SELECT: "Seleccionar imagen",
  CHANGE: "Cambiar imagen",
  REMOVE: "Quitar imagen",
  UPLOADING: "Subiendo...",
  DRAG_HINT: "Arrastra una imagen o haz clic para seleccionar",
  FORMAT_HINT: "JPG, PNG o WebP. Maximo 10 MB.",
  UPLOAD_ERROR: "Error al subir la imagen",
  RETRY: "Reintentar",
  INVALID_TYPE: "Formato no permitido. Usa JPG, PNG o WebP.",
  FILE_TOO_LARGE: "El archivo excede 10 MB.",
} as const;

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10 MB

interface MediaUploadResponse {
  id: string;
  url: string;
  thumbnail_url: string | null;
  width: number;
  height: number;
  size_bytes: number;
  content_type: string;
  original_filename: string;
}

interface ImageUploaderProps {
  /** Label displayed above the uploader */
  label?: string;
  /** Current image URL (for edit forms with existing images) */
  value: string;
  /** Called with the new URL after upload, or empty string on remove */
  onChange: (url: string) => void;
  /** Whether the image is required */
  required?: boolean;
}

export default function ImageUploader({
  label = S.LABEL,
  value,
  onChange,
  required = false,
}: ImageUploaderProps) {
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const displayUrl = previewUrl ?? value;

  const handleUpload = useCallback(
    async (file: File) => {
      // Client-side validation
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError(S.INVALID_TYPE);
        return;
      }
      if (file.size > MAX_FILE_SIZE_BYTES) {
        setError(S.FILE_TOO_LARGE);
        return;
      }

      setError(null);
      setIsUploading(true);

      // Optimistic preview
      const localPreview = URL.createObjectURL(file);
      setPreviewUrl(localPreview);

      try {
        const token = getAccessToken();
        const formData = new FormData();
        formData.append("file", file);

        const response = await fetch(`${API_BASE_URL}/api/media/upload`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: formData,
        });

        if (!response.ok) {
          let detail = S.UPLOAD_ERROR;
          try {
            const body = await response.json();
            detail = body.detail?.message ?? body.message ?? detail;
          } catch {
            // Non-JSON response
          }
          throw new Error(detail);
        }

        const data: MediaUploadResponse = await response.json();
        // Use the server URL, revoke the local preview
        URL.revokeObjectURL(localPreview);
        setPreviewUrl(null);
        onChange(data.url);
      } catch (err) {
        URL.revokeObjectURL(localPreview);
        setPreviewUrl(null);
        setError(err instanceof Error ? err.message : S.UPLOAD_ERROR);
      } finally {
        setIsUploading(false);
      }
    },
    [onChange],
  );

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      handleUpload(file);
    }
    // Reset input so re-selecting the same file triggers onChange
    e.target.value = "";
  }

  function handleRemove() {
    setPreviewUrl(null);
    setError(null);
    onChange("");
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleUpload(file);
    }
  }

  return (
    <div>
      <label className="mb-1 block text-sm font-medium text-warm-text-primary">
        {label}
        {required && " *"}
      </label>

      {/* Error banner */}
      {error && (
        <div className="mb-2 flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2">
          <AlertCircle className="h-4 w-4 flex-shrink-0 text-red-500" />
          <p className="flex-1 text-xs text-red-700">{error}</p>
          <button
            type="button"
            onClick={() => setError(null)}
            className="text-xs font-medium text-red-600 hover:text-red-800"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {displayUrl ? (
        /* Image preview with change/remove actions */
        <div className="relative overflow-hidden rounded-lg border border-warm-border">
          <img
            src={displayUrl}
            alt="Vista previa"
            className="h-48 w-full object-cover"
          />
          {isUploading && (
            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
              <Loader2 className="h-6 w-6 animate-spin text-white" />
            </div>
          )}
          <div className="absolute bottom-2 right-2 flex gap-1.5">
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              disabled={isUploading}
              className="rounded-md bg-white/90 px-2.5 py-1 text-xs font-medium text-warm-text-primary shadow-sm backdrop-blur-sm transition-colors hover:bg-white disabled:opacity-50"
            >
              {S.CHANGE}
            </button>
            <button
              type="button"
              onClick={handleRemove}
              disabled={isUploading}
              className="rounded-md bg-red-500/90 px-2.5 py-1 text-xs font-medium text-white shadow-sm backdrop-blur-sm transition-colors hover:bg-red-600 disabled:opacity-50"
            >
              {S.REMOVE}
            </button>
          </div>
        </div>
      ) : (
        /* Drop zone */
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => !isUploading && fileInputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed px-4 py-8 transition-colors ${
            isDragOver
              ? "border-primary-400 bg-primary-50"
              : "border-warm-border bg-warm-bg hover:border-primary-300 hover:bg-warm-surface"
          } ${isUploading ? "pointer-events-none opacity-60" : ""}`}
        >
          {isUploading ? (
            <>
              <Loader2 className="mb-2 h-8 w-8 animate-spin text-primary-400" />
              <p className="text-sm text-warm-text-secondary">{S.UPLOADING}</p>
            </>
          ) : (
            <>
              <div className="mb-2 rounded-lg bg-primary-50 p-2.5">
                {isDragOver ? (
                  <ImageIcon className="h-6 w-6 text-primary-500" />
                ) : (
                  <Upload className="h-6 w-6 text-primary-400" />
                )}
              </div>
              <p className="text-sm text-warm-text-secondary">{S.DRAG_HINT}</p>
              <p className="mt-1 text-xs text-warm-text-tertiary">{S.FORMAT_HINT}</p>
            </>
          )}
        </div>
      )}

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept={ACCEPTED_TYPES.join(",")}
        onChange={handleFileSelect}
        className="hidden"
        aria-label={label}
      />
    </div>
  );
}
