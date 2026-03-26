import type { Metadata } from "next";
import Link from "next/link";
import { DONATE, SITE_TITLE } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${DONATE.title} | ${SITE_TITLE}`,
  description: DONATE.metaDescription,
};

export default function DonatePage() {
  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-secondary-50 to-green-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {DONATE.heroTitle}
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 max-w-2xl mx-auto leading-relaxed">
            {DONATE.heroSubtitle}
          </p>
        </div>
      </section>

      {/* How Donations Help */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {DONATE.howHelpsTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {DONATE.howHelps.map((item) => (
              <div
                key={item.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
              >
                <div className="text-3xl mb-3">{item.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-gray-500 mb-3">
                  {item.description}
                </p>
                <p className="text-sm font-medium text-primary-600">
                  {item.amount}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Donation Options */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {DONATE.donateOptionsTitle}
          </h2>

          {/* Bank Transfer (Paraguay) */}
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
              <span>{"\u{1F3E6}"}</span> {DONATE.bankTransferTitle}
            </h3>
            <div className="space-y-2">
              {DONATE.bankDetails.map((detail) => (
                <div key={detail.label} className="flex gap-2 text-sm">
                  <span className="font-medium text-gray-700 min-w-[80px]">
                    {detail.label}:
                  </span>
                  <span className="text-gray-600">{detail.value}</span>
                </div>
              ))}
            </div>
            <p className="mt-4 text-sm text-gray-500 bg-gray-50 rounded-lg p-3">
              {DONATE.bankNote}
            </p>
          </div>

          {/* EU Donors */}
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span>{"\u{1F1EA}\u{1F1FA}"}</span> {DONATE.euTitle}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              {DONATE.euDescription}
            </p>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4">
              <p className="text-sm text-blue-700">{DONATE.euComingSoon}</p>
            </div>
          </div>
        </div>
      </section>

      {/* Other Ways to Help */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-8 text-center">
            {DONATE.otherWaysTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {DONATE.otherWays.map((item) => (
              <div
                key={item.title}
                className="bg-white rounded-xl p-6 shadow-sm border border-gray-100"
              >
                <div className="text-3xl mb-3">{item.icon}</div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {item.title}
                </h3>
                <p className="text-sm text-gray-500">{item.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Transparency */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-3xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-4">
            {DONATE.transparencyTitle}
          </h2>
          <p className="text-gray-600 leading-relaxed">
            {DONATE.transparencyText}
          </p>
        </div>
      </section>

      {/* WhatsApp CTA */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto text-center">
          <p className="text-2xl mb-3">{"\u{1F4AC}"}</p>
          <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
            {DONATE.whatsappCta}
          </h2>
          <a
            href={`https://wa.me/${DONATE.whatsappNumber.replace(/\s/g, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors mt-3"
          >
            {"\u{1F4F1}"} WhatsApp: {DONATE.whatsappNumber}
          </a>
          <div className="mt-6">
            <Link
              href="/animals"
              className="text-primary-600 hover:text-primary-700 font-medium"
            >
              {"\u{2190}"} Ver animales disponibles
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
