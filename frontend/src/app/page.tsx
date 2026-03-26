import Link from "next/link";

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 md:py-20 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 sm:mb-6 leading-tight">
            Every Animal Deserves a Loving Home
          </h1>
          <p className="text-base sm:text-lg md:text-xl text-gray-600 mb-6 sm:mb-8 max-w-2xl mx-auto leading-relaxed">
            Refugio Animal Paraguay rescues, rehabilitates, and rehomes animals
            in need. Join us in making a difference — adopt, donate, or volunteer
            today.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
            <Link
              href="/animals"
              className="inline-flex items-center justify-center bg-primary-600 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 active:bg-primary-800 transition-colors"
            >
              Meet Our Animals
            </Link>
            <Link
              href="/donate"
              className="inline-flex items-center justify-center bg-accent-500 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-accent-600 active:bg-accent-700 transition-colors"
            >
              Donate Now
            </Link>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto grid grid-cols-3 gap-4 sm:gap-8 text-center">
          <div>
            <p className="text-2xl sm:text-4xl font-bold text-primary-600">
              150+
            </p>
            <p className="text-gray-500 mt-1 text-xs sm:text-base">
              Animals Rescued
            </p>
          </div>
          <div>
            <p className="text-2xl sm:text-4xl font-bold text-primary-600">
              80+
            </p>
            <p className="text-gray-500 mt-1 text-xs sm:text-base">
              Successful Adoptions
            </p>
          </div>
          <div>
            <p className="text-2xl sm:text-4xl font-bold text-primary-600">
              50+
            </p>
            <p className="text-gray-500 mt-1 text-xs sm:text-base">
              Active Volunteers
            </p>
          </div>
        </div>
      </section>

      {/* How to Help Section */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
            How You Can Help
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-8">
            <div className="bg-white rounded-xl p-5 sm:p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-3 sm:mb-4">🏠</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                Adopt
              </h3>
              <p className="text-gray-500 text-sm sm:text-base leading-relaxed">
                Give a rescued animal a forever home. Browse our available
                animals and start your adoption journey.
              </p>
            </div>
            <div className="bg-white rounded-xl p-5 sm:p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-3 sm:mb-4">💝</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                Donate
              </h3>
              <p className="text-gray-500 text-sm sm:text-base leading-relaxed">
                Your contribution helps us provide food, shelter, and medical
                care. We accept EUR and PYG donations.
              </p>
            </div>
            <div className="bg-white rounded-xl p-5 sm:p-6 shadow-sm border border-gray-100">
              <div className="text-3xl mb-3 sm:mb-4">🤝</div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">
                Volunteer
              </h3>
              <p className="text-gray-500 text-sm sm:text-base leading-relaxed">
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
