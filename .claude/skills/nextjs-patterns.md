# Skill: Next.js Frontend Patterns
**Domain**: Next.js 14 App Router, React, Tailwind CSS, API integration
**Load when**: Creating frontend components, pages, layouts, API client code

---

## Project Frontend Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | Next.js 14 | App Router (not Pages Router) |
| Styling | Tailwind CSS 3.x | Utility-first, no custom CSS unless necessary |
| Language | TypeScript 5.x | Strict mode, no `any` types |
| HTTP Client | fetch / SWR | SWR for data fetching with caching |
| Forms | React Hook Form + Zod | Validation schemas shared where possible |
| State | React Context + SWR cache | No Redux — keep it simple |
| Icons | Lucide React | Consistent icon set |
| i18n | next-intl (future) | Spanish primary, English secondary |

---

## Directory Structure

```
frontend/
├── src/
│   ├── app/                    # App Router pages and layouts
│   │   ├── layout.tsx          # Root layout (nav, footer, providers)
│   │   ├── page.tsx            # Homepage
│   │   ├── animals/
│   │   │   ├── page.tsx        # Animal browsing (public)
│   │   │   └── [id]/page.tsx   # Animal detail
│   │   ├── adopt/
│   │   │   └── page.tsx        # Adoption application
│   │   ├── donate/
│   │   │   └── page.tsx        # Donation page
│   │   ├── admin/
│   │   │   ├── layout.tsx      # Admin layout (sidebar, auth guard)
│   │   │   ├── animals/page.tsx
│   │   │   └── adoptions/page.tsx
│   │   └── auth/
│   │       ├── login/page.tsx
│   │       └── register/page.tsx
│   ├── components/
│   │   ├── ui/                 # Reusable primitives (Button, Card, Input)
│   │   ├── animals/            # Animal-specific components
│   │   ├── forms/              # Form components
│   │   └── layout/             # Nav, Footer, Sidebar
│   ├── lib/
│   │   ├── api.ts              # API client (fetch wrapper)
│   │   ├── auth.ts             # Auth utilities (JWT, session)
│   │   └── constants.ts        # Shared constants
│   ├── hooks/                  # Custom React hooks
│   ├── types/                  # TypeScript type definitions
│   └── styles/
│       └── globals.css         # Tailwind base + custom tokens
├── public/                     # Static assets
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## API Client Pattern

```typescript
// src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface ApiOptions extends RequestInit {
  token?: string;
}

export async function apiFetch<T>(
  path: string,
  options: ApiOptions = {}
): Promise<T> {
  const { token, headers: customHeaders, ...rest } = options;

  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...customHeaders,
  };

  if (token) {
    (headers as Record<string, string>)["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    headers,
    ...rest,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new ApiError(response.status, error.message ?? "Request failed", error);
  }

  return response.json();
}
```

---

## Component Conventions

### File Naming
- Components: `PascalCase.tsx` (e.g., `AnimalCard.tsx`)
- Pages: `page.tsx` (Next.js convention)
- Hooks: `use-kebab-case.ts` (e.g., `use-animals.ts`)
- Utils: `kebab-case.ts`

### Component Pattern
```typescript
// src/components/animals/AnimalCard.tsx
interface AnimalCardProps {
  animal: Animal;
  onAdopt?: (id: string) => void;
}

export function AnimalCard({ animal, onAdopt }: AnimalCardProps) {
  return (
    <div className="rounded-lg border bg-white p-4 shadow-sm">
      {/* ... */}
    </div>
  );
}
```

Rules:
- Named exports only (no default exports except pages)
- Props interface defined above the component
- Tailwind classes inline, no CSS modules
- No `React.FC` — use plain function declarations

### Page Pattern (App Router)
```typescript
// src/app/animals/page.tsx
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Animals | Refugio Animal Paraguay",
  description: "Browse animals available for adoption",
};

export default async function AnimalsPage() {
  // Server component by default — fetch data here
  const animals = await apiFetch<Animal[]>("/animals");

  return (
    <main className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold">Available Animals</h1>
      {/* ... */}
    </main>
  );
}
```

---

## Data Fetching

### Server Components (default)
Fetch directly in the component. No `use` prefix, no `useState`.

### Client Components (interactive)
Use SWR for client-side data with automatic revalidation:
```typescript
"use client";
import useSWR from "swr";

export function AnimalList() {
  const { data, error, isLoading } = useSWR("/animals", apiFetch);
  // ...
}
```

---

## Auth Pattern

```typescript
// src/lib/auth.ts
import { cookies } from "next/headers";

export function getToken(): string | null {
  const cookieStore = cookies();
  return cookieStore.get("auth_token")?.value ?? null;
}

export function requireAuth(): string {
  const token = getToken();
  if (!token) redirect("/auth/login");
  return token;
}
```

Admin pages use a layout guard:
```typescript
// src/app/admin/layout.tsx
export default async function AdminLayout({ children }) {
  const token = requireAuth();
  // Verify role is admin/staff
  return <AdminShell>{children}</AdminShell>;
}
```

---

## Tailwind Design Tokens

```typescript
// tailwind.config.ts — project-specific tokens
const config = {
  theme: {
    extend: {
      colors: {
        primary: { 50: "...", 500: "...", 900: "..." },  // Shelter brand
        accent: { 50: "...", 500: "..." },                 // CTA/donate
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      },
    },
  },
};
```

---

## Environment Variables

```
NEXT_PUBLIC_API_URL=http://localhost:8000   # FastAPI backend
NEXT_PUBLIC_STRIPE_KEY=pk_test_...         # Stripe publishable key
NEXT_PUBLIC_SITE_URL=http://localhost:3000  # Frontend URL
```

`NEXT_PUBLIC_` prefix = exposed to browser. Never prefix secrets with it.

---

## Testing Frontend

```bash
npx jest              # Unit tests (components, hooks)
npx playwright test   # E2E tests (critical journeys)
```

Component tests use React Testing Library:
```typescript
import { render, screen } from "@testing-library/react";
import { AnimalCard } from "./AnimalCard";

test("renders animal name", () => {
  render(<AnimalCard animal={mockAnimal} />);
  expect(screen.getByText("Firulais")).toBeInTheDocument();
});
```

---

## Anti-Patterns

- No `use client` unless the component needs interactivity
- No `useEffect` for data fetching — use SWR or server components
- No inline styles — Tailwind only
- No `any` types — define proper interfaces
- No barrel exports (`index.ts`) for components — import directly
- No CSS-in-JS libraries (styled-components, emotion)
