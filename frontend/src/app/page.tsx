import Link from "next/link";
import { Home, Heart, Users, MapPin, Clock, Phone, Mail, Star } from "lucide-react";
import { HOME } from "@/lib/strings";
import LiveStats from "@/components/LiveStats";
import FeaturedAnimals from "@/components/FeaturedAnimals";

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-orange-50 py-12 sm:py-16 md:py-20 px-4 relative overflow-hidden">
        {/* Decorative background element */}
        <div className="absolute inset-0 opacity-5 pointer-events-none">
          <div className="absolute top-10 right-10 w-40 h-40 rounded-full bg-primary-400 blur-3xl" />
          <div className="absolute bottom-10 left-10 w-40 h-40 rounded-full bg-orange-400 blur-3xl" />
        </div>

        <div className="max-w-4xl mx-auto text-center relative z-10">
          {/* Glassmorphism overlay */}
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 sm:p-8 md:p-10 mb-8">
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-heading font-bold text-gray-900 mb-4 sm:mb-6 leading-tight">
              {HOME.heroTitle}
            </h1>
            <p className="text-base sm:text-lg md:text-xl text-gray-600 mb-8 sm:mb-10 max-w-2xl mx-auto leading-relaxed">
              {HOME.heroSubtitle}
            </p>
            <div className="flex flex-col sm:flex-row gap-3 sm:gap-4 justify-center">
              <Link
                href="/animals"
                className="inline-flex items-center justify-center bg-primary-600 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-primary-700 active:bg-primary-800 transition-colors shadow-md hover:shadow-lg"
              >
                {HOME.meetAnimals}
              </Link>
              <Link
                href="/donate"
                className="inline-flex items-center justify-center bg-secondary-600 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-secondary-700 active:bg-secondary-800 transition-colors shadow-md hover:shadow-lg"
              >
                {HOME.donateNow}
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section — live data with count-up animation */}
      <LiveStats />

      {/* Featured Animals Carousel */}
      <FeaturedAnimals />

      {/* How to Help Section */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
            {HOME.howToHelpTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-8">
            <Link
              href="/animals"
              className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 hover:shadow-md hover:border-primary-200 transition-all group"
            >
              <div className="w-12 h-12 rounded-lg bg-primary-100 flex items-center justify-center mb-4 group-hover:bg-primary-200 transition-colors">
                <Home className="w-6 h-6 text-primary-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3">
                {HOME.adoptTitle}
              </h3>
              <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
                {HOME.adoptDescription}
              </p>
            </Link>
            <Link
              href="/donate"
              className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 hover:shadow-md hover:border-secondary-200 transition-all group"
            >
              <div className="w-12 h-12 rounded-lg bg-secondary-100 flex items-center justify-center mb-4 group-hover:bg-secondary-200 transition-colors">
                <Heart className="w-6 h-6 text-secondary-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3">
                {HOME.donateTitle}
              </h3>
              <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
                {HOME.donateDescription}
              </p>
            </Link>
            <Link
              href="/volunteer"
              className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100 hover:shadow-md hover:border-orange-200 transition-all group"
            >
              <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center mb-4 group-hover:bg-orange-200 transition-colors">
                <Users className="w-6 h-6 text-orange-600" />
              </div>
              <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-3">
                {HOME.volunteerTitle}
              </h3>
              <p className="text-gray-600 text-sm sm:text-base leading-relaxed">
                {HOME.volunteerDescription}
              </p>
            </Link>
          </div>
        </div>
      </section>

      {/* Trust Team Section */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
            {HOME.trustTeamTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {HOME.trustTeam.map((member, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 text-center"
              >
                <div className="w-16 h-16 rounded-full bg-white border-2 border-primary-200 flex items-center justify-center mx-auto mb-4">
                  <Users className="w-8 h-8 text-primary-600" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {member.name}
                </h3>
                <p className="text-sm text-gray-600 mt-1">{member.role}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Location/Contact Trust Section */}
      <section className="py-10 sm:py-16 px-4 bg-gray-50">
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8">
            {HOME.trustLocationTitle}
          </h2>
          <div className="bg-white rounded-xl p-6 sm:p-8 shadow-sm border border-gray-100">
            <div className="space-y-4">
              <div className="flex items-start gap-4">
                <MapPin className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-gray-900">{HOME.trustAddress}</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <Clock className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-gray-700">{HOME.trustHours}</p>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <Phone className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <a
                    href={`https://wa.me/${HOME.trustWhatsApp.replace(/\s+/g, '')}`}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {HOME.trustWhatsApp}
                  </a>
                </div>
              </div>
              <div className="flex items-start gap-4">
                <Mail className="w-6 h-6 text-primary-600 flex-shrink-0 mt-0.5" />
                <div>
                  <a
                    href={`mailto:${HOME.trustEmail}`}
                    className="text-primary-600 hover:text-primary-700 font-medium"
                  >
                    {HOME.trustEmail}
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Social Proof Section */}
      <section className="py-10 sm:py-16 px-4 bg-white">
        <div className="max-w-5xl mx-auto">
          <h2 className="text-2xl sm:text-3xl font-heading font-bold text-center text-gray-900 mb-8 sm:mb-12">
            {HOME.socialProofTitle}
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 sm:gap-8">
            {HOME.testimonials.map((testimonial, idx) => (
              <div
                key={idx}
                className="bg-gradient-to-br from-primary-50 to-orange-50 rounded-xl p-6 sm:p-8"
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(5)].map((_: unknown, i: number) => (
                    <Star key={i} className="h-5 w-5 text-orange-400 fill-orange-400" aria-hidden="true" />
                  ))}
                </div>
                <p className="text-gray-700 italic mb-4 leading-relaxed">
                  &quot;{testimonial.quote}&quot;
                </p>
                <div className="border-t border-primary-200 pt-4">
                  <p className="font-semibold text-gray-900">
                    {testimonial.name}
                  </p>
                  <p className="text-sm text-gray-600">{testimonial.animal}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Footer CTA Section */}
      <section className="bg-gradient-to-br from-primary-600 to-orange-600 py-12 sm:py-16 px-4">
        <div className="max-w-2xl mx-auto text-center text-white">
          <p className="text-lg sm:text-xl mb-8 leading-relaxed">
            {HOME.footerCtaText}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href={`https://wa.me/${HOME.trustWhatsApp.replace(/\s+/g, '')}`}
              className="inline-flex items-center justify-center bg-white text-primary-600 px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              {HOME.footerCtaWhatsApp}
            </a>
            <Link
              href="/donate"
              className="inline-flex items-center justify-center bg-secondary-500 text-white px-6 sm:px-8 py-3 rounded-lg font-semibold hover:bg-secondary-600 transition-colors"
            >
              {HOME.footerCtaDonate}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}
