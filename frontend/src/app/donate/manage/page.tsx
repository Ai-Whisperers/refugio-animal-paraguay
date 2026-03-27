import type { Metadata } from "next";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { SUBSCRIPTION_MANAGE, SITE_TITLE } from "@/lib/strings";
import SubscriptionManager from "./SubscriptionManager";

export const metadata: Metadata = {
  title: `${SUBSCRIPTION_MANAGE.title} | ${SITE_TITLE}`,
  description: SUBSCRIPTION_MANAGE.metaDescription,
};

export default function ManageSubscriptionPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-lg mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            {SUBSCRIPTION_MANAGE.title}
          </h1>
          <p className="text-gray-500 text-sm">
            {SUBSCRIPTION_MANAGE.lookupDescription}
          </p>
        </div>
        <SubscriptionManager />
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
