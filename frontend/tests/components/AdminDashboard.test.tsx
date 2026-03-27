import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";

const { mockApiGet, mockIsAuthenticated } = vi.hoisted(() => ({
  mockApiGet: vi.fn(() => Promise.resolve([])),
  mockIsAuthenticated: vi.fn(() => true),
}));

vi.mock("@/lib/auth", () => ({
  isAuthenticated: mockIsAuthenticated,
  getAccessToken: vi.fn(() => "mock-token"),
  decodeToken: vi.fn(() => ({ sub: "user-1", role: "admin", exp: 9999999999 })),
  clearAccessToken: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: { get: mockApiGet },
}));

import AdminDashboardPage from "@/app/admin/dashboard/page";

describe("AdminDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockIsAuthenticated.mockReturnValue(true);
    mockApiGet.mockImplementation(() => Promise.resolve([]));
  });

  it("renders the dashboard title", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Panel de Administracion")).toBeInTheDocument();
    });
  });

  it("shows user role badge for admin", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("admin")).toBeInTheDocument();
    });
  });

  it("renders the welcome text", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Bienvenido")).toBeInTheDocument();
    });
  });

  it("renders quick link section header", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Accesos Rapidos")).toBeInTheDocument();
    });
  });

  it("renders all quick link buttons", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Ver Animales")).toBeInTheDocument();
    });
    expect(screen.getByText("Ver Adopciones")).toBeInTheDocument();
    expect(screen.getByText("Ver Donaciones")).toBeInTheDocument();
    expect(screen.getByText("Ver Donantes")).toBeInTheDocument();
  });

  it("renders quick link descriptions in Spanish", async () => {
    render(<AdminDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Gestionar registro de animales")).toBeInTheDocument();
    });
    expect(screen.getByText("Revisar solicitudes de adopcion")).toBeInTheDocument();
    expect(screen.getByText("Historial de donaciones")).toBeInTheDocument();
    expect(screen.getByText("Perfiles de donantes")).toBeInTheDocument();
  });

  it("shows loading skeletons while data is being fetched", () => {
    render(<AdminDashboardPage />);
    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBe(4);
  });
});
