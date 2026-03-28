"use client";

import { useCallback, useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface ShareWidgetProps {
  /** Page URL to share. Defaults to current window location. */
  url?: string;
  /** Share title / text for native share and WhatsApp. */
  title: string;
  /** Short description for email body. */
  description?: string;
  /** OG image URL for the share preview card. */
  ogImageUrl?: string;
  /** Visual variant. */
  variant?: "inline" | "floating";
  /** Additional CSS class. */
  className?: string;
}

type Platform = "whatsapp" | "facebook" | "twitter" | "email" | "copy";

// ---------------------------------------------------------------------------
// Spanish strings
// ---------------------------------------------------------------------------

const S = {
  share: "Compartir",
  whatsapp: "WhatsApp",
  facebook: "Facebook",
  twitter: "X (Twitter)",
  email: "Email",
  copyLink: "Copiar enlace",
  copied: "Copiado!",
  shareVia: "Compartir via",
  close: "Cerrar",
} as const;

// ---------------------------------------------------------------------------
// Share URL builders
// ---------------------------------------------------------------------------

function buildShareUrl(platform: Platform, url: string, title: string, description?: string): string {
  const encoded = encodeURIComponent(url);
  const encodedTitle = encodeURIComponent(title);

  switch (platform) {
    case "whatsapp":
      return `https://wa.me/?text=${encodedTitle}%20${encoded}`;
    case "facebook":
      return `https://www.facebook.com/sharer/sharer.php?u=${encoded}`;
    case "twitter":
      return `https://twitter.com/intent/tweet?url=${encoded}&text=${encodedTitle}`;
    case "email": {
      const body = description
        ? encodeURIComponent(`${description}\n\n${url}`)
        : encodeURIComponent(url);
      return `mailto:?subject=${encodedTitle}&body=${body}`;
    }
    default:
      return url;
  }
}

// ---------------------------------------------------------------------------
// Platform icons (inline SVG for zero dependencies)
// ---------------------------------------------------------------------------

function WhatsAppIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
    </svg>
  );
}

function FacebookIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  );
}

function TwitterIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function EmailIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <rect x="2" y="4" width="20" height="16" rx="2" />
      <path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7" />
    </svg>
  );
}

function LinkIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71" />
      <path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71" />
    </svg>
  );
}

function ShareIcon({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}>
      <circle cx="18" cy="5" r="3" />
      <circle cx="6" cy="12" r="3" />
      <circle cx="18" cy="19" r="3" />
      <line x1="8.59" y1="13.51" x2="15.42" y2="17.49" />
      <line x1="15.41" y1="6.51" x2="8.59" y2="10.49" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Share buttons config
// ---------------------------------------------------------------------------

interface ShareButtonConfig {
  platform: Platform;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  color: string;
  hoverColor: string;
}

const SHARE_BUTTONS: ShareButtonConfig[] = [
  {
    platform: "whatsapp",
    label: S.whatsapp,
    icon: WhatsAppIcon,
    color: "bg-green-500",
    hoverColor: "hover:bg-green-600",
  },
  {
    platform: "facebook",
    label: S.facebook,
    icon: FacebookIcon,
    color: "bg-blue-600",
    hoverColor: "hover:bg-blue-700",
  },
  {
    platform: "twitter",
    label: S.twitter,
    icon: TwitterIcon,
    color: "bg-gray-900",
    hoverColor: "hover:bg-black",
  },
  {
    platform: "email",
    label: S.email,
    icon: EmailIcon,
    color: "bg-orange-500",
    hoverColor: "hover:bg-orange-600",
  },
  {
    platform: "copy",
    label: S.copyLink,
    icon: LinkIcon,
    color: "bg-gray-500",
    hoverColor: "hover:bg-gray-600",
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ShareWidget({
  url,
  title,
  description,
  ogImageUrl,
  variant = "inline",
  className = "",
}: ShareWidgetProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const resolvedUrl = url ?? (typeof window !== "undefined" ? window.location.href : "");

  // Close on outside click
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [isOpen]);

  // Close on Escape
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setIsOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen]);

  const handleShare = useCallback(
    async (platform: Platform) => {
      if (platform === "copy") {
        try {
          await navigator.clipboard.writeText(resolvedUrl);
          setCopied(true);
          setTimeout(() => setCopied(false), 2000);
        } catch {
          // Fallback: do nothing
        }
        return;
      }

      // Try native Web Share API first (mobile)
      if (platform === "whatsapp" && navigator.share) {
        try {
          await navigator.share({ title, text: description, url: resolvedUrl });
          setIsOpen(false);
          return;
        } catch {
          // User cancelled or not supported — fall through to URL
        }
      }

      const shareUrl = buildShareUrl(platform, resolvedUrl, title, description);
      window.open(shareUrl, "_blank", "noopener,noreferrer,width=600,height=400");
      setIsOpen(false);
    },
    [resolvedUrl, title, description]
  );

  const isFloating = variant === "floating";

  return (
    <div ref={dropdownRef} className={`relative inline-block ${className}`}>
      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`inline-flex items-center gap-2 rounded-full font-medium
                    transition-all ${
                      isFloating
                        ? "h-12 w-12 justify-center bg-emerald-600 text-white shadow-lg hover:bg-emerald-700"
                        : "bg-gray-100 px-4 py-2 text-sm text-gray-700 hover:bg-gray-200"
                    }`}
        aria-label={S.share}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        <ShareIcon className={isFloating ? "h-5 w-5" : "h-4 w-4"} />
        {!isFloating && <span>{S.share}</span>}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div
          className={`absolute z-50 mt-2 w-56 overflow-hidden rounded-xl bg-white
                      shadow-xl ring-1 ring-black/5 ${
                        isFloating ? "bottom-full right-0 mb-2" : "left-0 top-full"
                      }`}
          role="menu"
          aria-label={S.shareVia}
        >
          {/* OG Image preview */}
          {ogImageUrl && (
            <div className="border-b border-gray-100 p-3">
              <img
                src={ogImageUrl}
                alt={title}
                className="h-auto w-full rounded-lg"
                loading="lazy"
              />
            </div>
          )}

          {/* Share buttons */}
          <div className="p-2">
            {SHARE_BUTTONS.map(({ platform, label, icon: Icon, color, hoverColor }) => (
              <button
                key={platform}
                type="button"
                onClick={() => handleShare(platform)}
                className="flex w-full items-center gap-3 rounded-lg px-3 py-2.5
                           text-left text-sm transition-colors hover:bg-gray-50"
                role="menuitem"
              >
                <span
                  className={`inline-flex h-8 w-8 items-center justify-center
                              rounded-full text-white ${color} ${hoverColor}`}
                >
                  <Icon className="h-4 w-4" />
                </span>
                <span className="font-medium text-gray-700">
                  {platform === "copy" && copied ? S.copied : label}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
