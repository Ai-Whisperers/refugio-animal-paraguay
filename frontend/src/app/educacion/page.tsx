"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const CATEGORIES = [
  { value: "all", label: "Todos" },
  { value: "cuidado", label: "Cuidado animal" },
  { value: "salud", label: "Salud" },
  { value: "adopcion", label: "Adopcion" },
  { value: "esterilizacion", label: "Esterilizacion" },
  { value: "nutricion", label: "Nutricion" },
  { value: "comportamiento", label: "Comportamiento" },
] as const;

const FEATURED_SECTIONS = [
  {
    title: "Esterilizacion",
    description: "Aprende por que esterilizar es un acto de amor y responsabilidad.",
    href: "/educacion/esterilizacion",
    color: "bg-orange-50 border-orange-200",
    textColor: "text-orange-700",
  },
  {
    title: "Videos educativos",
    description: "Contenido audiovisual sobre cuidado animal responsable.",
    href: "/educacion/videos",
    color: "bg-blue-50 border-blue-200",
    textColor: "text-blue-700",
  },
];

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Article {
  id: string;
  title: string;
  excerpt: string;
  category: string;
  read_time_minutes: number;
  published_at: string;
  featured_image: string | null;
  slug: string;
}

// ---------------------------------------------------------------------------
// Sample Articles (fallback when API unavailable)
// ---------------------------------------------------------------------------

const SAMPLE_ARTICLES: Article[] = [
  {
    id: "art-1",
    title: "Guia completa para adoptar un perro en Paraguay",
    excerpt: "Todo lo que necesitas saber antes de adoptar: preparacion del hogar, primeros dias, y compromisos a largo plazo.",
    category: "adopcion",
    read_time_minutes: 8,
    published_at: "2026-03-15",
    featured_image: null,
    slug: "guia-adoptar-perro-paraguay",
  },
  {
    id: "art-2",
    title: "Vacunacion: calendario esencial para tu mascota",
    excerpt: "Las vacunas que tu perro o gato necesita segun su edad y las recomendaciones veterinarias en Paraguay.",
    category: "salud",
    read_time_minutes: 6,
    published_at: "2026-03-10",
    featured_image: null,
    slug: "calendario-vacunacion-mascotas",
  },
  {
    id: "art-3",
    title: "Alimentacion casera vs comercial: que es mejor?",
    excerpt: "Comparamos las opciones de alimentacion para ayudarte a elegir la mejor nutricion para tu mascota.",
    category: "nutricion",
    read_time_minutes: 10,
    published_at: "2026-03-05",
    featured_image: null,
    slug: "alimentacion-casera-vs-comercial",
  },
  {
    id: "art-4",
    title: "Señales de estres en gatos: como identificarlas",
    excerpt: "Aprende a reconocer cuando tu gato esta estresado y que puedes hacer para ayudarlo.",
    category: "comportamiento",
    read_time_minutes: 5,
    published_at: "2026-02-28",
    featured_image: null,
    slug: "senales-estres-gatos",
  },
  {
    id: "art-5",
    title: "Primeros auxilios para mascotas",
    excerpt: "Que hacer en caso de emergencia antes de llegar al veterinario. Guia practica y rapida.",
    category: "salud",
    read_time_minutes: 7,
    published_at: "2026-02-20",
    featured_image: null,
    slug: "primeros-auxilios-mascotas",
  },
  {
    id: "art-6",
    title: "Cuidados basicos del cachorro recien adoptado",
    excerpt: "Los primeros 30 dias son cruciales. Sigue esta guia para darle la mejor bienvenida.",
    category: "cuidado",
    read_time_minutes: 9,
    published_at: "2026-02-15",
    featured_image: null,
    slug: "cuidados-cachorro-adoptado",
  },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function CategoryFilter({
  active,
  onChange,
}: {
  active: string;
  onChange: (cat: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-2" role="group" aria-label="Filtrar por categoria">
      {CATEGORIES.map((cat) => (
        <button
          key={cat.value}
          onClick={() => onChange(cat.value)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors min-h-[44px] ${
            active === cat.value
              ? "bg-orange-600 text-white"
              : "bg-white text-gray-600 border border-gray-200 hover:bg-gray-50"
          }`}
          aria-pressed={active === cat.value}
        >
          {cat.label}
        </button>
      ))}
    </div>
  );
}

function SearchBar({
  value,
  onChange,
}: {
  value: string;
  onChange: (val: string) => void;
}) {
  return (
    <div className="relative">
      <input
        type="search"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Buscar articulos..."
        className="w-full border border-gray-200 rounded-xl px-4 py-3 pl-10 text-sm focus:ring-2 focus:ring-orange-500 focus:border-orange-500 bg-white"
        aria-label="Buscar articulos educativos"
      />
      <svg
        className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        aria-hidden="true"
      >
        <circle cx="11" cy="11" r="8" />
        <path d="M21 21l-4.35-4.35" />
      </svg>
    </div>
  );
}

function ArticleCard({ article }: { article: Article }) {
  const categoryLabel = CATEGORIES.find((c) => c.value === article.category)?.label ?? article.category;

  return (
    <article className="bg-white rounded-xl border border-gray-200 shadow-sm hover:shadow-md transition-shadow overflow-hidden">
      {article.featured_image && (
        <div className="h-40 bg-gray-100">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={article.featured_image}
            alt={article.title}
            className="w-full h-full object-cover"
            loading="lazy"
          />
        </div>
      )}
      <div className="p-5">
        <div className="flex items-center gap-2 mb-2">
          <span className="text-xs font-medium text-orange-600 bg-orange-50 px-2 py-0.5 rounded-full">
            {categoryLabel}
          </span>
          <span className="text-xs text-gray-400">
            {article.read_time_minutes} min de lectura
          </span>
        </div>
        <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">
          <Link
            href={`/educacion/articulos/${article.slug}`}
            className="hover:text-orange-600 transition-colors"
          >
            {article.title}
          </Link>
        </h3>
        <p className="text-sm text-gray-600 line-clamp-3">{article.excerpt}</p>
        <div className="mt-3 flex items-center justify-between">
          <time
            className="text-xs text-gray-400"
            dateTime={article.published_at}
          >
            {new Date(article.published_at).toLocaleDateString("es-PY", {
              year: "numeric",
              month: "long",
              day: "numeric",
            })}
          </time>
          <Link
            href={`/educacion/articulos/${article.slug}`}
            className="text-sm text-orange-600 font-medium hover:text-orange-700 min-h-[44px] flex items-center"
            aria-label={`Leer articulo: ${article.title}`}
          >
            Leer mas
          </Link>
        </div>
      </div>
    </article>
  );
}

function FeaturedSectionCard({
  section,
}: {
  section: (typeof FEATURED_SECTIONS)[number];
}) {
  return (
    <Link
      href={section.href}
      className={`block rounded-xl border p-6 ${section.color} hover:shadow-md transition-shadow min-h-[44px]`}
    >
      <h3 className={`font-semibold text-lg ${section.textColor}`}>
        {section.title}
      </h3>
      <p className="text-sm text-gray-600 mt-1">{section.description}</p>
      <span className={`text-sm font-medium ${section.textColor} mt-3 inline-block`}>
        Explorar →
      </span>
    </Link>
  );
}

function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse" aria-busy="true" aria-label="Cargando articulos">
      {[1, 2, 3, 4, 5, 6].map((n) => (
        <div key={n} className="bg-gray-200 rounded-xl h-64" />
      ))}
    </div>
  );
}

function EmptyState({ searchTerm, category }: { searchTerm: string; category: string }) {
  return (
    <div className="text-center py-12">
      <p className="text-gray-500 text-lg mb-2">No se encontraron articulos</p>
      <p className="text-gray-400 text-sm">
        {searchTerm
          ? `No hay resultados para "${searchTerm}"`
          : category !== "all"
            ? "No hay articulos en esta categoria todavia."
            : "Pronto agregaremos contenido educativo."}
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function EducationHubPage() {
  const [articles, setArticles] = useState<Article[]>(SAMPLE_ARTICLES);
  const [loading, setLoading] = useState(false);
  const [category, setCategory] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");

  const fetchArticles = useCallback(async () => {
    try {
      setLoading(true);
      const res = await fetch(`${API_BASE_URL}/api/articles/public`);
      if (res.ok) {
        const data = await res.json();
        if (data.articles && data.articles.length > 0) {
          setArticles(data.articles);
        }
      }
    } catch {
      // Use sample articles as fallback
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchArticles();
  }, [fetchArticles]);

  const filtered = articles.filter((article) => {
    const matchesCategory = category === "all" || article.category === category;
    const matchesSearch =
      searchTerm === "" ||
      article.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      article.excerpt.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-6xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <header className="mb-8">
          <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
            Centro Educativo
          </h1>
          <p className="text-sm text-gray-500 mt-2 max-w-2xl">
            Recursos y articulos sobre cuidado animal responsable, adopcion, salud,
            nutricion y mas. Aprende a ser el mejor dueño para tu mascota.
          </p>
        </header>

        {/* Featured sections */}
        <section className="mb-10" aria-label="Secciones destacadas">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {FEATURED_SECTIONS.map((section) => (
              <FeaturedSectionCard key={section.href} section={section} />
            ))}
          </div>
        </section>

        {/* Search and filter */}
        <div className="mb-6 space-y-4">
          <SearchBar value={searchTerm} onChange={setSearchTerm} />
          <CategoryFilter active={category} onChange={setCategory} />
        </div>

        {/* Article count */}
        <p className="text-sm text-gray-400 mb-4">
          {filtered.length} articulo{filtered.length !== 1 ? "s" : ""} encontrado{filtered.length !== 1 ? "s" : ""}
        </p>

        {/* Articles grid */}
        {loading && articles.length === 0 && <LoadingSkeleton />}

        {!loading && filtered.length === 0 && (
          <EmptyState searchTerm={searchTerm} category={category} />
        )}

        {filtered.length > 0 && (
          <div
            className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
            role="list"
            aria-label="Lista de articulos educativos"
          >
            {filtered.map((article) => (
              <div key={article.id} role="listitem">
                <ArticleCard article={article} />
              </div>
            ))}
          </div>
        )}

        {/* Newsletter CTA */}
        <section className="mt-16 bg-white rounded-2xl shadow-sm border border-gray-200 p-8 text-center" aria-label="Suscripcion">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">
            Mantente informado
          </h2>
          <p className="text-sm text-gray-600 max-w-md mx-auto mb-4">
            Siguenos en redes sociales para recibir nuevos articulos y consejos
            sobre cuidado animal.
          </p>
          <a
            href="/contacto"
            className="inline-block bg-orange-600 text-white px-6 py-3 rounded-xl font-medium hover:bg-orange-700 transition-colors min-h-[44px] min-w-[44px]"
          >
            Contactanos
          </a>
        </section>
      </div>
    </div>
  );
}
