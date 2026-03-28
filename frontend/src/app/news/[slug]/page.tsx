"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

interface Post {
  id: string;
  title: string;
  slug: string;
  body_html: string;
  excerpt: string;
  author_id: string | null;
  featured_image_url: string | null;
  tags: string[];
  published_at: string | null;
  is_published: boolean;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

export default function NewsDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) return;
    fetch(`${API_BASE}/api/blog/${slug}`)
      .then((res) => {
        if (!res.ok) throw new Error("Noticia no encontrada");
        return res.json();
      })
      .then((data: Post) => {
        setPost(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-pulse text-gray-500 text-lg">Cargando...</div>
      </div>
    );
  }

  if (error || !post) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-gray-50 gap-4">
        <p className="text-red-600 text-lg">{error ?? "Noticia no encontrada"}</p>
        <Link href="/news" className="text-primary-600 hover:underline">
          Ver todas las noticias
        </Link>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {post.featured_image_url && (
        <div className="w-full h-64 sm:h-96 overflow-hidden">
          <img
            src={post.featured_image_url}
            alt={post.title}
            className="w-full h-full object-cover"
          />
        </div>
      )}

      <article className="max-w-3xl mx-auto px-4 py-8 sm:py-12">
        <Link
          href="/news"
          className="text-primary-600 hover:underline text-sm mb-4 inline-block"
        >
          ← Volver a noticias
        </Link>

        <h1 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">
          {post.title}
        </h1>

        <div className="flex items-center gap-4 text-sm text-gray-500 mb-6">
          {post.published_at && (
            <time>
              {new Date(post.published_at).toLocaleDateString("es-PY", {
                year: "numeric",
                month: "long",
                day: "numeric",
              })}
            </time>
          )}
          {post.tags.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {post.tags.map((tag) => (
                <Link
                  key={tag}
                  href={`/news?tag=${encodeURIComponent(tag)}`}
                  className="bg-primary-50 text-primary-700 px-2 py-0.5 rounded text-xs hover:bg-primary-100"
                >
                  {tag}
                </Link>
              ))}
            </div>
          )}
        </div>

        <div
          className="prose prose-lg max-w-none text-gray-700"
          dangerouslySetInnerHTML={{ __html: post.body_html }}
        />

        {/* Share */}
        <div className="border-t border-gray-200 pt-6 mt-10">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">
            Comparte esta noticia
          </h3>
          <div className="flex gap-3 flex-wrap">
            <a
              href={`https://wa.me/?text=${encodeURIComponent(post.title + " - " + (typeof window !== "undefined" ? window.location.href : ""))}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
            >
              WhatsApp
            </a>
            <a
              href={`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(typeof window !== "undefined" ? window.location.href : "")}`}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
            >
              Facebook
            </a>
            <button
              onClick={() => {
                if (typeof window !== "undefined") {
                  navigator.clipboard.writeText(window.location.href);
                }
              }}
              className="inline-flex items-center gap-2 bg-gray-200 text-gray-700 px-4 py-2 rounded-lg text-sm font-medium hover:bg-gray-300 transition-colors"
            >
              Copiar enlace
            </button>
          </div>
        </div>
      </article>
    </div>
  );
}
