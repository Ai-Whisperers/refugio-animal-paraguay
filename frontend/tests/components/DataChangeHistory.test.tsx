import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import DataChangeHistoryPage from "@/app/admin/audit-logs/resource/[resourceType]/[resourceId]/page";

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    push: mockPush,
    replace: mockReplace,
  })),
  useParams: vi.fn(() => ({
    resourceType: "animal",
    resourceId: "cccc1111-0000-0000-0000-000000000001",
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
      action: "update",
      resource_type: "animal",
      resource_id: "cccc1111-0000-0000-0000-000000000001",
      timestamp: "2026-03-29T10:00:00Z",
      ip_address: "192.168.1.1",
      user_agent: "Mozilla/5.0",
      old_values: { name: "Firulais", status: "available" },
      new_values: { name: "Firulais", status: "reserved" },
      request_id: "req-001",
    },
    {
      id: "aaaaaaaa-0000-0000-0000-000000000002",
      user_id: "bbbbbbbb-0000-0000-0000-000000000002",
      action: "create",
      resource_type: "animal",
      resource_id: "cccc1111-0000-0000-0000-000000000001",
      timestamp: "2026-03-28T09:00:00Z",
      ip_address: null,
      user_agent: null,
      old_values: null,
      new_values: { name: "Firulais", status: "available" },
      request_id: null,
    },
  ],
  total: 2,
  page: 1,
  page_size: 20,
};

describe("DataChangeHistoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockReturnValue(new Promise(() => {}));
  });

  it("renders the page title", () => {
    render(<DataChangeHistoryPage />);
    expect(screen.getByText("Historial de Cambios")).toBeDefined();
  });

  it("renders resource type and ID in header", () => {
    render(<DataChangeHistoryPage />);
    expect(screen.getByText("animal")).toBeDefined();
    expect(
      screen.getByText("cccc1111-0000-0000-0000-000000000001")
    ).toBeDefined();
  });

  it("renders loading state", () => {
    render(<DataChangeHistoryPage />);
    expect(screen.getByText("Cargando historial...")).toBeDefined();
  });

  it("renders the back button", () => {
    render(<DataChangeHistoryPage />);
    expect(screen.getByLabelText("Volver a Auditoria")).toBeDefined();
  });

  it("renders change entries after successful fetch", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Actualizado")).toBeDefined();
    });
    expect(screen.getByText("Creado")).toBeDefined();
  });

  it("renders 'Ver cambios' button for entries with diff", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      const buttons = screen.getAllByText("Ver cambios");
      expect(buttons.length).toBeGreaterThan(0);
    });
  });

  it("expands diff view on click", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(screen.getAllByText("Ver cambios").length).toBeGreaterThan(0);
    });

    fireEvent.click(screen.getAllByText("Ver cambios")[0]);
    expect(screen.getByText("Antes")).toBeDefined();
    expect(screen.getByText("Despues")).toBeDefined();
  });

  it("renders empty state when no entries", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 20,
    });
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(
        screen.getByText("Sin cambios registrados para este recurso")
      ).toBeDefined();
    });
  });

  it("renders error state on API failure", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText("Error al cargar historial")).toBeDefined();
    });
    expect(screen.getByText("Reintentar")).toBeDefined();
  });

  it("passes resource_type and resource_id as query params", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("resource_type=animal")
      );
    });
    expect(mockApiGet.mock.calls[0][0]).toContain(
      "resource_id=cccc1111-0000-0000-0000-000000000001"
    );
  });

  it("shows page info in footer", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<DataChangeHistoryPage />);

    await waitFor(() => {
      expect(screen.getByText(/Mostrando/)).toBeDefined();
    });
  });
});
