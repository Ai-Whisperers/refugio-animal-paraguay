import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-shelter-warm py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-6">
            Every Animal Deserves a Loving Home
          </h1>
          <p className="text-lg md:text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Refugio Animal Paraguay rescues, rehabilitates, and rehomes animals
            in need. Join us in making a difference — adopt, donate, or volunteer
            today.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              href="/animals"
              className="inline-block bg-primary-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              Meet Our Animals
            </Link>
            <Link
              href="/donate"
              className="inline-block bg-accent-500 text-white px-8 py-3 rounded-lg font-semibold hover:bg-accent-600 transition-colors"
            >
              Donate Now
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid grid-cols-1 sm:grid-cols-3 gap-8 text-center">
          <div>
            <p className="text-4xl font-bold text-primary-600">150+</p>
            <p className="text-gray-500 mt-1">Animals Rescued</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">80+</p>
            <p className="text-gray-500 mt-1">Successful Adoptions</p>
          </div>
          <div>
            <p className="text-4xl font-bold text-primary-600">50+</p>
            <p className="text-gray-500 mt-1">Active Volunteers</p>
          </div>
        </div>
      </section>

      {/* How to Help Section */}
      <section className="py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-3xl font-heading font-bold text-center text-gray-900 mb-12">
            How You Can Help
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-4">🏠</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Adopt
              </h3>
              <p className="text-gray-500">
                Give a rescued animal a forever home. Browse our available
                animals and start your adoption journey.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-4">💝</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Donate
              </h3>
              <p className="text-gray-500">
                Your contribution helps us provide food, shelter, and medical
                care. We accept EUR and PYG donations.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-4">🤝</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Volunteer
              </h3>
              <p className="text-gray-500">
                Join our team of dedicated volunteers. Help with daily care,
                events, and outreach programs.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
