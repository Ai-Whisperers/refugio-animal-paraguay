import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        // Primary: Warm orange (#E8622A) - energy, hope
        primary: {
          50: "#fef6f2",
          100: "#fdeae0",
          200: "#fbd3bf",
          300: "#f7b08e",
          400: "#f28b5c",
          500: "#E8622A",
          600: "#E8622A",
          700: "#C44D1A",
          800: "#9E3E15",
          900: "#7D3213",
          950: "#431707",
        },
        // Secondary: Nature green (#2A7E62) - wellbeing, trust
        secondary: {
          50: "#f0faf6",
          100: "#d9f2e8",
          200: "#b5e4d2",
          300: "#84cfb4",
          400: "#52b492",
          500: "#2A7E62",
          600: "#2A7E62",
          700: "#1A5E47",
          800: "#184B3A",
          900: "#153E31",
          950: "#0A231C",
        },
        // Accent: kept for special UI highlights
        accent: {
          50: "#fff7ed",
          100: "#ffedd5",
          200: "#fed7aa",
          300: "#fdba74",
          400: "#fb923c",
          500: "#f97316",
          600: "#ea580c",
          700: "#c2410c",
          800: "#9a3412",
          900: "#7c2d12",
          950: "#431407",
        },
        // Status colors from UX-PRINCIPLES.md
        status: {
          success: "#2A7E62",
          warning: "#E8922A",
          error: "#D93025",
          urgent: "#D93025",
          available: "#2A7E62",
          pending: "#E8922A",
        },
        // Warm neutrals
        warm: {
          bg: "#FAFAF8",
          surface: "#FFFFFF",
          border: "#E5E5E0",
          "text-primary": "#1A1A18",
          "text-secondary": "#6B6B63",
          "text-muted": "#9B9B92",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        heading: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
    },
  },
  plugins: [],
};
export default config;
