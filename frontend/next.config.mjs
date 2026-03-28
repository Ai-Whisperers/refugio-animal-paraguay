/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || "",
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH || "",
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "images.unsplash.com",
      },
      {
        protocol: "https",
        hostname: "placedog.net",
      },
      {
        protocol: "https",
        hostname: "sunstein.cloud",
      },
    ],
    unoptimized: false,
    // Serve modern image formats for smaller payloads
    formats: ["image/avif", "image/webp"],
    // Responsive breakpoints matching Tailwind defaults
    deviceSizes: [640, 750, 828, 1080, 1200, 1920],
    imageSizes: [16, 32, 48, 64, 96, 128, 256, 384],
  },
  // Enable gzip compression for all responses
  compress: true,
  // Strip console.log in production for smaller bundles
  compiler: {
    removeConsole: process.env.NODE_ENV === "production" ? { exclude: ["error", "warn"] } : false,
  },
  // Performance headers
  headers: async () => [
    {
      source: "/(.*)",
      headers: [
        { key: "X-Content-Type-Options", value: "nosniff" },
        { key: "X-Frame-Options", value: "DENY" },
      ],
    },
    {
      // Cache static assets aggressively
      source: "/_next/static/(.*)",
      headers: [
        { key: "Cache-Control", value: "public, max-age=31536000, immutable" },
      ],
    },
    {
      // Cache optimized images
      source: "/_next/image(.*)",
      headers: [
        { key: "Cache-Control", value: "public, max-age=86400, stale-while-revalidate=604800" },
      ],
    },
  ],
};

export default nextConfig;
