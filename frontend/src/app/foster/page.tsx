import type { Metadata } from "next";
import DynamicIcon from "@/components/DynamicIcon";
import { Phone } from "lucide-react";
import { FOSTER, SITE_TITLE } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${FOSTER.title} | ${SITE_TITLE}`,
  description: FOSTER.metaDescription,
};

export default function FosterPage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-purple-50 to-primary-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {FOSTER.heroTitle}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {FOSTER.heroSubtitle}
          </p>
        </div>
      </section>

      {/* How it Works */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {FOSTER.howItWorksTitle}
          </h2>
          <div className="space-y-6">
            {FOSTER.howItWorksSteps.map((step) => (
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

      {/* Requirements */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {FOSTER.requirementsTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {FOSTER.requirements.map((req) => (
              <div
                key={req.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 text-center"
              >
                <div className="mb-3 text-primary-600"><DynamicIcon name={req.icon} className="h-8 w-8" /></div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {req.title}
                </h3>
                <p className="text-sm text-gray-500">{req.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-6 bg-primary-50 rounded-lg p-4 text-center">
            <p className="text-sm text-primary-800 font-medium">
              {FOSTER.shelterProvides}
            </p>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {FOSTER.faqTitle}
          </h2>
          <div className="space-y-4">
            {FOSTER.faqs.map((faq) => (
              <div
                key={faq.question}
                className="bg-gray-50 rounded-xl p-5 border border-gray-100"
              >
                <h3 className="font-semibold text-gray-900 mb-2">
                  {faq.question}
                </h3>
                <p className="text-sm text-gray-600">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            {FOSTER.ctaTitle}
          </h2>
          <p className="text-gray-600 mb-6">{FOSTER.ctaSubtitle}</p>
          <a
            href={`https://wa.me/${FOSTER.whatsappNumber.replace(/\s/g, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors"
          >
            <Phone className="h-5 w-5" /> WhatsApp: {FOSTER.whatsappNumber}
          </a>
        </div>
      </section>
    </div>
  );
}
