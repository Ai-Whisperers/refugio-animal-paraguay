import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      {/* Hero section */}
      <section className="bg-primary-700 px-4 py-20 text-center text-white">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
            Dale un hogar a quien mas lo necesita
          </h1>
          <p className="mt-4 text-lg text-primary-100">
            Refugio Animal Paraguay rescata, rehabilita y busca familias
            amorosas para animales abandonados. Cada adopcion cambia dos vidas.
          </p>
          <div className="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
            <Link
              href="/animals"
              className="rounded-lg bg-white px-6 py-3 font-semibold text-primary-700 shadow transition-colors hover:bg-primary-50"
            >
              Ver animales
            </Link>
            <Link
              href="/donate"
              className="rounded-lg border-2 border-white px-6 py-3 font-semibold text-white transition-colors hover:bg-primary-600"
            >
              Donar ahora
            </Link>
          </div>
        </div>
      </section>

      {/* Stats section */}
      <section className="bg-white px-4 py-16">
        <div className="mx-auto grid max-w-5xl grid-cols-1 gap-8 text-center sm:grid-cols-3">
          <div>
            <p className="text-4xl font-bold text-primary-600">150+</p>
            <p className="mt-1 text-sm text-stone-600">Animales rescatados</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">80+</p>
            <p className="mt-1 text-sm text-stone-600">Adopciones exitosas</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">50+</p>
            <p className="mt-1 text-sm text-stone-600">Voluntarios activos</p>
          </div>
        </div>
      </section>

      {/* How to help section */}
      <section className="bg-shelter-cream px-4 py-16">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-3xl font-bold text-stone-800">
            Como puedes ayudar
          </h2>
          <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-3">
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-primary-700">
                Adopta
              </h3>
              <p className="mt-2 text-sm text-stone-600">
                Encuentra a tu companero perfecto entre nuestros animales
                disponibles para adopcion.
              </p>
              <Link
                href="/adopt"
                className="mt-4 inline-block text-sm font-medium text-primary-600 hover:text-primary-700"
              >
                Conoce el proceso &rarr;
              </Link>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-accent-600">Dona</h3>
              <p className="mt-2 text-sm text-stone-600">
                Tu donacion ayuda a cubrir alimento, atencion veterinaria y
                refugio para los animales.
              </p>
              <Link
                href="/donate"
                className="mt-4 inline-block text-sm font-medium text-accent-600 hover:text-accent-700"
              >
                Haz tu donacion &rarr;
              </Link>
            </div>
            <div className="rounded-lg bg-white p-6 shadow-sm">
              <h3 className="text-lg font-semibold text-shelter-brown">
                Voluntariado
              </h3>
              <p className="mt-2 text-sm text-stone-600">
                Unete a nuestro equipo de voluntarios y marca la diferencia en
                la vida de los animales.
              </p>
              <Link
                href="/contact"
                className="mt-4 inline-block text-sm font-medium text-shelter-brown hover:text-stone-700"
              >
                Contactanos &rarr;
              </Link>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
