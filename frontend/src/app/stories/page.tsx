import type { Metadata } from "next";
import Link from "next/link";
import { Heart, Calendar, Quote } from "lucide-react";
import { SUCCESS_STORIES, SITE_TITLE } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${SUCCESS_STORIES.title} | ${SITE_TITLE}`,
  description: SUCCESS_STORIES.metaDescription,
};

export default function SuccessStoriesPage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {SUCCESS_STORIES.heroTitle}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {SUCCESS_STORIES.heroSubtitle}
          </p>
        </div>
      </section>

      {/* Stories Grid */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 sm:mb-12 text-center">
            {SUCCESS_STORIES.storiesTitle}
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            {SUCCESS_STORIES.stories.map((story) => (
              <article
                key={story.animal}
                className="bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow overflow-hidden"
              >
                {/* Story Header */}
                <div className="bg-gradient-to-r from-primary-50 to-orange-50 px-6 py-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-900">
                        {story.animal}
                      </h3>
                      <p className="text-sm text-gray-600">{story.species}</p>
                    </div>
                    <div className="flex items-center gap-1.5 text-sm text-gray-500">
                      <Calendar className="w-4 h-4" aria-hidden="true" />
                      <span>{story.date}</span>
                    </div>
                  </div>
                </div>

                {/* Story Body */}
                <div className="px-6 py-5 space-y-4">
                  <p className="text-gray-600 leading-relaxed text-sm sm:text-base">
                    {story.summary}
                  </p>

                  {/* Quote */}
                  <blockquote className="border-l-4 border-primary-300 pl-4 py-2 bg-gray-50 rounded-r-lg">
                    <div className="flex gap-2">
                      <Quote
                        className="w-5 h-5 text-primary-400 flex-shrink-0 mt-0.5"
                        aria-hidden="true"
                      />
                      <div>
                        <p className="text-gray-700 italic text-sm leading-relaxed">
                          &quot;{story.quote}&quot;
                        </p>
                        <p className="text-sm font-medium text-gray-900 mt-2">
                          — {story.adopter}
                        </p>
                      </div>
                    </div>
                  </blockquote>
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Impact Stats */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {SUCCESS_STORIES.impactTitle}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-8">
            {SUCCESS_STORIES.impactStats.map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-2xl sm:text-4xl font-bold text-primary-600">
                  {stat.value}
                </p>
                <p className="text-gray-500 mt-1 text-xs sm:text-base">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Share Your Story */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-2xl mx-auto text-center">
          <div className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 sm:p-8">
            <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center mx-auto mb-4">
              <Heart className="w-6 h-6 text-primary-600" aria-hidden="true" />
            </div>
            <h2 className="text-2xl font-heading font-bold text-gray-900 mb-3">
              {SUCCESS_STORIES.shareTitle}
            </h2>
            <p className="text-gray-600 mb-6 leading-relaxed">
              {SUCCESS_STORIES.shareText}
            </p>
            <a
              href={`https://wa.me/${SUCCESS_STORIES.whatsappNumber.replace(/\s+/g, "")}`}
              className="inline-flex items-center justify-center bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
            >
              Escribinos por WhatsApp
            </a>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-primary-600 to-orange-600 py-12 sm:py-16 px-4">
        <div className="max-w-2xl mx-auto text-center text-white">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold mb-3">
            {SUCCESS_STORIES.ctaTitle}
          </h2>
          <p className="text-lg sm:text-xl mb-8 leading-relaxed opacity-90">
            {SUCCESS_STORIES.ctaSubtitle}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/animals"
              className="inline-flex items-center justify-center bg-white text-primary-600 px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              {SUCCESS_STORIES.ctaAdopt}
            </Link>
            <Link
              href="/donate"
              className="inline-flex items-center justify-center bg-secondary-500 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-secondary-600 transition-colors"
            >
              {SUCCESS_STORIES.ctaDonate}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
