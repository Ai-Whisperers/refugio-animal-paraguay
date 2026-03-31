import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import ExportAuditLogsButton from "@/components/admin/ExportAuditLogsButton";
import ExportAuditLogsPage from "@/app/admin/audit-logs/export/page";

// --- Mock setup ---

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    push: mockPush,
    replace: mockReplace,
  })),
}));

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "mock-token"),
}));

// Mock fetch for the export download
const mockFetch = vi.fn();
global.fetch = mockFetch;

// Mock URL.createObjectURL
global.URL.createObjectURL = vi.fn(() => "blob:mock-url");
global.URL.revokeObjectURL = vi.fn();

describe("ExportAuditLogsButton", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders CSV export button by default", () => {
    render(<ExportAuditLogsButton />);
    expect(screen.getByText("Exportar CSV")).toBeDefined();
  });

  it("renders JSON export button when format is json", () => {
    render(<ExportAuditLogsButton format="json" />);
    expect(screen.getByText("Exportar JSON")).toBeDefined();
  });

  it("renders custom label when provided", () => {
    render(<ExportAuditLogsButton label="Descargar Reporte" />);
    expect(screen.getByText("Descargar Reporte")).toBeDefined();
  });

  it("shows loading state during export", async () => {
    mockFetch.mockReturnValueOnce(new Promise(() => {}));
    render(<ExportAuditLogsButton />);

    const button = screen.getByText("Exportar CSV").closest("button")!;
    fireEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("Exportando...")).toBeDefined();
    });
    expect(button.disabled).toBe(true);
  });

  it("calls fetch with correct endpoint for CSV", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(["data"])),
    });

    render(<ExportAuditLogsButton format="csv" />);
    fireEvent.click(screen.getByText("Exportar CSV").closest("button")!);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("format=csv"),
        expect.objectContaining({
          method: "GET",
          headers: expect.objectContaining({
            Authorization: "Bearer mock-token",
          }),
        })
      );
    });
  });

  it("calls fetch with correct endpoint for JSON", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(["[]"])),
    });

    render(<ExportAuditLogsButton format="json" />);
    fireEvent.click(screen.getByText("Exportar JSON").closest("button")!);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("format=json"),
        expect.any(Object)
      );
    });
  });

  it("includes filter params in export URL", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      blob: () => Promise.resolve(new Blob(["data"])),
    });

    render(
      <ExportAuditLogsButton
        filters={{ action: "create", resource_type: "animal" }}
        format="csv"
      />
    );
    fireEvent.click(screen.getByText("Exportar CSV").closest("button")!);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining("action=create"),
        expect.any(Object)
      );
    });

    expect(mockFetch.mock.calls[0][0]).toContain("resource_type=animal");
  });

  it("shows error message on failed export", async () => {
    mockFetch.mockResolvedValueOnce({ ok: false, status: 500 });

    render(<ExportAuditLogsButton />);
    fireEvent.click(screen.getByText("Exportar CSV").closest("button")!);

    await waitFor(() => {
      expect(screen.getByText("Error al exportar")).toBeDefined();
    });
  });

  it("shows error message on network failure", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));

    render(<ExportAuditLogsButton />);
    fireEvent.click(screen.getByText("Exportar CSV").closest("button")!);

    await waitFor(() => {
      expect(screen.getByText("Error al exportar")).toBeDefined();
    });
  });
});

describe("ExportAuditLogsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the page title", () => {
    render(<ExportAuditLogsPage />);
    expect(screen.getByText("Exportar Registros de Auditoria")).toBeDefined();
  });

  it("renders CSV and JSON export cards", () => {
    render(<ExportAuditLogsPage />);
    expect(screen.getByText("CSV")).toBeDefined();
    expect(screen.getByText("JSON")).toBeDefined();
  });

  it("renders both export buttons", () => {
    render(<ExportAuditLogsPage />);
    expect(screen.getByText("Exportar CSV")).toBeDefined();
    expect(screen.getByText("Exportar JSON")).toBeDefined();
  });

  it("renders filter inputs", () => {
    render(<ExportAuditLogsPage />);
    expect(screen.getByLabelText("Accion")).toBeDefined();
    expect(screen.getByLabelText("Tipo de Recurso")).toBeDefined();
    expect(screen.getByLabelText("Desde")).toBeDefined();
    expect(screen.getByLabelText("Hasta")).toBeDefined();
  });

  it("renders the back button", () => {
    render(<ExportAuditLogsPage />);
    expect(screen.getByLabelText("Volver a Auditoria")).toBeDefined();
  });

  it("renders format descriptions", () => {
    render(<ExportAuditLogsPage />);
    expect(
      screen.getByText("Compatible con Excel y Google Sheets")
    ).toBeDefined();
    expect(screen.getByText("Para procesamiento programatico")).toBeDefined();
  });
});
