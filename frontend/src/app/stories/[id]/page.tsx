"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

interface Story {
  id: string;
  title: string;
  animal_id: string | null;
  adopter_name: string;
  story_text: string;
  quote: string | null;
  photo_url: string | null;
  published_at: string | null;
  is_featured: boolean;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

function ShareButtons({ title, url }: { title: string; url: string }) {
  const encodedUrl = encodeURIComponent(url);
  const encodedTitle = encodeURIComponent(title);
  const whatsappText = encodeURIComponent(`${title} - ${url}`);

  return (
    <div className="flex gap-3 flex-wrap">
      <a
        href={`https://wa.me/?text=${whatsappText}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
      >
        WhatsApp
      </a>
      <a
        href={`https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
      >
        Facebook
      </a>
      <a
        href={`https://twitter.com/intent/tweet?text=${encodedTitle}&url=${encodedUrl}`}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-2 bg-sky-500 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-sky-600 transition-colors"
      >
        Twitter
      </a>
      <button
        onClick={() => {
          navigator.clipboard.writeText(url);
        }}
        className="inline-flex items-center gap-2 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors"
      >
        Copiar enlace
      </button>
    </div>
  );
}

export default function StoryDetailPage() {
  const params = useParams();
  const storyId = params.id as string;

  const [story, setStory] = useState<Story | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!storyId) return;
    fetch(`${API_BASE}/api/stories/${storyId}`)
      .then((res) => {
        if (!res.ok) throw new Error("Historia no encontrada");
        return res.json();
      })
      .then((data: Story) => {
        setStory(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [storyId]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500 text-lg">Cargando...</div>
      </div>
    );
  }

  if (error || !story) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-4">
        <p className="text-red-600 text-lg">{error ?? "Historia no encontrada"}</p>
        <Link href="/stories" className="text-primary-600 hover:underline">
          Ver todas las historias
        </Link>
      </div>
    );
  }

  const pageUrl = typeof window !== "undefined" ? window.location.href : "";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero photo */}
      {story.photo_url && (
        <div className="w-full h-64 sm:h-96 overflow-hidden">
          <img
            src={story.photo_url}
            alt={story.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      {/* Content */}
      <article className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
        <Link
          href="/stories"
          className="text-primary-600 hover:underline text-sm mb-4 inline-block"
        >
          ← Volver a historias
        </Link>

        {story.is_featured && (
          <span className="inline-block bg-orange-100 text-orange-700 text-xs font-semibold px-2 py-0.5 rounded mb-3 ml-3">
            Historia destacada
          </span>
        )}

        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
          {story.title}
        </h1>

        <p className="text-gray-500 mb-8">
          Adoptado por <span className="font-medium text-gray-700">{story.adopter_name}</span>
          {story.published_at && (
            <>
              {" "}&middot;{" "}
              {new Date(story.published_at).toLocaleDateString("es-PY", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </>
          )}
        </p>

        {/* Quote pull-out */}
        {story.quote && (
          <blockquote className="border-l-4 border-primary-400 bg-primary-50 px-6 py-4 rounded-r-lg mb-8 italic text-gray-700 text-lg">
            &ldquo;{story.quote}&rdquo;
            <footer className="mt-2 text-sm text-gray-500 not-italic">
              — {story.adopter_name}
            </footer>
          </blockquote>
        )}

        {/* Story text */}
        <div className="prose prose-lg max-w-none text-gray-700 leading-relaxed whitespace-pre-line mb-10">
          {story.story_text}
        </div>

        {/* Animal link */}
        {story.animal_id && (
          <div className="bg-primary-50 rounded-lg p-4 mb-8">
            <Link
              href={`/animals/${story.animal_id}`}
              className="text-primary-600 hover:underline font-medium"
            >
              Ver perfil del animal →
            </Link>
          </div>
        )}

        {/* Share */}
        <div className="border-t border-gray-200 pt-6">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Comparte esta historia
          </h3>
          <ShareButtons title={story.title} url={pageUrl} />
        </div>
      </article>
    </div>
  );
}
