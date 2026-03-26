/**
 * Application-wide constants for Refugio Animal Paraguay frontend.
 */

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const APP_NAME = "Refugio Animal Paraguay";

export const APP_DESCRIPTION =
  "Refugio de animales en Paraguay - Adopta, dona y ayuda a los animales que necesitan un hogar.";

export const AUTH_TOKEN_KEY = "refugio_access_token";
export const AUTH_REFRESH_TOKEN_KEY = "refugio_refresh_token";

export const DEFAULT_PAGE_SIZE = 20;

export const SUPPORTED_LOCALES = ["es", "en"] as const;
export type SupportedLocale = (typeof SUPPORTED_LOCALES)[number];

export const NAV_LINKS = [
  { href: "/", label: "Inicio" },
  { href: "/animals", label: "Animales" },
  { href: "/adopt", label: "Adoptar" },
  { href: "/donate", label: "Donar" },
  { href: "/about", label: "Nosotros" },
  { href: "/contact", label: "Contacto" },
] as const;
