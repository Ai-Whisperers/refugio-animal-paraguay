import { MessageCircle } from "lucide-react";

const WHATSAPP_NUMBER = process.env.NEXT_PUBLIC_WHATSAPP_NUMBER ?? "595981000000";
const DEFAULT_MESSAGE = "Hola! Me gustaria obtener informacion sobre el Refugio Animal Paraguay.";

/**
 * Floating WhatsApp action button visible on every page.
 * Opens WhatsApp chat with pre-filled message.
 */
export default function WhatsAppFab() {
  const url = `https://wa.me/${WHATSAPP_NUMBER.replace(/\s/g, "")}?text=${encodeURIComponent(DEFAULT_MESSAGE)}`;

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      aria-label="Contactar por WhatsApp"
      className="fixed bottom-6 right-6 z-30 flex items-center justify-center w-14 h-14 md:w-16 md:h-16 rounded-full bg-[#25D366] text-white shadow-lg hover:bg-[#1fb855] hover:shadow-xl hover:scale-105 transition-all duration-300 animate-pulse-once"
    >
      <MessageCircle className="h-7 w-7 md:h-8 md:w-8" />
    </a>
  );
}
