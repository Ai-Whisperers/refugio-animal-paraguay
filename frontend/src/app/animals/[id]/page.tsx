"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import Link from "next/link";
import { X, ChevronLeft, ChevronRight, MessageCircle, ArrowLeft, ClipboardCheck, Heart } from "lucide-react";
import type { Animal } from "@/types/api";
import { getAnimalPublic } from "@/lib/public-api";
import { STATUS_LABELS, statusBadgeClass, calculateAge } from "@/lib/animal-utils";
import { ANIMAL_DETAIL, COMMON, SPECIES_LABELS, formatDate } from "@/lib/strings";
import AnimalPlaceholder from "@/components/AnimalPlaceholder";
import WhatsAppShareButton from "@/components/WhatsAppShareButton";
import ShareWidget from "@/components/ShareWidget";

const WHATSAPP_BASE = "https://wa.me/595981000000";

export default function AnimalDetailPage() {
  const params = useParams<{ id: string }>();
  const [animal, setAnimal] = useState<Animal | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mainPhotoIndex, setMainPhotoIndex] = useState(0);
  const [lightboxOpen, setLightboxOpen] = useState(false);
  const [lightboxIndex, setLightboxIndex] = useState(0);
  const ctaRef = useRef<HTMLDivElement>(null);
  const [showStickyBar, setShowStickyBar] = useState(true);

  useEffect(() => {
    if (!params.id) return;

    async function fetchAnimal() {
      setIsLoading(true);
      setError(null);
      try {
        const data = await getAnimalPublic(params.id);
        setAnimal(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : COMMON.error);
      } finally {
        setIsLoading(false);
      }
    }

    fetchAnimal();
  }, [params.id]);

  // Hide sticky bar when actual CTA is visible
  useEffect(() => {
    if (!ctaRef.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => setShowStickyBar(!entry.isIntersecting),
      { threshold: 0.5 }
    );
    observer.observe(ctaRef.current);
    return () => observer.disconnect();
  }, [animal]);

  const allPhotos = animal
    ? [
        ...(animal.primary_photo_url ? [{ url: animal.primary_photo_url, caption: animal.name }] : []),
        ...animal.photos.map((p) => ({ url: p.url, caption: p.caption ?? animal.name })),
      ]
    : [];

  const openLightbox = useCallback((index: number) => {
    setLightboxIndex(index);
    setLightboxOpen(true);
  }, []);

  const closeLightbox = useCallback(() => setLightboxOpen(false), []);

  const lightboxPrev = useCallback(() => {
    setLightboxIndex((i) => (i > 0 ? i - 1 : allPhotos.length - 1));
  }, [allPhotos.length]);

  const lightboxNext = useCallback(() => {
    setLightboxIndex((i) => (i < allPhotos.length - 1 ? i + 1 : 0));
  }, [allPhotos.length]);

  // Keyboard navigation for lightbox
  useEffect(() => {
    if (!lightboxOpen) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") closeLightbox();
      if (e.key === "ArrowLeft") lightboxPrev();
      if (e.key === "ArrowRight") lightboxNext();
    }
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [lightboxOpen, closeLightbox, lightboxPrev, lightboxNext]);

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-[#E8622A] border-r-transparent" />
        <p className="mt-3 text-gray-500">{ANIMAL_DETAIL.loading}</p>
      </div>
    );
  }

  if (error || !animal) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-orange-50 mb-4">
          <ArrowLeft className="h-8 w-8 text-[#E8622A]" />
        </div>
        <p className="text-red-600 mb-4">{error ?? ANIMAL_DETAIL.notFound}</p>
        <Link href="/animals" className="text-[#E8622A] hover:underline font-medium">
          {ANIMAL_DETAIL.backToAnimals}
        </Link>
      </div>
    );
  }

  const isAvailable = animal.status === "available";
  const whatsappMessage = encodeURIComponent(`Hola! Me interesa adoptar a ${animal.name}. Vi su perfil en Refugio Animal Paraguay.`);
  const whatsappUrl = `${WHATSAPP_BASE}?text=${whatsappMessage}`;

  return (
    <>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 pb-24 md:pb-10">
        {/* Breadcrumb */}
        <nav className="mb-6 text-sm text-gray-500">
          <Link href="/animals" className="hover:text-[#E8622A] transition-colors">
            {ANIMAL_DETAIL.breadcrumbAnimals}
          </Link>
          <span className="mx-2">/</span>
          <span className="text-gray-900">{animal.name}</span>
        </nav>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          {/* Photo Section */}
          <div className="relative">
            {allPhotos.length > 0 ? (
              <button
                onClick={() => openLightbox(mainPhotoIndex)}
                className="w-full cursor-zoom-in"
                aria-label={ANIMAL_DETAIL.openGallery}
              >
                <Image
                  src={allPhotos[mainPhotoIndex].url}
                  alt={allPhotos[mainPhotoIndex].caption}
                  width={800}
                  height={500}
                  className="w-full h-64 md:h-96 object-cover"
                  sizes="(max-width: 768px) 100vw, 800px"
                  priority
                />
              </button>
            ) : (
              <AnimalPlaceholder
                species={animal.species}
                className="w-full h-64 md:h-96 bg-gradient-to-br from-orange-50 to-orange-100 flex items-center justify-center"
              />
            )}
            {/* Status badge */}
            <span
              className={`absolute top-4 right-4 text-sm px-3 py-1 rounded-full font-medium shadow-sm ${statusBadgeClass(animal.status)}`}
            >
              {STATUS_LABELS[animal.status]}
            </span>
          </div>

          {/* Thumbnail Strip */}
          {allPhotos.length > 1 && (
            <div className="flex gap-2 px-4 py-3 bg-gray-50 overflow-x-auto scroll-smooth snap-x snap-mandatory">
              {allPhotos.map((photo, i) => (
                <button
                  key={i}
                  onClick={() => setMainPhotoIndex(i)}
                  className={`flex-shrink-0 snap-start rounded-lg overflow-hidden border-2 transition-all ${
                    i === mainPhotoIndex
                      ? "border-[#E8622A] ring-2 ring-[#E8622A]/30"
                      : "border-transparent hover:border-gray-300"
                  }`}
                >
                  <Image
                    src={photo.url}
                    alt={photo.caption}
                    width={80}
                    height={80}
                    className="w-20 h-20 object-cover"
                    sizes="80px"
                  />
                </button>
              ))}
            </div>
          )}

          {/* Info Section */}
          <div className="p-6 md:p-8">
            <div className="flex items-center gap-3 mb-4">
              <h1 className="text-3xl font-bold text-gray-900">
                {animal.name}
              </h1>
              <WhatsAppShareButton
                animalName={animal.name}
                species={animal.species}
                birthDate={animal.birth_date}
                animalId={animal.id}
                size="md"
              />
              <ShareWidget
                title={`${animal.name} busca hogar — Refugio Animal Paraguay`}
                description={animal.description ?? undefined}
                url={typeof window !== "undefined" ? window.location.href : undefined}
              />
            </div>

            {/* Details Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <DetailItem label={ANIMAL_DETAIL.species} value={SPECIES_LABELS[animal.species] ?? animal.species} />
              {animal.birth_date && (
                <DetailItem label={ANIMAL_DETAIL.age} value={calculateAge(animal.birth_date)} />
              )}
              <DetailItem
                label={ANIMAL_DETAIL.arrived}
                value={formatDate(animal.created_at)}
              />
            </div>

            {/* Description */}
            {animal.description && (
              <div className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 mb-2">
                  {ANIMAL_DETAIL.about(animal.name)}
                </h2>
                <p className="text-gray-600 leading-relaxed whitespace-pre-line">
                  {animal.description}
                </p>
              </div>
            )}

            {/* Action Buttons */}
            <div ref={ctaRef} className="flex flex-col sm:flex-row gap-3">
              {isAvailable ? (
                <>
                  <Link
                    href={`/animals/${animal.id}/apply`}
                    className="inline-flex items-center justify-center bg-[#E8622A] text-white px-6 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors"
                  >
                    {ANIMAL_DETAIL.applyToAdopt(animal.name)}
                  </Link>
                  <Link
                    href={`/animals/${animal.id}/pre-qualify`}
                    className="inline-flex items-center justify-center gap-2 bg-white text-[#E8622A] border border-[#E8622A] px-6 py-3 rounded-lg font-medium hover:bg-orange-50 transition-colors"
                  >
                    <ClipboardCheck className="h-4 w-4" />
                    {ANIMAL_DETAIL.preQualify}
                  </Link>
                </>
              ) : (
                <div className="px-6 py-3 bg-gray-100 text-gray-500 rounded-lg text-center font-medium">
                  {ANIMAL_DETAIL.notAvailable}
                </div>
              )}
              <a
                href={whatsappUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center gap-2 bg-[#25D366] text-white px-6 py-3 rounded-lg font-medium hover:bg-[#1fb855] transition-colors"
              >
                <MessageCircle className="h-5 w-5" />
                {ANIMAL_DETAIL.askAbout(animal.name)}
              </a>
              <Link
                href={`/animals/${animal.id}/sponsor`}
                className="inline-flex items-center justify-center gap-2 bg-pink-500 text-white px-6 py-3 rounded-lg font-medium hover:bg-pink-600 transition-colors"
              >
                <Heart className="h-5 w-5" />
                {ANIMAL_DETAIL.sponsorAnimal(animal.name)}
              </Link>
              <Link
                href="/animals"
                className="inline-flex items-center justify-center bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
              >
                {ANIMAL_DETAIL.backToAnimals}
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Sticky Bottom CTA (mobile) */}
      {isAvailable && showStickyBar && (
        <div className="fixed bottom-0 inset-x-0 p-4 bg-white/95 backdrop-blur-sm border-t shadow-lg z-20 md:hidden">
          <div className="flex gap-3 max-w-4xl mx-auto">
            <Link
              href={`/animals/${animal.id}/apply`}
              className="flex-1 inline-flex items-center justify-center bg-[#E8622A] text-white px-4 py-3 rounded-lg font-semibold hover:bg-[#d4571f] transition-colors text-sm"
            >
              {ANIMAL_DETAIL.wantToAdopt(animal.name)}
            </Link>
            <a
              href={whatsappUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center bg-[#25D366] text-white px-4 py-3 rounded-lg hover:bg-[#1fb855] transition-colors"
              aria-label={ANIMAL_DETAIL.askAbout(animal.name)}
            >
              <MessageCircle className="h-5 w-5" />
            </a>
          </div>
        </div>
      )}

      {/* Lightbox Modal */}
      {lightboxOpen && allPhotos.length > 0 && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={closeLightbox}
          role="dialog"
          aria-modal="true"
          aria-label={ANIMAL_DETAIL.photoGallery}
        >
          <button
            onClick={closeLightbox}
            className="absolute top-4 right-4 text-white/80 hover:text-white z-10"
            aria-label={ANIMAL_DETAIL.closeGallery}
          >
            <X className="h-8 w-8" />
          </button>

          {allPhotos.length > 1 && (
            <>
              <button
                onClick={(e) => { e.stopPropagation(); lightboxPrev(); }}
                className="absolute left-4 text-white/80 hover:text-white z-10"
                aria-label={ANIMAL_DETAIL.previousPhoto}
              >
                <ChevronLeft className="h-10 w-10" />
              </button>
              <button
                onClick={(e) => { e.stopPropagation(); lightboxNext(); }}
                className="absolute right-4 text-white/80 hover:text-white z-10"
                aria-label={ANIMAL_DETAIL.nextPhoto}
              >
                <ChevronRight className="h-10 w-10" />
              </button>
            </>
          )}

          <div
            className="max-w-5xl max-h-[90vh] px-12"
            onClick={(e) => e.stopPropagation()}
          >
            <Image
              src={allPhotos[lightboxIndex].url}
              alt={allPhotos[lightboxIndex].caption}
              width={1200}
              height={800}
              className="max-h-[85vh] w-auto object-contain mx-auto"
              sizes="90vw"
            />
            <p className="text-white/70 text-center mt-2 text-sm">
              {lightboxIndex + 1} / {allPhotos.length}
            </p>
          </div>
        </div>
      )}
    </>
  );
}

function DetailItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs text-gray-400 uppercase tracking-wider">{label}</p>
      <p className="text-gray-900 font-medium">{value}</p>
    </div>
  );
}
