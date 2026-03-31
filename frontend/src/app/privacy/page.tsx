"use client";

import { useState } from "react";
import type { Metadata } from "next";
import { PRIVACY, SITE_TITLE } from "@/lib/strings";

// Note: metadata cannot be exported from a "use client" component.
// The page head is handled via the layout or a separate metadata file.

type Lang = "es" | "en";

export default function PrivacyPage() {
  const [lang, setLang] = useState<Lang>("es");
  const isEn = lang === "en";

  const sections = isEn
    ? [
        { title: PRIVACY.section1TitleEn, body: PRIVACY.section1BodyEn },
        { title: PRIVACY.section2TitleEn, body: PRIVACY.section2BodyEn },
        { title: PRIVACY.section3TitleEn, body: PRIVACY.section3BodyEn },
        { title: PRIVACY.section4TitleEn, body: PRIVACY.section4BodyEn },
        { title: PRIVACY.section5TitleEn, body: PRIVACY.section5BodyEn },
        { title: PRIVACY.section6TitleEn, body: PRIVACY.section6BodyEn },
        { title: PRIVACY.section7TitleEn, body: PRIVACY.section7BodyEn },
      ]
    : [
        { title: PRIVACY.section1Title, body: PRIVACY.section1Body },
        { title: PRIVACY.section2Title, body: PRIVACY.section2Body },
        { title: PRIVACY.section3Title, body: PRIVACY.section3Body },
        { title: PRIVACY.section4Title, body: PRIVACY.section4Body },
        { title: PRIVACY.section5Title, body: PRIVACY.section5Body },
        { title: PRIVACY.section6Title, body: PRIVACY.section6Body },
        { title: PRIVACY.section7Title, body: PRIVACY.section7Body },
      ];

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {isEn ? PRIVACY.heroTitleEn : PRIVACY.heroTitle}
          </h1>
          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed mb-6">
            {isEn ? PRIVACY.heroSubtitleEn : PRIVACY.heroSubtitle}
          </p>
          {/* Language toggle */}
          <div className="inline-flex rounded-lg border border-gray-200 bg-white shadow-sm" role="group" aria-label="Language">
            <button
              type="button"
              onClick={() => setLang("es")}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg transition-colors ${
                lang === "es"
                  ? "bg-primary-600 text-white"
                  : "text-gray-600 hover:text-primary-600"
              }`}
            >
              {PRIVACY.langEs}
            </button>
            <button
              type="button"
              onClick={() => setLang("en")}
              className={`px-4 py-2 text-sm font-medium rounded-r-lg transition-colors ${
                lang === "en"
                  ? "bg-primary-600 text-white"
                  : "text-gray-600 hover:text-primary-600"
              }`}
            >
              {PRIVACY.langEn}
            </button>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <p className="text-sm text-gray-400 mb-8">
            {isEn ? PRIVACY.lastUpdatedEn : PRIVACY.lastUpdated}: {PRIVACY.lastUpdatedDate}
          </p>
          <div className="space-y-8">
            {sections.map((section, idx) => (
              <div key={idx}>
                <h2 className="text-xl font-heading font-semibold text-gray-900 mb-3">
                  {section.title}
                </h2>
                <p className="text-gray-600 leading-relaxed">{section.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
