import type { Metadata } from "next";
import { SITE_TITLE } from "@/lib/strings";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const BASE_URL =
  process.env.NEXT_PUBLIC_BASE_URL ?? "https://refugioanimal.com.py";

interface AnimalLayoutProps {
  params: Promise<{ id: string }>;
  children: React.ReactNode;
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const fallbackTitle = `Animal | ${SITE_TITLE}`;
  const fallbackDescription =
    "Conoce a este animal que busca un hogar para siempre";

  try {
    const res = await fetch(`${API_BASE_URL}/public/animals/${id}`, {
      next: { revalidate: 300 },
    });
    if (!res.ok) {
      return { title: fallbackTitle, description: fallbackDescription };
    }
    const animal = await res.json();
    const title = `${animal.name} busca hogar | ${SITE_TITLE}`;
    const description =
      animal.description ?? `${animal.name} esta disponible para adopcion`;
    const ogImageUrl = animal.primary_photo_url ?? undefined;

    return {
      title,
      description,
      openGraph: {
        title,
        description,
        url: `${BASE_URL}/animals/${id}`,
        images: ogImageUrl
          ? [{ url: ogImageUrl, width: 1200, height: 630 }]
          : undefined,
      },
      twitter: {
        card: "summary_large_image",
        title,
        description,
        images: ogImageUrl ? [ogImageUrl] : undefined,
      },
    };
  } catch {
    return { title: fallbackTitle, description: fallbackDescription };
  }
}

export default async function AnimalDetailLayout({
  children,
}: AnimalLayoutProps) {
  return <>{children}</>;
}
