import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import AnimalHistoryTimeline from "@/components/admin/AnimalHistoryTimeline";
import type { AuditLogListResponse } from "@/types/api";

const mockGet = vi.fn();

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockGet(...args),
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

const MOCK_ENTRIES: AuditLogListResponse = {
  items: [
    {
      id: "log-1",
      user_id: "user-1",
      action: "create",
      resource_type: "animal",
      resource_id: "animal-123",
      timestamp: "2026-03-20T10:00:00Z",
      ip_address: null,
      user_agent: null,
      old_values: null,
      new_values: null,
      request_id: null,
    },
    {
      id: "log-2",
      user_id: "user-1",
      action: "update",
      resource_type: "animal",
      resource_id: "animal-123",
      timestamp: "2026-03-21T14:30:00Z",
      ip_address: null,
      user_agent: null,
      old_values: { status: "intake" },
      new_values: { status: "available" },
      request_id: null,
    },
    {
      id: "log-3",
      user_id: "user-2",
      action: "update",
      resource_type: "animal",
      resource_id: "animal-123",
      timestamp: "2026-03-22T09:15:00Z",
      ip_address: null,
      user_agent: null,
      old_values: { name: "Luna" },
      new_values: { name: "Luna Maria" },
      request_id: null,
    },
  ],
  total: 3,
  page: 1,
  page_size: 50,
};

describe("AnimalHistoryTimeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("shows loading state initially", () => {
    mockGet.mockReturnValue(new Promise(() => {})); // never resolves
    render(<AnimalHistoryTimeline animalId="animal-123" />);
    expect(screen.getByText("Cargando historial...")).toBeDefined();
  });

  it("shows Historial title", () => {
    mockGet.mockReturnValue(new Promise(() => {}));
    render(<AnimalHistoryTimeline animalId="animal-123" />);
    expect(screen.getByText("Historial")).toBeDefined();
  });

  it("renders timeline entries after loading", async () => {
    mockGet.mockResolvedValueOnce(MOCK_ENTRIES);
    render(<AnimalHistoryTimeline animalId="animal-123" />);

    await waitFor(() => {
      expect(screen.getByText("Creado")).toBeDefined();
    });

    // Two "Actualizado" entries
    const updateLabels = screen.getAllByText("Actualizado");
    expect(updateLabels.length).toBe(2);
  });

  it("renders status change badges for status updates", async () => {
    mockGet.mockResolvedValueOnce(MOCK_ENTRIES);
    render(<AnimalHistoryTimeline animalId="animal-123" />);

    await waitFor(() => {
      expect(screen.getByText("Ingreso")).toBeDefined();
      expect(screen.getByText("Disponible")).toBeDefined();
    });
  });

  it("renders changed fields for non-status updates", async () => {
    mockGet.mockResolvedValueOnce(MOCK_ENTRIES);
    render(<AnimalHistoryTimeline animalId="animal-123" />);

    await waitFor(() => {
      expect(screen.getByText("Campos: name")).toBeDefined();
    });
  });

  it("shows empty state when no entries", async () => {
    mockGet.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });
    render(<AnimalHistoryTimeline animalId="animal-123" />);

    await waitFor(() => {
      expect(screen.getByText("Sin eventos registrados")).toBeDefined();
    });
  });

  it("calls API with correct resource filters", async () => {
    mockGet.mockResolvedValueOnce({ items: [], total: 0, page: 1, page_size: 50 });
    render(<AnimalHistoryTimeline animalId="animal-xyz" />);

    await waitFor(() => {
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("resource_type=animal")
      );
      expect(mockGet).toHaveBeenCalledWith(
        expect.stringContaining("resource_id=animal-xyz")
      );
    });
  });

  it("shows error state on API failure", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network error"));
    render(<AnimalHistoryTimeline animalId="animal-123" />);

    await waitFor(() => {
      expect(screen.getByText("Error al cargar historial")).toBeDefined();
    });

    expect(screen.getByText("Reintentar")).toBeDefined();
  });
});
