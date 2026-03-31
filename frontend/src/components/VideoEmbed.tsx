"use client";

import { useState } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const YOUTUBE_REGEX = /(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([\w-]{11})/;
const VIMEO_REGEX = /vimeo\.com\/(\d+)/;
const DEFAULT_ASPECT_RATIO = "16/9";
const THUMBNAIL_BASE_URL = "https://img.youtube.com/vi";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface VideoEmbedProps {
  url: string;
  title?: string;
  autoplay?: boolean;
  aspectRatio?: string;
  className?: string;
}

type VideoProvider = "youtube" | "vimeo" | "unknown";

interface ParsedVideo {
  provider: VideoProvider;
  videoId: string;
  embedUrl: string;
  thumbnailUrl: string | null;
}

// ---------------------------------------------------------------------------
// URL Parser
// ---------------------------------------------------------------------------

export function parseVideoUrl(url: string): ParsedVideo | null {
  const ytMatch = url.match(YOUTUBE_REGEX);
  if (ytMatch) {
    const videoId = ytMatch[1];
    return {
      provider: "youtube",
      videoId,
      embedUrl: `https://www.youtube.com/embed/${videoId}`,
      thumbnailUrl: `${THUMBNAIL_BASE_URL}/${videoId}/maxresdefault.jpg`,
    };
  }

  const vimeoMatch = url.match(VIMEO_REGEX);
  if (vimeoMatch) {
    const videoId = vimeoMatch[1];
    return {
      provider: "vimeo",
      videoId,
      embedUrl: `https://player.vimeo.com/video/${videoId}`,
      thumbnailUrl: null,
    };
  }

  return null;
}

// ---------------------------------------------------------------------------
// Provider Badge
// ---------------------------------------------------------------------------

function ProviderBadge({ provider }: { provider: VideoProvider }) {
  const labels: Record<VideoProvider, string> = {
    youtube: "YouTube",
    vimeo: "Vimeo",
    unknown: "Video",
  };

  const colors: Record<VideoProvider, string> = {
    youtube: "bg-red-100 text-red-700",
    vimeo: "bg-blue-100 text-blue-700",
    unknown: "bg-gray-100 text-gray-700",
  };

  return (
    <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${colors[provider]}`}>
      {labels[provider]}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Video Embed Component
// ---------------------------------------------------------------------------

export default function VideoEmbed({
  url,
  title = "Video educativo",
  autoplay = false,
  aspectRatio = DEFAULT_ASPECT_RATIO,
  className = "",
}: VideoEmbedProps) {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);

  const parsed = parseVideoUrl(url);

  if (!parsed) {
    return (
      <div
        className={`bg-gray-100 rounded-xl p-6 text-center ${className}`}
        role="alert"
      >
        <p className="text-gray-500 text-sm">
          URL de video no soportada. Usa enlaces de YouTube o Vimeo.
        </p>
      </div>
    );
  }

  const embedSrc = `${parsed.embedUrl}?rel=0&modestbranding=1${autoplay ? "&autoplay=1" : ""}`;

  // Lazy-load: show thumbnail for YouTube until user clicks
  if (!isLoaded && parsed.provider === "youtube" && parsed.thumbnailUrl && !autoplay) {
    return (
      <div className={`relative rounded-xl overflow-hidden ${className}`}>
        <div style={{ aspectRatio }}>
          <button
            onClick={() => setIsLoaded(true)}
            className="w-full h-full relative group cursor-pointer min-h-[44px]"
            aria-label={`Reproducir video: ${title}`}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={parsed.thumbnailUrl}
              alt={`Miniatura: ${title}`}
              className="w-full h-full object-cover"
              loading="lazy"
            />
            <div className="absolute inset-0 bg-black/30 group-hover:bg-black/40 transition-colors flex items-center justify-center">
              <div className="w-16 h-16 bg-red-600 rounded-full flex items-center justify-center group-hover:scale-110 transition-transform">
                <svg
                  viewBox="0 0 24 24"
                  fill="white"
                  className="w-8 h-8 ml-1"
                  aria-hidden="true"
                >
                  <path d="M8 5v14l11-7z" />
                </svg>
              </div>
            </div>
            <div className="absolute top-3 left-3">
              <ProviderBadge provider={parsed.provider} />
            </div>
          </button>
        </div>
        {title && (
          <p className="text-sm text-gray-600 mt-2 font-medium">{title}</p>
        )}
      </div>
    );
  }

  if (hasError) {
    return (
      <div
        className={`bg-red-50 rounded-xl p-6 text-center border border-red-200 ${className}`}
        role="alert"
      >
        <p className="text-red-600 text-sm font-medium">
          Error al cargar el video
        </p>
        <p className="text-red-500 text-xs mt-1">
          Verifica que la URL sea correcta e intenta de nuevo.
        </p>
      </div>
    );
  }

  return (
    <div className={`rounded-xl overflow-hidden ${className}`}>
      <div style={{ aspectRatio }} className="relative bg-gray-900">
        <iframe
          src={embedSrc}
          title={title}
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
          allowFullScreen
          className="absolute inset-0 w-full h-full"
          loading="lazy"
          onError={() => setHasError(true)}
        />
      </div>
      <div className="flex items-center gap-2 mt-2">
        <ProviderBadge provider={parsed.provider} />
        {title && (
          <p className="text-sm text-gray-600 font-medium">{title}</p>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Video Gallery Component
// ---------------------------------------------------------------------------

export interface VideoItem {
  url: string;
  title: string;
  description?: string;
  category?: string;
}

export function VideoGallery({
  videos,
  columns = 2,
}: {
  videos: VideoItem[];
  columns?: number;
}) {
  const [filter, setFilter] = useState<string>("all");

  const categories = [
    "all",
    ...new Set(videos.map((v) => v.category).filter(Boolean)),
  ];

  const filtered =
    filter === "all"
      ? videos
      : videos.filter((v) => v.category === filter);

  const gridCols =
    columns === 1
      ? "grid-cols-1"
      : columns === 3
        ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3"
        : "grid-cols-1 md:grid-cols-2";

  return (
    <div>
      {categories.length > 2 && (
        <div className="flex flex-wrap gap-2 mb-6" role="group" aria-label="Filtrar videos por categoria">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setFilter(cat as string)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors min-h-[44px] ${
                filter === cat
                  ? "bg-orange-600 text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
              aria-pressed={filter === cat}
            >
              {cat === "all" ? "Todos" : cat}
            </button>
          ))}
        </div>
      )}

      {filtered.length === 0 && (
        <p className="text-gray-400 text-center py-8">
          No hay videos en esta categoria.
        </p>
      )}

      <div className={`grid ${gridCols} gap-6`} role="list" aria-label="Galeria de videos">
        {filtered.map((video, idx) => (
          <div key={idx} role="listitem">
            <VideoEmbed url={video.url} title={video.title} />
            {video.description && (
              <p className="text-xs text-gray-500 mt-1">{video.description}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
