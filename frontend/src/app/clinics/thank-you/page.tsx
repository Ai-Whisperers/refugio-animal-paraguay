"use client";

import Link from "next/link";
import { CheckCircle, Heart } from "lucide-react";

const S = {
  title: "Gracias por tu donacion!",
  message: "Tu apoyo ayuda a las clinicas veterinarias a brindar servicios accesibles a mas animales.",
  backToClinics: "Ver mas clinicas",
  home: "Volver al inicio",
} as const;

export default function ClinicThankYouPage() {
  return (
    <main className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md w-full text-center">
        <div className="relative inline-block mb-4">
          <CheckCircle className="h-16 w-16 text-green-500" />
          <Heart className="h-6 w-6 text-pink-500 absolute -bottom-1 -right-1" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-3">
          {S.title}
        </h1>
        <p className="text-gray-600 mb-6">
          {S.message}
        </p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link
            href="/clinics"
            className="inline-block bg-teal-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-teal-700 transition-colors"
          >
            {S.backToClinics}
          </Link>
          <Link
            href="/"
            className="inline-block bg-gray-100 text-gray-700 px-6 py-3 rounded-lg font-medium hover:bg-gray-200 transition-colors"
          >
            {S.home}
          </Link>
        </div>
      </div>
    </main>
  );
}
