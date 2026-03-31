"use client";

import { useState, useRef, useCallback } from "react";
import { Camera, X, RotateCcw, Loader2 } from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024; // 2 MB
const COMPRESSION_THRESHOLD_BYTES = 5 * 1024 * 1024; // 5 MB — show progress
const PREVIEW_SIZE_PX = 150;
const ACCEPTED_IMAGE_TYPES = "image/*";

// ---------------------------------------------------------------------------
// Image compression utility (pure browser, no external dependency)
// ---------------------------------------------------------------------------

interface CompressionResult {
  file: File;
  originalSize: number;
  compressedSize: number;
}

async function compressImage(
  file: File,
  maxSizeBytes: number = MAX_FILE_SIZE_BYTES,
  onProgress?: (pct: number) => void
): Promise<CompressionResult> {
  const originalSize = file.size;

  // Already small enough
  if (file.size <= maxSizeBytes) {
    onProgress?.(100);
    return { file, originalSize, compressedSize: file.size };
  }

  onProgress?.(10);

  return new Promise((resolve, reject) => {
    const img = new Image();
    const url = URL.createObjectURL(file);

    img.onload = () => {
      URL.revokeObjectURL(url);
      onProgress?.(30);

      const canvas = document.createElement("canvas");
      let { width, height } = img;

      // Scale down if very large
      const maxDim = 2048;
      if (width > maxDim || height > maxDim) {
        const ratio = Math.min(maxDim / width, maxDim / height);
        width = Math.round(width * ratio);
        height = Math.round(height * ratio);
      }

      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext("2d");
      if (!ctx) {
        reject(new Error("Could not get canvas context"));
        return;
      }

      ctx.drawImage(img, 0, 0, width, height);
      onProgress?.(60);

      // Try progressively lower quality
      let quality = 0.8;
      const tryCompress = () => {
        canvas.toBlob(
          (blob) => {
            if (!blob) {
              reject(new Error("Canvas toBlob returned null"));
              return;
            }

            onProgress?.(80 + (0.8 - quality) * 100);

            if (blob.size <= maxSizeBytes || quality <= 0.1) {
              const compressed = new File([blob], file.name, {
                type: "image/jpeg",
                lastModified: Date.now(),
              });
              onProgress?.(100);
              resolve({
                file: compressed,
                originalSize,
                compressedSize: compressed.size,
              });
            } else {
              quality -= 0.1;
              tryCompress();
            }
          },
          "image/jpeg",
          quality
        );
      };

      tryCompress();
    };

    img.onerror = () => {
      URL.revokeObjectURL(url);
      reject(new Error("Failed to load image for compression"));
    };

    img.src = url;
  });
}

// ---------------------------------------------------------------------------
// Component props
// ---------------------------------------------------------------------------

export interface CameraCaptureProps {
  /** Label for the camera button, e.g. "Tomar foto de tu hogar" */
  label: string;
  /** Whether to use rear camera (environment) or front (user) */
  captureMode?: "environment" | "user";
  /** Called with the (possibly compressed) File when image is ready */
  onImageCapture: (file: File) => void;
  /** Called when image is removed */
  onImageRemove?: () => void;
  /** Optional className for the container */
  className?: string;
}

// ---------------------------------------------------------------------------
// CameraCapture component
// ---------------------------------------------------------------------------

export default function CameraCapture({
  label,
  captureMode = "environment",
  onImageCapture,
  onImageRemove,
  className = "",
}: CameraCaptureProps) {
  const [preview, setPreview] = useState<string | null>(null);
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionProgress, setCompressionProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setError(null);

      try {
        const showProgress = file.size > COMPRESSION_THRESHOLD_BYTES;
        setIsCompressing(true);
        setCompressionProgress(0);

        const result = await compressImage(
          file,
          MAX_FILE_SIZE_BYTES,
          showProgress ? setCompressionProgress : undefined
        );

        // Create preview URL
        const previewUrl = URL.createObjectURL(result.file);
        setPreview(previewUrl);
        setIsCompressing(false);

        onImageCapture(result.file);
      } catch {
        setError("No se pudo procesar la imagen");
        setIsCompressing(false);
      }

      // Reset input so same file can be re-selected
      if (inputRef.current) {
        inputRef.current.value = "";
      }
    },
    [onImageCapture]
  );

  const handleRemove = useCallback(() => {
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    setPreview(null);
    setError(null);
    onImageRemove?.();
  }, [preview, onImageRemove]);

  const handleRetake = useCallback(() => {
    handleRemove();
    // Trigger file input after removal
    setTimeout(() => inputRef.current?.click(), 100);
  }, [handleRemove]);

  return (
    <div className={`flex flex-col gap-3 ${className}`}>
      {/* Hidden file input */}
      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED_IMAGE_TYPES}
        capture={captureMode}
        onChange={handleFileChange}
        className="sr-only"
        aria-label={label}
      />

      {/* Preview or capture button */}
      {preview ? (
        <div className="flex items-start gap-3">
          {/* Thumbnail preview */}
          <div
            className="relative flex-shrink-0 rounded-lg overflow-hidden border border-gray-200"
            style={{ width: PREVIEW_SIZE_PX, height: PREVIEW_SIZE_PX }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={preview}
              alt="Vista previa de la foto capturada"
              className="w-full h-full object-cover"
            />
          </div>

          {/* Action buttons */}
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={handleRetake}
              className="flex items-center gap-2 px-3 py-2 text-sm text-primary-600 hover:text-primary-800 hover:bg-primary-50 rounded-md min-h-[44px] min-w-[44px]"
              aria-label="Tomar otra foto"
            >
              <RotateCcw className="w-4 h-4" aria-hidden="true" />
              <span>Tomar otra</span>
            </button>
            <button
              type="button"
              onClick={handleRemove}
              className="flex items-center gap-2 px-3 py-2 text-sm text-red-600 hover:text-red-800 hover:bg-red-50 rounded-md min-h-[44px] min-w-[44px]"
              aria-label="Eliminar foto"
            >
              <X className="w-4 h-4" aria-hidden="true" />
              <span>Eliminar</span>
            </button>
          </div>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          disabled={isCompressing}
          className="flex items-center justify-center gap-2 px-4 py-3 border-2 border-dashed border-gray-300 rounded-lg text-gray-600 hover:border-primary-400 hover:text-primary-600 hover:bg-primary-50 transition-colors min-h-[44px]"
          aria-label={label}
        >
          {isCompressing ? (
            <>
              <Loader2
                className="w-5 h-5 animate-spin"
                aria-hidden="true"
              />
              <span>
                Comprimiendo...{" "}
                {compressionProgress > 0 && `${Math.round(compressionProgress)}%`}
              </span>
            </>
          ) : (
            <>
              <Camera className="w-5 h-5" aria-hidden="true" />
              <span>{label}</span>
            </>
          )}
        </button>
      )}

      {/* Error message */}
      {error && (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}

export {
  compressImage,
  MAX_FILE_SIZE_BYTES,
  COMPRESSION_THRESHOLD_BYTES,
  PREVIEW_SIZE_PX,
  ACCEPTED_IMAGE_TYPES,
};
