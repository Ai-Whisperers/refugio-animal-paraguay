import type { Metadata } from "next";
import { SITE_TITLE, ANIMALS_LIST } from "@/lib/strings";

export const metadata: Metadata = {
  title: `${ANIMALS_LIST.title} | ${SITE_TITLE}`,
  description: ANIMALS_LIST.subtitle,
  openGraph: {
    title: `${ANIMALS_LIST.title} | ${SITE_TITLE}`,
    description: ANIMALS_LIST.subtitle,
    url: "/animals",
  },
};

export default function AnimalsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
