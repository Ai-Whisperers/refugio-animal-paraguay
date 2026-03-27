import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { DONOR_DASHBOARD, SITE_TITLE } from "@/lib/strings";
import DonorDashboard from "./DonorDashboard";

export const metadata: Metadata = {
  title: `${DONOR_DASHBOARD.title} | ${SITE_TITLE}`,
  description: DONOR_DASHBOARD.metaDescription,
};

export default function DonorDashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-2xl mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            {DONOR_DASHBOARD.title}
          </h1>
          <p className="text-gray-500 text-sm">
            {DONOR_DASHBOARD.lookupDescription}
          </p>
        </div>
        <DonorDashboard />
        <div className="mt-8 text-center">
          <Link
            href="/donate"
            className="text-primary-600 hover:text-primary-700 font-medium inline-flex items-center gap-1 text-sm"
          >
            <ArrowLeft className="h-4 w-4" /> Volver a opciones de donacion
          </Link>
        </div>
      </div>
    </div>
  );
}
