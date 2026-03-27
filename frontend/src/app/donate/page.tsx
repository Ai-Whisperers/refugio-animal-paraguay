import type { Metadata } from "next";
import Link from "next/link";
import DynamicIcon from "@/components/DynamicIcon";
import { Building2, MessageCircle, Phone, ArrowLeft } from "lucide-react";
import { DONATE, SITE_TITLE } from "@/lib/strings";
import CampaignListSection from "./CampaignListSection";
import FeaturedCampaignBanner from "@/components/campaigns/FeaturedCampaignBanner";

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

      {/* Featured Campaign */}
      <section className="py-8 sm:py-12 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <FeaturedCampaignBanner />
        </div>
      </section>

      {/* Active Campaigns */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-gray-900 mb-2 text-center">
            {DONATE.campaignsTitle}
          </h2>
          <p className="text-gray-500 text-center mb-8">
            {DONATE.campaignsSubtitle}
          </p>
          <CampaignListSection />
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
                <div className="mb-3 text-primary-600"><DynamicIcon name={item.icon} className="h-8 w-8" /></div>
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
              <Building2 className="h-5 w-5 text-primary-600" /> {DONATE.bankTransferTitle}
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

          {/* EU Donors — SEPA Direct Debit */}
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <span className="inline-flex items-center justify-center w-6 h-6 bg-blue-100 text-blue-700 font-bold text-sm rounded">EU</span> {DONATE.euTitle}
            </h3>
            <p className="text-sm text-gray-600 mb-3">
              {DONATE.euDescription}
            </p>
            <div className="bg-blue-50 border border-blue-100 rounded-lg p-4 mb-4">
              <p className="text-sm text-blue-700 mb-3">
                Los donantes europeos pueden guardar su cuenta bancaria (IBAN)
                para donaciones recurrentes via Débito Directo SEPA. Es gratis,
                seguro y procesado a través de Stripe.
              </p>
              <Link
                href="/donate/sepa-setup"
                className="inline-block bg-blue-600 text-white text-sm font-medium px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
              >
                Configurar Débito SEPA
              </Link>
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
                <div className="mb-3 text-primary-600"><DynamicIcon name={item.icon} className="h-8 w-8" /></div>
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
          <div className="inline-flex items-center justify-center mb-3"><MessageCircle className="h-8 w-8 text-gray-900" /></div>
          <h2 className="text-xl font-heading font-bold text-gray-900 mb-2">
            {DONATE.whatsappCta}
          </h2>
          <a
            href={`https://wa.me/${DONATE.whatsappNumber.replace(/\s/g, "")}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-green-700 transition-colors mt-3"
          >
            <Phone className="h-5 w-5" /> WhatsApp: {DONATE.whatsappNumber}
          </a>
          <div className="mt-6">
            <Link
              href="/animals"
              className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1"
            >
              <ArrowLeft className="h-4 w-4" /> Ver animales disponibles
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
