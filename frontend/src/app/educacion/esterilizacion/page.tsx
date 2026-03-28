"use client";

import { useState } from "react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const HERO_TITLE = "Esterilizacion: Un Acto de Amor";
const HERO_SUBTITLE = "Descubre por que esterilizar a tu mascota es una de las decisiones mas importantes que puedes tomar como dueño responsable.";

const CAMPAIGN_PHONE = "+595 981 123456";

interface FAQ {
  question: string;
  answer: string;
}

interface Benefit {
  icon: string;
  title: string;
  description: string;
}

interface Myth {
  myth: string;
  reality: string;
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const BENEFITS: Benefit[] = [
  {
    icon: "heart",
    title: "Mejor salud",
    description: "Reduce el riesgo de cancer y enfermedades reproductivas. Las hembras esterilizadas tienen menor riesgo de tumores mamarios y piometra.",
  },
  {
    icon: "shield",
    title: "Menos abandonos",
    description: "Cada camada no planificada contribuye a la sobrepoblacion. En Paraguay, miles de animales son abandonados cada año.",
  },
  {
    icon: "users",
    title: "Comunidades mas seguras",
    description: "Menos animales callejeros significa menos riesgo de accidentes, mordeduras y transmision de enfermedades.",
  },
  {
    icon: "trending-down",
    title: "Mejor comportamiento",
    description: "Los animales esterilizados son menos agresivos, no marcan territorio y no escapan buscando pareja.",
  },
  {
    icon: "dollar-sign",
    title: "Ahorro economico",
    description: "El costo de una esterilizacion es mucho menor que el de cuidar una camada completa.",
  },
  {
    icon: "globe",
    title: "Impacto ambiental",
    description: "Menos animales callejeros reduce el impacto en ecosistemas locales y la fauna silvestre.",
  },
];

const MYTHS: Myth[] = [
  {
    myth: "Mi mascota debe tener al menos una camada antes de esterilizarla",
    reality: "No hay ninguna evidencia medica que respalde esto. De hecho, esterilizar antes del primer celo reduce significativamente el riesgo de cancer mamario.",
  },
  {
    myth: "La esterilizacion cambia la personalidad de mi mascota",
    reality: "La personalidad fundamental no cambia. Lo que si disminuye son comportamientos no deseados como marcaje, agresividad y tendencia a escapar.",
  },
  {
    myth: "Es una cirugia muy cara",
    reality: "Muchos refugios y clinicas ofrecen programas de esterilizacion a bajo costo o gratuitos. El costo es minimo comparado con los gastos de una camada.",
  },
  {
    myth: "Solo las hembras necesitan ser esterilizadas",
    reality: "Los machos tambien deben ser esterilizados. Un solo macho no castrado puede fecundar a muchas hembras, contribuyendo enormemente a la sobrepoblacion.",
  },
  {
    myth: "Mi mascota va a engordar",
    reality: "El aumento de peso se debe a la sobrealimentacion y falta de ejercicio, no a la esterilizacion. Con una dieta adecuada, mantendran su peso ideal.",
  },
];

const FAQS: FAQ[] = [
  {
    question: "A que edad se puede esterilizar?",
    answer: "Se recomienda a partir de los 4-6 meses de edad. Tu veterinario puede asesorarte sobre el mejor momento segun la raza y estado de salud.",
  },
  {
    question: "Cuanto tiempo dura la recuperacion?",
    answer: "Generalmente entre 7 y 10 dias. Las mascotas suelen retomar su actividad normal en pocos dias con los cuidados postoperatorios adecuados.",
  },
  {
    question: "Donde puedo esterilizar a mi mascota en Paraguay?",
    answer: "Refugio Animal Paraguay organiza campañas de esterilizacion periodicas. Contactanos por WhatsApp para conocer las proximas fechas.",
  },
  {
    question: "Es dolorosa la cirugia?",
    answer: "Se realiza bajo anestesia general, por lo que el animal no siente dolor durante el procedimiento. Se administran analgesicos para la recuperacion.",
  },
];

const STATISTICS = [
  { value: "70%", label: "de animales callejeros son resultado de camadas no planificadas" },
  { value: "200%", label: "de reduccion en riesgo de cancer uterino tras esterilizar" },
  { value: "80%", label: "menos agresividad en machos castrados" },
  { value: "1", label: "pareja de gatos puede generar 420,000 descendientes en 7 años" },
];

// ---------------------------------------------------------------------------
// Components
// ---------------------------------------------------------------------------

function BenefitCard({ benefit }: { benefit: Benefit }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 shadow-sm hover:shadow-md transition-shadow">
      <h3 className="font-semibold text-gray-900 text-lg mb-2">{benefit.title}</h3>
      <p className="text-sm text-gray-600 leading-relaxed">{benefit.description}</p>
    </div>
  );
}

function MythCard({ item }: { item: Myth }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
      <div className="bg-red-50 px-5 py-3 border-b border-red-100">
        <p className="text-red-700 font-medium text-sm">Mito: &ldquo;{item.myth}&rdquo;</p>
      </div>
      <div className="bg-green-50 px-5 py-3">
        <p className="text-green-700 text-sm">Realidad: {item.reality}</p>
      </div>
    </div>
  );
}

function FAQItem({ faq }: { faq: FAQ }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-5 py-4 text-left bg-white hover:bg-gray-50 transition-colors min-h-[44px]"
        aria-expanded={isOpen}
      >
        <span className="font-medium text-gray-900 text-sm">{faq.question}</span>
        <span className="text-gray-400 ml-2">{isOpen ? "−" : "+"}</span>
      </button>
      {isOpen && (
        <div className="px-5 py-3 bg-gray-50 border-t border-gray-100">
          <p className="text-sm text-gray-600">{faq.answer}</p>
        </div>
      )}
    </div>
  );
}

function StatCard({ value, label }: { value: string; label: string }) {
  return (
    <div className="text-center" role="group" aria-label={`${value} ${label}`}>
      <p className="text-3xl font-bold text-orange-600">{value}</p>
      <p className="text-xs text-gray-600 mt-1 leading-snug">{label}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function SterilizationAwarenessPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Hero */}
      <section className="bg-gradient-to-br from-orange-600 to-orange-700 text-white py-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl font-bold mb-4">{HERO_TITLE}</h1>
          <p className="text-lg text-orange-100 max-w-2xl mx-auto">{HERO_SUBTITLE}</p>
          <a
            href={`https://wa.me/${CAMPAIGN_PHONE.replace(/\D/g, "")}`}
            className="inline-block mt-6 bg-white text-orange-600 px-6 py-3 rounded-xl font-semibold hover:bg-orange-50 transition-colors min-h-[44px]"
            aria-label="Agendar esterilizacion por WhatsApp"
          >
            Agendar esterilizacion
          </a>
        </div>
      </section>

      <div className="max-w-5xl mx-auto px-4 py-12 sm:px-6 lg:px-8 space-y-16">
        {/* Statistics */}
        <section aria-label="Estadisticas sobre esterilizacion">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            {STATISTICS.map((stat, idx) => (
              <StatCard key={idx} value={stat.value} label={stat.label} />
            ))}
          </div>
        </section>

        {/* Benefits */}
        <section aria-label="Beneficios de la esterilizacion">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Beneficios de la esterilizacion</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {BENEFITS.map((benefit, idx) => (
              <BenefitCard key={idx} benefit={benefit} />
            ))}
          </div>
        </section>

        {/* Myths vs Reality */}
        <section aria-label="Mitos y realidades">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Mitos y Realidades</h2>
          <div className="space-y-4">
            {MYTHS.map((item, idx) => (
              <MythCard key={idx} item={item} />
            ))}
          </div>
        </section>

        {/* FAQ */}
        <section aria-label="Preguntas frecuentes">
          <h2 className="text-xl font-bold text-gray-900 mb-6">Preguntas frecuentes</h2>
          <div className="space-y-3" role="list">
            {FAQS.map((faq, idx) => (
              <div key={idx} role="listitem">
                <FAQItem faq={faq} />
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="bg-orange-50 rounded-2xl p-8 text-center border border-orange-200" aria-label="Llamada a la accion">
          <h2 className="text-xl font-bold text-gray-900 mb-3">
            Sumate a la causa
          </h2>
          <p className="text-sm text-gray-600 max-w-xl mx-auto mb-6">
            Contactanos para programar la esterilizacion de tu mascota o para
            informarte sobre nuestras proximas campañas comunitarias.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <a
              href={`https://wa.me/${CAMPAIGN_PHONE.replace(/\D/g, "")}`}
              className="bg-green-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-green-700 transition-colors min-h-[44px] min-w-[44px]"
              aria-label="Contactar por WhatsApp"
            >
              WhatsApp
            </a>
            <a
              href="/contacto"
              className="bg-orange-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-orange-700 transition-colors min-h-[44px] min-w-[44px]"
              aria-label="Ir a la pagina de contacto"
            >
              Contacto
            </a>
          </div>
        </section>
      </div>
    </div>
  );
}
