import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { MONTHLY_GIVING, SITE_TITLE } from "@/lib/strings";
import MonthlyGivingFlow from "./MonthlyGivingFlow";

export const metadata: Metadata = {
  title: `${MONTHLY_GIVING.title} | ${SITE_TITLE}`,
  description: MONTHLY_GIVING.metaDescription,
};

export default function MonthlyGivingPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-primary-50 to-green-50 py-10 sm:py-14 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-2xl sm:text-3xl md:text-4xl font-heading font-bold text-gray-900 mb-3 leading-tight">
            {MONTHLY_GIVING.heroTitle}
          </h1>
          <p className="text-sm sm:text-base text-gray-600 max-w-xl mx-auto leading-relaxed">
            {MONTHLY_GIVING.heroSubtitle}
          </p>
        </div>
      </section>

      {/* Form + Impact sidebar */}
      <section className="py-10 sm:py-14 px-4">
        <div className="max-w-4xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main form */}
          <div className="lg:col-span-2">
            <MonthlyGivingFlow />
          </div>

          {/* Impact sidebar */}
          <aside className="hidden lg:block">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 sticky top-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                {MONTHLY_GIVING.impactTitle}
              </h3>
              <ul className="space-y-3">
                {MONTHLY_GIVING.impactItems.map((item) => (
                  <li key={item.amount} className="flex items-start gap-3">
                    <span className="inline-flex items-center justify-center w-8 h-8 bg-primary-100 text-primary-700 rounded-full text-xs font-bold shrink-0">
                      {MONTHLY_GIVING.intervalMonth.charAt(0)}
                    </span>
                    <div>
                      <p className="text-sm font-medium text-gray-900">
                        {item.amount}
                      </p>
                      <p className="text-xs text-gray-500">
                        {item.description}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </aside>
        </div>
      </section>

      {/* Back link */}
      <section className="pb-10 px-4">
        <div className="max-w-4xl mx-auto">
          <Link
            href="/donate"
            className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1 text-sm"
          >
            <ArrowLeft className="h-4 w-4" /> Volver a opciones de donacion
          </Link>
        </div>
      </section>
    </div>
  );
}
