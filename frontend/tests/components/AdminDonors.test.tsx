import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import AdminDonorsPage from "@/app/admin/donors/page";

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "mock-token"),
}));

vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(() => new Promise(() => {})),
  },
  ApiClientError: class ApiClientError extends Error {
    statusCode: number;
    detail: string;
    constructor(message: string, statusCode: number, detail: string) {
      super(message);
      this.statusCode = statusCode;
      this.detail = detail;
    }
  },
}));

describe("AdminDonorsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByText("Gestion de Donantes")).toBeDefined();
  });

  it("renders the search input", () => {
    render(<AdminDonorsPage />);
    expect(
      screen.getByPlaceholderText("Buscar por nombre o email...")
    ).toBeDefined();
  });

  it("renders the export button", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByText("Exportar CSV")).toBeDefined();
  });

  it("renders country filter", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByLabelText(/Pais/)).toBeDefined();
  });

  it("renders GDPR filter", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByLabelText(/GDPR/)).toBeDefined();
  });

  it("renders loading state", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByText("Cargando donantes...")).toBeDefined();
  });

  it("renders the back button", () => {
    render(<AdminDonorsPage />);
    expect(screen.getByLabelText("Volver al panel")).toBeDefined();
  });
});
