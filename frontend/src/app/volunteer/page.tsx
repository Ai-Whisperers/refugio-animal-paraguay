import type { Metadata } from "next";
import { VOLUNTEER, SITE_TITLE } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${VOLUNTEER.title} | ${SITE_TITLE}`,
  description: VOLUNTEER.metaDescription,
};

export default function VolunteerPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {VOLUNTEER.heroTitle}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {VOLUNTEER.heroSubtitle}
          </p>
        </div>
      </section>

      {/* Activities */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {VOLUNTEER.activitiesTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {VOLUNTEER.activities.map((activity) => (
              <div
                key={activity.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center"
              >
                <div className="text-3xl mb-3">{activity.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {activity.title}
                </h3>
                <p className="text-sm text-gray-500">{activity.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Requirements */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-6 text-center">
            {VOLUNTEER.requirementsTitle}
          </h2>
          <ul className="space-y-3">
            {VOLUNTEER.requirements.map((req) => (
              <li
                key={req}
                className="flex items-start gap-3 bg-white rounded-lg p-4 border border-gray-100"
              >
                <span className="text-primary-600 font-bold mt-0.5">
                  {"\u{2713}"}
                </span>
                <span className="text-gray-700">{req}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* How to Join */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {VOLUNTEER.howToJoinTitle}
          </h2>
          <div className="space-y-6">
            {VOLUNTEER.howToJoinSteps.map((step) => (
              <div key={step.step} className="flex items-start gap-4">
                <div className="w-10 h-10 rounded-full bg-primary-600 text-white flex items-center justify-center font-bold flex-shrink-0">
                  {step.step}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{step.title}</h3>
                  <p className="text-sm text-gray-500 mt-1">
                    {step.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {VOLUNTEER.testimonialTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {VOLUNTEER.testimonials.map((t) => (
              <div
                key={t.name}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
              >
                <p className="text-gray-600 italic mb-4">
                  &ldquo;{t.quote}&rdquo;
                </p>
                <p className="font-semibold text-gray-900 text-sm">
                  {t.name}
                </p>
                <p className="text-xs text-gray-500">{t.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-heading font-bold text-gray-900 mb-4">
            {VOLUNTEER.ctaTitle}
          </h2>
          <a
            href={`https://wa.me/${VOLUNTEER.whatsappNumber.replace(/\s/g, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
          >
            {"\u{1F4F1}"} WhatsApp: {VOLUNTEER.whatsappNumber}
          </a>
        </div>
      </section>
    </div>
  );
}
