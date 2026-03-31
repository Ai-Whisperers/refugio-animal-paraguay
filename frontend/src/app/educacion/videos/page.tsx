"use client";

import { VideoGallery } from "@/components/VideoEmbed";
import type { VideoItem } from "@/components/VideoEmbed";

// ---------------------------------------------------------------------------
// Sample educational video content
// ---------------------------------------------------------------------------

const EDUCATIONAL_VIDEOS: VideoItem[] = [
  {
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Cuidado basico de mascotas",
    description: "Aprende los fundamentos del cuidado responsable de animales domesticos.",
    category: "Cuidado animal",
  },
  {
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "La importancia de la esterilizacion",
    description: "Por que esterilizar es esencial para el control de la poblacion animal.",
    category: "Esterilizacion",
  },
  {
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Primeros auxilios para mascotas",
    description: "Que hacer en caso de emergencia con tu mascota.",
    category: "Salud",
  },
  {
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Adopcion responsable",
    description: "Guia completa para prepararte antes de adoptar un animal.",
    category: "Adopcion",
  },
  {
    url: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    title: "Alimentacion saludable",
    description: "Consejos de nutricion para perros y gatos.",
    category: "Cuidado animal",
  },
  {
    url: "https://vimeo.com/123456789",
    title: "Voluntariado en refugios",
    description: "Como puedes ayudar como voluntario en un refugio animal.",
    category: "Voluntariado",
  },
];

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function EducationalVideosPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <header className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">
            Videos educativos
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Recursos audiovisuales sobre cuidado animal responsable, adopcion, salud y mas.
          </p>
        </header>

        <VideoGallery videos={EDUCATIONAL_VIDEOS} columns={2} />

        <div className="mt-12 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Quieres sugerir un video?
          </h2>
          <p className="text-sm text-gray-600">
            Si conoces contenido educativo que pueda ayudar a nuestra comunidad,
            contactanos por WhatsApp o email.
          </p>
        </div>
      </div>
    </div>
  );
}
