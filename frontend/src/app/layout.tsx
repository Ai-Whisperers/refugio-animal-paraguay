import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";
import WhatsAppFab from "@/components/WhatsAppFab";
import WebVitals from "@/components/WebVitals";
import ServiceWorkerRegistration from "@/components/ServiceWorkerRegistration";
import { SITE_TITLE, SITE_DESCRIPTION, SKIP_LINK } from "@/lib/strings";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL ?? "https://refugioanimal.com.py";

export const metadata: Metadata = {
  title: SITE_TITLE,
  description: SITE_DESCRIPTION,
  keywords: ["animal shelter", "Paraguay", "adoption", "rescue", "donate"],
  metadataBase: new URL(BASE_URL),
  openGraph: {
    type: "website",
    locale: "es_PY",
    siteName: SITE_TITLE,
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
    url: BASE_URL,
  },
  twitter: {
    card: "summary_large_image",
    title: SITE_TITLE,
    description: SITE_DESCRIPTION,
  },
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: SITE_TITLE,
  },
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  viewportFit: "cover",
  themeColor: "#E8622A",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="es-PY" className={inter.variable}>
      <body className="flex flex-col min-h-screen font-sans">
        <a href="#main-content" className="skip-link">
          {SKIP_LINK}
        </a>
        <Navbar />
        <main id="main-content" className="flex-1">
          {children}
        </main>
        <Footer />
        <WhatsAppFab />
        <WebVitals />
        <ServiceWorkerRegistration />
      </body>
    </html>
  );
}
