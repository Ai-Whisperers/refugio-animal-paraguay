import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import StatusWorkflowModal, {
  VALID_TRANSITIONS,
} from "@/components/admin/StatusWorkflowModal";
import type { AnimalStatus } from "@/types/api";

// Mock the API module
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

const DEFAULT_PROPS = {
  animalId: "test-uuid-123",
  animalName: "Luna",
  currentStatus: "intake" as AnimalStatus,
  onClose: vi.fn(),
  onStatusChanged: vi.fn(),
};

describe("StatusWorkflowModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the modal with animal name", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    expect(screen.getByText(/Cambiar Estado: Luna/)).toBeInTheDocument();
  });

  it("displays the current status badge", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    // "Ingreso" appears multiple times (current badge + transition labels)
    const ingresoElements = screen.getAllByText("Ingreso");
    expect(ingresoElements.length).toBeGreaterThan(0);
  });

  it("shows valid transitions for intake status", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    // intake can go to: quarantine, available, under_treatment
    expect(screen.getByText("Cuarentena")).toBeInTheDocument();
    expect(screen.getByText("Disponible")).toBeInTheDocument();
    expect(screen.getByText("En tratamiento")).toBeInTheDocument();
  });

  it("does not show invalid transitions for intake status", () => {
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);
    // intake cannot go directly to adopted, foster, or deceased
    const buttons = screen.getAllByRole("button");
    const buttonTexts = buttons.map((b) => b.textContent);
    const hasAdopted = buttonTexts.some((t) => t?.includes("Adoptado"));
    // Adoptado should not be in the transition buttons
    // It might appear in the current status badge area, so check transition buttons specifically
    const transitionArea = screen.getByText("Seleccionar nuevo estado").parentElement;
    if (transitionArea) {
      const adoptadoInTransitions = within(transitionArea).queryByText("Adoptado");
      expect(adoptadoInTransitions).not.toBeInTheDocument();
    }
  });

  it("shows no transitions message for deceased status", () => {
    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        currentStatus="deceased"
      />
    );
    expect(
      screen.getByText("No hay transiciones disponibles desde este estado")
    ).toBeInTheDocument();
  });

  it("shows confirmation step when a transition is selected", async () => {
    const user = userEvent.setup();
    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);

    // Click on "Disponible" transition
    const transitionButtons = screen.getAllByRole("button");
    const disponibleButton = transitionButtons.find((b) =>
      b.textContent?.includes("Disponible")
    );
    expect(disponibleButton).toBeDefined();

    await user.click(disponibleButton!);
    expect(screen.getByText(/Estas seguro de cambiar el estado/)).toBeInTheDocument();
    expect(screen.getByText("Confirmar cambio")).toBeInTheDocument();
  });

  it("calls onClose when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<StatusWorkflowModal {...DEFAULT_PROPS} onClose={onClose} />);

    await user.click(screen.getByText("Cancelar"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("calls API and onStatusChanged on successful transition", async () => {
    const user = userEvent.setup();
    const onStatusChanged = vi.fn();
    const onClose = vi.fn();
    vi.mocked(api.patch).mockResolvedValueOnce({ status: "available" });

    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        onStatusChanged={onStatusChanged}
        onClose={onClose}
      />
    );

    // Select "Disponible" transition
    const transitionButtons = screen.getAllByRole("button");
    const disponibleButton = transitionButtons.find((b) =>
      b.textContent?.includes("Disponible")
    );
    await user.click(disponibleButton!);

    // Confirm
    await user.click(screen.getByText("Confirmar cambio"));

    expect(api.patch).toHaveBeenCalledWith("/animals/test-uuid-123", {
      status: "available",
    });
    expect(onStatusChanged).toHaveBeenCalledWith("available");
    expect(onClose).toHaveBeenCalled();
  });

  it("shows error message on API failure", async () => {
    const user = userEvent.setup();
    const { ApiClientError } = await import("@/lib/api");
    vi.mocked(api.patch).mockRejectedValueOnce(
      new ApiClientError("fail", 422, "Transicion invalida")
    );

    render(<StatusWorkflowModal {...DEFAULT_PROPS} />);

    // Select transition
    const transitionButtons = screen.getAllByRole("button");
    const disponibleButton = transitionButtons.find((b) =>
      b.textContent?.includes("Disponible")
    );
    await user.click(disponibleButton!);

    // Confirm
    await user.click(screen.getByText("Confirmar cambio"));

    expect(
      await screen.findByText("Transicion invalida")
    ).toBeInTheDocument();
  });

  it("shows terminal state warning for deceased target", async () => {
    const user = userEvent.setup();
    render(
      <StatusWorkflowModal
        {...DEFAULT_PROPS}
        currentStatus="quarantine"
      />
    );

    // Deceased should be a valid transition from quarantine
    const transitionButtons = screen.getAllByRole("button");
    const deceasedButton = transitionButtons.find((b) =>
      b.textContent?.includes("Fallecido")
    );
    expect(deceasedButton).toBeDefined();
    await user.click(deceasedButton!);

    expect(
      screen.getByText(/No se podra revertir/)
    ).toBeInTheDocument();
  });

  it("closes modal when clicking the backdrop", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<StatusWorkflowModal {...DEFAULT_PROPS} onClose={onClose} />);

    // Click the backdrop (the dialog overlay)
    const dialog = screen.getByRole("dialog");
    await user.click(dialog);
    expect(onClose).toHaveBeenCalled();
  });
});

describe("VALID_TRANSITIONS", () => {
  it("mirrors backend transition map", () => {
    // Verify key transition rules match backend
    expect(VALID_TRANSITIONS.intake).toContain("quarantine");
    expect(VALID_TRANSITIONS.intake).toContain("available");
    expect(VALID_TRANSITIONS.intake).not.toContain("adopted");

    expect(VALID_TRANSITIONS.available).toContain("adopted");
    expect(VALID_TRANSITIONS.available).toContain("foster");

    expect(VALID_TRANSITIONS.adopted).toEqual(["available"]);
    expect(VALID_TRANSITIONS.deceased).toEqual([]);
  });

  it("has entries for all animal statuses", () => {
    const allStatuses: AnimalStatus[] = [
      "intake",
      "quarantine",
      "available",
      "foster",
      "under_treatment",
      "adopted",
      "deceased",
    ];
    for (const status of allStatuses) {
      expect(VALID_TRANSITIONS).toHaveProperty(status);
    }
  });
});
