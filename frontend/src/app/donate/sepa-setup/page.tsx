import type { Metadata } from "next";
import SepaSetupFlow from "./SepaSetupFlow";

export const metadata: Metadata = {
  title: "Configurar Débito SEPA | Refugio Animal Paraguay",
  description:
    "Guarda tu cuenta bancaria europea (IBAN) para donaciones recurrentes via Débito Directo SEPA.",
};

export default function SepaSetupPage() {
  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4">
      <div className="max-w-lg mx-auto">
        <div className="mb-8 text-center">
          <h1 className="text-2xl font-heading font-bold text-gray-900 mb-2">
            Configurar Débito SEPA
          </h1>
          <p className="text-gray-500 text-sm">
            Guarda tu cuenta bancaria de forma segura para donaciones recurrentes.
            Solo se realizará un cargo cuando lo autorices.
          </p>
        </div>
        <SepaSetupFlow />
      </div>
    </div>
  );
}
