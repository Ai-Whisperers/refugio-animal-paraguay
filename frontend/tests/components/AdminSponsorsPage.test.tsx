import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

// Mock next/navigation
const mockPush = vi.fn();
const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  usePathname: () => "/admin/sponsors",
}));

// Mock auth
import * as authModule from "@/lib/auth";
vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "mock-token"),
  clearAccessToken: vi.fn(),
  getCurrentUserRole: vi.fn(() => "admin"),
}));

// Mock API
const mockApiGet = vi.fn();
vi.mock("@/lib/api", () => ({
  api: { get: (...args: unknown[]) => mockApiGet(...args) },
  ApiClientError: class extends Error {
    statusCode: number;
    detail: string;
    constructor(msg: string, code: number, detail: string) {
      super(msg);
      this.statusCode = code;
      this.detail = detail;
    }
  },
}));

import AdminSponsorsPage from "@/app/admin/sponsors/page";

function makeSponsorshipItem(overrides: Record<string, unknown> = {}) {
  return {
    id: "sp-001",
    donor_id: "d-001",
    animal_id: "a-001",
    tier_id: "t-001",
    frequency: "monthly",
    status: "active",
    stripe_subscription_id: null,
    total_contributed_cents: 15000,
    started_at: "2026-01-15T00:00:00Z",
    ended_at: null,
    notes: null,
    created_at: "2026-01-15T00:00:00Z",
    updated_at: "2026-03-01T00:00:00Z",
    tier: {
      id: "t-001",
      level: "gold",
      name: "Oro",
      amount_cents: 5000,
      currency: "EUR",
    },
    ...overrides,
  };
}

describe("AdminSponsorsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(screen.getByText("Panel de Padrinos")).toBeInTheDocument();
  });

  it("shows empty state when no sponsorships exist", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(
      await screen.findByText("No hay padrinazgos registrados")
    ).toBeInTheDocument();
  });

  it("renders sponsorship table when data is loaded", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem()],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    // Wait for data to load and table headers to appear
    expect(await screen.findByText("Nivel")).toBeInTheDocument();
    expect(screen.getByText("Estado")).toBeInTheDocument();
    expect(screen.getByText("Frecuencia")).toBeInTheDocument();
    expect(screen.getByText("Monto")).toBeInTheDocument();
  });

  it("displays tier badge with correct label", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem()],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(await screen.findByText("Oro")).toBeInTheDocument();
  });

  it("displays active status badge", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem({ status: "active" })],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(await screen.findByText("Activo")).toBeInTheDocument();
  });

  it("shows frequency label", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem({ frequency: "monthly" })],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(await screen.findByText("Mensual")).toBeInTheDocument();
  });

  it("shows 'Ver animal' link for each sponsorship", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem()],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(await screen.findByText("Ver animal")).toBeInTheDocument();
  });

  it("shows error state on API failure", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));

    render(<AdminSponsorsPage />);
    expect(
      await screen.findByText("Error al cargar padrinos")
    ).toBeInTheDocument();
  });

  it("redirects to login when not authenticated", () => {
    vi.mocked(authModule.isAuthenticated).mockReturnValueOnce(false);

    render(<AdminSponsorsPage />);
    expect(mockReplace).toHaveBeenCalledWith("/admin/login?expired=true");
  });

  it("renders summary cards", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [makeSponsorshipItem()],
      total: 1,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    expect(await screen.findByText("Padrinos activos")).toBeInTheDocument();
    expect(screen.getByText("Ingreso mensual")).toBeInTheDocument();
    expect(screen.getByText("Total contribuido")).toBeInTheDocument();
    expect(screen.getByText("Animales apadrinados")).toBeInTheDocument();
  });

  it("shows status filter dropdown", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });

    render(<AdminSponsorsPage />);
    const select = await screen.findByLabelText("Estado:");
    expect(select).toBeInTheDocument();
  });
});
