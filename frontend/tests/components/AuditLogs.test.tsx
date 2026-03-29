import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AuditLogsPage from "@/app/admin/audit-logs/page";

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    push: vi.fn(),
    replace: vi.fn(),
  })),
}));

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
}));

const mockApiGet = vi.fn(() => new Promise(() => {}));

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockApiGet(...args),
  },
  ApiClientError: class ApiClientError extends Error {
    statusCode: number;
    detail: string;
    constructor(message: string, statusCode: number, detail: string) {
      super(message);
      this.name = "ApiClientError";
      this.statusCode = statusCode;
      this.detail = detail;
    }
  },
}));

const MOCK_RESPONSE = {
  items: [
    {
      id: "aaaaaaaa-0000-0000-0000-000000000001",
      user_id: "bbbbbbbb-0000-0000-0000-000000000001",
      action: "create",
      resource_type: "animal",
      resource_id: "cccc1111",
      timestamp: "2026-03-29T10:00:00Z",
      ip_address: "192.168.1.1",
      user_agent: "Mozilla/5.0",
      old_values: null,
      new_values: { name: "Firulais" },
      request_id: "req-001",
    },
    {
      id: "aaaaaaaa-0000-0000-0000-000000000002",
      user_id: "bbbbbbbb-0000-0000-0000-000000000002",
      action: "delete",
      resource_type: "donor",
      resource_id: null,
      timestamp: "2026-03-29T11:00:00Z",
      ip_address: null,
      user_agent: null,
      old_values: null,
      new_values: null,
      request_id: null,
    },
  ],
  total: 2,
  page: 1,
  page_size: 50,
};

describe("AuditLogsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockReturnValue(new Promise(() => {}));
  });

  it("renders the page title", () => {
    render(<AuditLogsPage />);
    expect(screen.getByText("Registros de Auditoria")).toBeDefined();
  });

  it("renders the loading state initially", () => {
    render(<AuditLogsPage />);
    expect(screen.getByText("Cargando registros...")).toBeDefined();
  });

  it("renders the back button", () => {
    render(<AuditLogsPage />);
    expect(screen.getByLabelText("Volver al panel")).toBeDefined();
  });

  it("renders the filter toggle button", () => {
    render(<AuditLogsPage />);
    expect(screen.getByText("Filtros")).toBeDefined();
  });

  it("renders audit entries after successful fetch", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("animal")).toBeDefined();
    });

    expect(screen.getByText("donor")).toBeDefined();
    expect(screen.getByText(/Mostrando/)).toBeDefined();
  });

  it("renders action badges with Spanish labels", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("Crear")).toBeDefined();
    });
    expect(screen.getByText("Eliminar")).toBeDefined();
  });

  it("renders the empty state when no entries", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 50,
    });
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("No se encontraron registros de auditoria")
      ).toBeDefined();
    });
  });

  it("renders error state on API failure", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Error al cargar registros de auditoria")
      ).toBeDefined();
    });
    expect(screen.getByText("Reintentar")).toBeDefined();
  });

  it("shows filter panel when filter button is clicked", async () => {
    render(<AuditLogsPage />);
    const filterButton = screen.getByText("Filtros");
    fireEvent.click(filterButton);

    expect(screen.getByText("Accion")).toBeDefined();
    expect(screen.getByText("Tipo de Recurso")).toBeDefined();
    expect(screen.getByText("Desde")).toBeDefined();
    expect(screen.getByText("Hasta")).toBeDefined();
  });

  it("renders pagination controls when entries exist", async () => {
    mockApiGet.mockResolvedValueOnce({
      ...MOCK_RESPONSE,
      total: 200,
    });
    render(<AuditLogsPage />);

    await waitFor(() => {
      expect(screen.getByText("Anterior")).toBeDefined();
    });
    expect(screen.getByText("Siguiente")).toBeDefined();
  });

  it("disables previous button on first page", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<AuditLogsPage />);

    await waitFor(() => {
      const prevButton = screen.getByText("Anterior").closest("button");
      expect(prevButton?.disabled).toBe(true);
    });
  });
});
