"use client";

import { useState } from "react";
import { TERMS } from "@/lib/strings";

type Lang = "es" | "en";

export default function TermsPage() {
  const [lang, setLang] = useState<Lang>("es");
  const isEn = lang === "en";

  const sections = isEn
    ? [
        { title: TERMS.section1TitleEn, body: TERMS.section1BodyEn },
        { title: TERMS.section2TitleEn, body: TERMS.section2BodyEn },
        { title: TERMS.section3TitleEn, body: TERMS.section3BodyEn },
        { title: TERMS.section4TitleEn, body: TERMS.section4BodyEn },
        { title: TERMS.section5TitleEn, body: TERMS.section5BodyEn },
        { title: TERMS.section6TitleEn, body: TERMS.section6BodyEn },
        { title: TERMS.section7TitleEn, body: TERMS.section7BodyEn },
        { title: TERMS.section8TitleEn, body: TERMS.section8BodyEn },
      ]
    : [
        { title: TERMS.section1Title, body: TERMS.section1Body },
        { title: TERMS.section2Title, body: TERMS.section2Body },
        { title: TERMS.section3Title, body: TERMS.section3Body },
        { title: TERMS.section4Title, body: TERMS.section4Body },
        { title: TERMS.section5Title, body: TERMS.section5Body },
        { title: TERMS.section6Title, body: TERMS.section6Body },
        { title: TERMS.section7Title, body: TERMS.section7Body },
        { title: TERMS.section8Title, body: TERMS.section8Body },
      ];

  return (
    <div>
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-heading font-bold text-gray-900 mb-4 leading-tight">
            {isEn ? TERMS.heroTitleEn : TERMS.heroTitle}
          </h1>
          <p className="text-base sm:text-lg text-gray-600 max-w-2xl mx-auto leading-relaxed mb-6">
            {isEn ? TERMS.heroSubtitleEn : TERMS.heroSubtitle}
          </p>
          {/* Language toggle */}
          <div
            className="inline-flex rounded-lg border border-gray-200 bg-white shadow-sm"
            role="group"
            aria-label="Language"
          >
            <button
              type="button"
              onClick={() => setLang("es")}
              className={`px-4 py-2 text-sm font-medium rounded-l-lg transition-colors ${
                lang === "es"
                  ? "bg-primary-600 text-white"
                  : "text-gray-600 hover:text-primary-600"
              }`}
            >
              {TERMS.langEs}
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
              {TERMS.langEn}
            </button>
          </div>
        </div>
      </section>

      {/* Content */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-3xl mx-auto">
          <p className="text-sm text-gray-400 mb-8">
            {isEn ? TERMS.lastUpdatedEn : TERMS.lastUpdated}: {TERMS.lastUpdatedDate}
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
