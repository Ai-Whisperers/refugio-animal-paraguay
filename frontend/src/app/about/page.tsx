import type { Metadata } from "next";
import Link from "next/link";
import { ABOUT, SITE_TITLE } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${ABOUT.title} | ${SITE_TITLE}`,
  description: ABOUT.metaDescription,
};

export default function AboutPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {ABOUT.heroTitle}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {ABOUT.heroSubtitle}
          </p>
        </div>
      </section>

      {/* History */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-6 text-center">
            {ABOUT.historyTitle}
          </h2>
          <div className="space-y-4 text-gray-600 leading-relaxed">
            <p>{ABOUT.historyP1}</p>
            <p>{ABOUT.historyP2}</p>
            <p>{ABOUT.historyP3}</p>
          </div>
        </div>
      </section>

      {/* Team */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {ABOUT.teamTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {ABOUT.teamMembers.map((member) => (
              <div
                key={member.name}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-primary-100 flex items-center justify-center text-2xl mx-auto mb-4">
                  {""}
                </div>
                <h3 className="font-semibold text-gray-900">{member.name}</h3>
                <p className="text-sm text-gray-500 mt-1">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Location */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-6 text-center">
            {ABOUT.locationTitle}
          </h2>
          <div className="bg-gray-50 rounded-xl p-6 sm:p-8 border border-gray-100">
            <div className="flex items-start gap-4">
              <span className="text-3xl">{""}</span>
              <div className="space-y-2">
                <p className="font-semibold text-gray-900">
                  {ABOUT.locationAddress}
                </p>
                <p className="text-sm text-gray-600">{ABOUT.locationHours}</p>
                <p className="text-sm text-gray-500">{ABOUT.locationVisit}</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Impact */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {ABOUT.impactTitle}
          </h2>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-8">
            {ABOUT.impactStats.map((stat) => (
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

      {/* CTA */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-3">
            {ABOUT.ctaTitle}
          </h2>
          <p className="text-gray-600 mb-6 max-w-xl mx-auto">
            {ABOUT.ctaSubtitle}
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <Link
              href="/animals"
              className="inline-flex items-center justify-center bg-primary-600 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              {ABOUT.ctaAdopt}
            </Link>
            <Link
              href="/donate"
              className="inline-flex items-center justify-center bg-secondary-600 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-secondary-700 transition-colors"
            >
              {ABOUT.ctaDonate}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
