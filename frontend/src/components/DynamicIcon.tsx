"use client";

import {
  Utensils,
  Stethoscope,
  Wrench,
  Truck,
  Package,
  Heart,
  Handshake,
  PawPrint,
  Car,
  PartyPopper,
  Camera,
  Home,
  Clock,
  Star,
  type LucideIcon,
} from "lucide-react";

const ICON_MAP: Record<string, LucideIcon> = {
  utensils: Utensils,
  stethoscope: Stethoscope,
  wrench: Wrench,
  truck: Truck,
  package: Package,
  heart: Heart,
  handshake: Handshake,
  dog: PawPrint,
  car: Car,
  "party-popper": PartyPopper,
  camera: Camera,
  home: Home,
  clock: Clock,
  star: Star,
  "paw-print": PawPrint,
};

interface DynamicIconProps {
  name: string;
  className?: string;
}

export default function DynamicIcon({ name, className = "h-8 w-8" }: DynamicIconProps) {
  const IconComponent = ICON_MAP[name];
  if (!IconComponent) {
    return <PawPrint className={className} aria-hidden="true" />;
  }
  return <IconComponent className={className} aria-hidden="true" />;
}
