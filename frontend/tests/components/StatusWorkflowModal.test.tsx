import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import StatusWorkflowModal from "@/components/admin/StatusWorkflowModal";

// Mock API
vi.mock("@/lib/api", () => ({
  api: {
    patch: vi.fn(),
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

import { api } from "@/lib/api";
const mockPatch = vi.mocked(api.patch);

const DEFAULT_PROPS = {
  animalId: "animal-123",
  animalName: "Luna",
  currentStatus: "available" as const,
  onClose: vi.fn(),
  onStatusChanged: vi.fn(),
};

describe("StatusWorkflowModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders modal with animal name and current status", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    expect(screen.getByText("Luna")).toBeDefined();
    expect(screen.getByText("Disponible")).toBeDefined();
  });

  it("shows valid transitions for available status", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    // available -> foster, adopted, under_treatment, quarantine, deceased
    expect(screen.getByText("Acogida")).toBeDefined();
    expect(screen.getByText("Adoptado")).toBeDefined();
    expect(screen.getByText("En tratamiento")).toBeDefined();
    expect(screen.getByText("Cuarentena")).toBeDefined();
    expect(screen.getByText("Fallecido")).toBeDefined();
  });

  it("shows no transitions for deceased status", () => {
    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        currentStatus="deceased"
      />
    );
    expect(
      screen.getByText("No hay transiciones disponibles desde este estado")
    ).toBeDefined();
  });

  it("shows confirmation step after selecting a status", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    fireEvent.click(screen.getByText("Adoptado"));
    expect(screen.getByText(/Cambiar estado de/)).toBeDefined();
    expect(screen.getByText("Confirmar cambio")).toBeDefined();
  });

  it("shows terminal warning when selecting deceased", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    fireEvent.click(screen.getByText("Fallecido"));
    expect(
      screen.getByText("Este es un estado terminal. No se podra revertir.")
    ).toBeDefined();
  });

  it("calls onClose when cancel is clicked", () => {
    const onClose = vi.fn();
    render(<StatusWorkflowModal {...DEFAULT_PROPS} onClose={onClose} />);
    fireEvent.click(screen.getByText("Cancelar"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls API and onStatusChanged on confirm", async () => {
    mockPatch.mockResolvedValueOnce({});
    const onStatusChanged = vi.fn();

    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        onStatusChanged={onStatusChanged}
      />
    );

    // Select status
    fireEvent.click(screen.getByText("Adoptado"));
    // Confirm
    fireEvent.click(screen.getByText("Confirmar cambio"));

    // Wait for async
    await vi.waitFor(() => {
      expect(mockPatch).toHaveBeenCalledWith("/animals/animal-123", {
        status: "adopted",
      });
    });

    await vi.waitFor(() => {
      expect(onStatusChanged).toHaveBeenCalledWith("adopted");
    });
  });

  it("shows only valid transitions for intake status", () => {
    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        currentStatus="intake"
      />
    );
    // intake -> quarantine, available, under_treatment
    expect(screen.getByText("Cuarentena")).toBeDefined();
    expect(screen.getByText("Disponible")).toBeDefined();
    expect(screen.getByText("En tratamiento")).toBeDefined();
    // Should NOT show adopted, foster, deceased
    expect(screen.queryByText("Adoptado")).toBeNull();
    expect(screen.queryByText("Acogida")).toBeNull();
  });

  it("can go back from confirmation to selection", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    fireEvent.click(screen.getByText("Adoptado"));
    expect(screen.getByText("Confirmar cambio")).toBeDefined();
    fireEvent.click(screen.getByText("Cancelar"));
    // Back to selection view
    expect(screen.getByText("Seleccionar nuevo estado")).toBeDefined();
  });
});
