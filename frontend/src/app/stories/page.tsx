"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

interface Story {
  id: string;
  title: string;
  adopter_name: string;
  story_text: string;
  quote: string | null;
  photo_url: string | null;
  published_at: string | null;
  is_featured: boolean;
}

interface StoryListResponse {
  items: Story[];
  total: number;
  page: number;
  page_size: number;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function StoriesPage() {
  const [data, setData] = useState<StoryListResponse | null>(null);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(`${API_BASE}/api/stories?page=${page}`)
      .then((res) => res.json())
      .then((json: StoryListResponse) => {
        setData(json);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [page]);

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 0;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-primary-600 to-orange-500 text-white py-12 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-3">
            Historias de Exito
          </h1>
          <p className="text-white/90 text-lg max-w-2xl mx-auto">
            Conoce a los animales que encontraron un hogar gracias a personas como tu.
          </p>
        </div>
      </div>

      {/* Stories grid */}
      <div className="max-w-5xl mx-auto px-4 py-10">
        {loading ? (
          <div className="text-center text-gray-500 py-20 animate-pulse">
            Cargando historias...
          </div>
        ) : !data || data.items.length === 0 ? (
          <div className="text-center text-gray-500 py-20">
            Aun no hay historias publicadas. Vuelve pronto!
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
              {data.items.map((story) => (
                <Link
                  key={story.id}
                  href={`/stories/${story.id}`}
                  className="bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100 hover:shadow-md transition-shadow group"
                >
                  {story.photo_url ? (
                    <div className="h-48 overflow-hidden">
                      <img
                        src={story.photo_url}
                        alt={story.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                      />
                    </div>
                  ) : (
                    <div className="h-48 bg-gradient-to-br from-primary-100 to-orange-100 flex items-center justify-center">
                      <svg className="w-12 h-12 text-primary-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                    </div>
                  )}
                  <div className="p-5">
                    {story.is_featured && (
                      <span className="inline-block bg-orange-100 text-orange-700 text-xs font-semibold px-2 py-0.5 rounded mb-2">
                        Destacada
                      </span>
                    )}
                    <h2 className="text-lg font-semibold text-gray-900 mb-1 group-hover:text-primary-600 transition-colors">
                      {story.title}
                    </h2>
                    <p className="text-sm text-gray-500 mb-2">
                      Adoptado por {story.adopter_name}
                    </p>
                    <p className="text-sm text-gray-600 line-clamp-3">
                      {story.story_text}
                    </p>
                    <span className="inline-block mt-3 text-primary-600 text-sm font-medium">
                      Leer historia →
                    </span>
                  </div>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-10">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Anterior
                </button>
                <span className="px-4 py-2 text-gray-600">
                  Pagina {page} de {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-100 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Siguiente
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
