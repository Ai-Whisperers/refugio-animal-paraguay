"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const MAX_RELATED_ARTICLES = 3;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ArticleDetail {
  id: string;
  title: string;
  content: string;
  excerpt: string;
  category: string;
  read_time_minutes: number;
  published_at: string;
  updated_at: string | null;
  author: string;
  featured_image: string | null;
  slug: string;
  tags: string[];
}

interface RelatedArticle {
  id: string;
  title: string;
  excerpt: string;
  category: string;
  read_time_minutes: number;
  slug: string;
}

// ---------------------------------------------------------------------------
// Sample data (fallback)
// ---------------------------------------------------------------------------

const SAMPLE_ARTICLES: Record<string, ArticleDetail> = {
  "guia-adoptar-perro-paraguay": {
    id: "art-1",
    title: "Guia completa para adoptar un perro en Paraguay",
    content: `
## Antes de adoptar

Adoptar un perro es una decision importante que cambiara tu vida y la del animal. En Paraguay, miles de perros esperan una segunda oportunidad en refugios y rescates.

### Preparacion del hogar

Antes de traer a tu nuevo compañero a casa, asegurate de tener:

- Un espacio seguro y cercado donde pueda estar
- Comedero y bebedero apropiados para su tamaño
- Alimento de buena calidad recomendado por el veterinario
- Una cama o espacio comodo para descansar
- Collar, correa y placa de identificacion

### Los primeros dias

Los primeros 7 a 14 dias son cruciales para la adaptacion. Tu nuevo perro necesita:

- Paciencia mientras se adapta al nuevo entorno
- Una rutina establecida de alimentacion y paseos
- Un area tranquila donde pueda retirarse si se siente abrumado
- Visita al veterinario para chequeo general

## El proceso de adopcion

En Refugio Animal Paraguay, el proceso incluye:

1. Completar el formulario de solicitud
2. Entrevista con nuestro equipo
3. Visita al refugio para conocer animales disponibles
4. Periodo de prueba de convivencia
5. Formalizacion de la adopcion

## Compromiso a largo plazo

Adoptar significa comprometerte por toda la vida del animal, que puede ser de 10 a 15 años. Esto incluye alimentacion, salud veterinaria, ejercicio y mucho amor.
    `.trim(),
    excerpt: "Todo lo que necesitas saber antes de adoptar: preparacion del hogar, primeros dias, y compromisos a largo plazo.",
    category: "adopcion",
    read_time_minutes: 8,
    published_at: "2026-03-15",
    updated_at: null,
    author: "Refugio Animal Paraguay",
    featured_image: null,
    slug: "guia-adoptar-perro-paraguay",
    tags: ["adopcion", "perros", "guia", "cuidado"],
  },
  "calendario-vacunacion-mascotas": {
    id: "art-2",
    title: "Vacunacion: calendario esencial para tu mascota",
    content: `
## Por que vacunar?

La vacunacion es la mejor forma de proteger a tu mascota contra enfermedades graves y potencialmente mortales.

### Calendario para perros

- 6-8 semanas: Primera dosis de parvovirus y moquillo
- 10-12 semanas: Segunda dosis + hepatitis + leptospirosis
- 14-16 semanas: Tercera dosis + rabia
- Anual: Refuerzo de todas las vacunas

### Calendario para gatos

- 8 semanas: Triple felina (panleucopenia, calicivirus, rinotraqueitis)
- 12 semanas: Refuerzo triple felina + leucemia felina
- 16 semanas: Rabia
- Anual: Refuerzos

## Vacunas obligatorias en Paraguay

La vacuna antirrabica es obligatoria por ley en Paraguay. Asegurate de mantener al dia el carnet de vacunacion.
    `.trim(),
    excerpt: "Las vacunas que tu perro o gato necesita segun su edad.",
    category: "salud",
    read_time_minutes: 6,
    published_at: "2026-03-10",
    updated_at: null,
    author: "Refugio Animal Paraguay",
    featured_image: null,
    slug: "calendario-vacunacion-mascotas",
    tags: ["vacunacion", "salud", "prevencion"],
  },
};

const SAMPLE_RELATED: RelatedArticle[] = [
  {
    id: "art-3",
    title: "Alimentacion casera vs comercial",
    excerpt: "Comparamos las opciones de alimentacion para tu mascota.",
    category: "nutricion",
    read_time_minutes: 10,
    slug: "alimentacion-casera-vs-comercial",
  },
  {
    id: "art-5",
    title: "Primeros auxilios para mascotas",
    excerpt: "Que hacer en caso de emergencia.",
    category: "salud",
    read_time_minutes: 7,
    slug: "primeros-auxilios-mascotas",
  },
  {
    id: "art-6",
    title: "Cuidados del cachorro adoptado",
    excerpt: "Los primeros 30 dias son cruciales.",
    category: "cuidado",
    read_time_minutes: 9,
    slug: "cuidados-cachorro-adoptado",
  },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function Breadcrumb({ title }: { title: string }) {
  return (
    <nav aria-label="Ruta de navegacion" className="mb-6">
      <ol className="flex items-center gap-2 text-sm text-gray-500">
        <li>
          <Link href="/educacion" className="hover:text-orange-600 transition-colors">
            Centro Educativo
          </Link>
        </li>
        <li aria-hidden="true">/</li>
        <li className="text-gray-900 font-medium truncate max-w-xs">{title}</li>
      </ol>
    </nav>
  );
}

function ArticleHeader({ article }: { article: ArticleDetail }) {
  const categoryLabels: Record<string, string> = {
    adopcion: "Adopcion",
    salud: "Salud",
    nutricion: "Nutricion",
    cuidado: "Cuidado animal",
    comportamiento: "Comportamiento",
    esterilizacion: "Esterilizacion",
  };

  return (
    <header className="mb-8">
      <div className="flex items-center gap-3 mb-3">
        <span className="text-xs font-medium text-orange-600 bg-orange-50 px-2.5 py-1 rounded-full">
          {categoryLabels[article.category] ?? article.category}
        </span>
        <span className="text-xs text-gray-400">
          {article.read_time_minutes} min de lectura
        </span>
      </div>
      <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 leading-tight">
        {article.title}
      </h1>
      <div className="flex items-center gap-4 mt-4 text-sm text-gray-500">
        <span>Por {article.author}</span>
        <time dateTime={article.published_at}>
          {new Date(article.published_at).toLocaleDateString("es-PY", {
            year: "numeric",
            month: "long",
            day: "numeric",
          })}
        </time>
      </div>
      {article.tags.length > 0 && (
        <div className="flex flex-wrap gap-2 mt-4" aria-label="Etiquetas del articulo">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
    </header>
  );
}

function ArticleContent({ content }: { content: string }) {
  // Simple markdown-like rendering for headings and lists
  const renderContent = (text: string) => {
    const lines = text.split("\n");
    const elements: JSX.Element[] = [];
    let listItems: string[] = [];
    let key = 0;

    const flushList = () => {
      if (listItems.length > 0) {
        elements.push(
          <ul key={key++} className="list-disc list-inside space-y-1 mb-4 text-gray-700">
            {listItems.map((item, i) => (
              <li key={i} className="text-sm leading-relaxed">{item}</li>
            ))}
          </ul>
        );
        listItems = [];
      }
    };

    for (const line of lines) {
      const trimmed = line.trim();

      if (trimmed.startsWith("## ")) {
        flushList();
        elements.push(
          <h2 key={key++} className="text-xl font-bold text-gray-900 mt-8 mb-4">
            {trimmed.replace("## ", "")}
          </h2>
        );
      } else if (trimmed.startsWith("### ")) {
        flushList();
        elements.push(
          <h3 key={key++} className="text-lg font-semibold text-gray-900 mt-6 mb-3">
            {trimmed.replace("### ", "")}
          </h3>
        );
      } else if (trimmed.startsWith("- ")) {
        listItems.push(trimmed.replace("- ", ""));
      } else if (/^\d+\.\s/.test(trimmed)) {
        flushList();
        listItems.push(trimmed.replace(/^\d+\.\s/, ""));
      } else if (trimmed === "") {
        flushList();
      } else {
        flushList();
        elements.push(
          <p key={key++} className="text-sm text-gray-700 leading-relaxed mb-4">
            {trimmed}
          </p>
        );
      }
    }
    flushList();
    return elements;
  };

  return (
    <div className="prose-custom">
      {renderContent(content)}
    </div>
  );
}

function ShareButtons({ title, slug }: { title: string; slug: string }) {
  const url = typeof window !== "undefined"
    ? `${window.location.origin}/educacion/articulos/${slug}`
    : "";

  const handleShare = async () => {
    if (navigator.share) {
      await navigator.share({ title, url });
    }
  };

  return (
    <div className="flex items-center gap-3 py-4 border-t border-gray-200 mt-8" aria-label="Compartir articulo">
      <span className="text-sm font-medium text-gray-500">Compartir:</span>
      <a
        href={`https://wa.me/?text=${encodeURIComponent(`${title} - ${url}`)}`}
        target="_blank"
        rel="noopener noreferrer"
        className="text-green-600 hover:text-green-700 text-sm font-medium min-h-[44px] flex items-center"
        aria-label="Compartir por WhatsApp"
      >
        WhatsApp
      </a>
      {typeof navigator !== "undefined" && navigator.share && (
        <button
          onClick={handleShare}
          className="text-blue-600 hover:text-blue-700 text-sm font-medium min-h-[44px] min-w-[44px]"
          aria-label="Compartir usando menu del dispositivo"
        >
          Compartir
        </button>
      )}
    </div>
  );
}

function RelatedArticleCard({ article }: { article: RelatedArticle }) {
  return (
    <Link
      href={`/educacion/articulos/${article.slug}`}
      className="block bg-white rounded-xl border border-gray-200 p-4 hover:shadow-md transition-shadow"
    >
      <span className="text-xs font-medium text-orange-600">{article.category}</span>
      <h4 className="font-semibold text-gray-900 mt-1 text-sm line-clamp-2">
        {article.title}
      </h4>
      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{article.excerpt}</p>
      <span className="text-xs text-gray-400 mt-2 inline-block">
        {article.read_time_minutes} min de lectura
      </span>
    </Link>
  );
}

function LoadingSkeleton() {
  return (
    <div className="animate-pulse space-y-6" aria-busy="true" aria-label="Cargando articulo">
      <div className="h-4 bg-gray-200 rounded w-1/3" />
      <div className="h-8 bg-gray-200 rounded w-2/3" />
      <div className="h-4 bg-gray-200 rounded w-1/4" />
      <div className="space-y-3 mt-8">
        {[1, 2, 3, 4, 5].map((n) => (
          <div key={n} className="h-4 bg-gray-200 rounded" style={{ width: `${90 - n * 5}%` }} />
        ))}
      </div>
    </div>
  );
}

function NotFoundState() {
  return (
    <div className="text-center py-16" role="alert">
      <h2 className="text-xl font-semibold text-gray-900 mb-2">Articulo no encontrado</h2>
      <p className="text-sm text-gray-500 mb-6">
        El articulo que buscas no existe o fue removido.
      </p>
      <Link
        href="/educacion"
        className="inline-block bg-orange-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-orange-700 transition-colors min-h-[44px]"
      >
        Volver al Centro Educativo
      </Link>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function ArticleDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [related, setRelated] = useState<RelatedArticle[]>([]);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);

  const fetchArticle = useCallback(async () => {
    setLoading(true);
    setNotFound(false);

    try {
      const res = await fetch(`${API_BASE_URL}/api/articles/public/${slug}`);
      if (res.ok) {
        const data = await res.json();
        setArticle(data);

        // Fetch related
        const relRes = await fetch(
          `${API_BASE_URL}/api/articles/public?category=${data.category}&limit=${MAX_RELATED_ARTICLES}`
        );
        if (relRes.ok) {
          const relData = await relRes.json();
          setRelated(
            (relData.articles ?? [])
              .filter((a: RelatedArticle) => a.id !== data.id)
              .slice(0, MAX_RELATED_ARTICLES)
          );
        }
      } else if (res.status === 404) {
        // Try sample data
        const sample = SAMPLE_ARTICLES[slug];
        if (sample) {
          setArticle(sample);
          setRelated(SAMPLE_RELATED.slice(0, MAX_RELATED_ARTICLES));
        } else {
          setNotFound(true);
        }
      }
    } catch {
      // Fallback to sample
      const sample = SAMPLE_ARTICLES[slug];
      if (sample) {
        setArticle(sample);
        setRelated(SAMPLE_RELATED.slice(0, MAX_RELATED_ARTICLES));
      } else {
        setNotFound(true);
      }
    } finally {
      setLoading(false);
    }
  }, [slug]);

  useEffect(() => {
    if (slug) fetchArticle();
  }, [slug, fetchArticle]);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-3xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {loading && <LoadingSkeleton />}
        {notFound && <NotFoundState />}

        {article && (
          <>
            <Breadcrumb title={article.title} />
            <article>
              <ArticleHeader article={article} />
              <ArticleContent content={article.content} />
              <ShareButtons title={article.title} slug={article.slug} />
            </article>

            {related.length > 0 && (
              <section className="mt-12" aria-label="Articulos relacionados">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  Articulos relacionados
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" role="list">
                  {related.map((rel) => (
                    <div key={rel.id} role="listitem">
                      <RelatedArticleCard article={rel} />
                    </div>
                  ))}
                </div>
              </section>
            )}

            <div className="mt-8 text-center">
              <Link
                href="/educacion"
                className="text-orange-600 hover:text-orange-700 font-medium text-sm min-h-[44px] inline-flex items-center"
              >
                ← Volver al Centro Educativo
              </Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
