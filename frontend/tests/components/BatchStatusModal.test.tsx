import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import BatchStatusModal from "@/components/admin/BatchStatusModal";
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

const INTAKE_ANIMALS = [
  { id: "a1", name: "Luna", status: "intake" as AnimalStatus },
  { id: "a2", name: "Max", status: "intake" as AnimalStatus },
];

const MIXED_ANIMALS = [
  { id: "a1", name: "Luna", status: "intake" as AnimalStatus },
  { id: "a2", name: "Max", status: "available" as AnimalStatus },
];

const DEFAULT_PROPS = {
  animals: INTAKE_ANIMALS,
  onClose: vi.fn(),
  onBatchCompleted: vi.fn(),
};

describe("BatchStatusModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders the modal with selected count", () => {
    render(<BatchStatusModal {...DEFAULT_PROPS} />);
    expect(screen.getByText(/2/)).toBeInTheDocument();
    expect(screen.getByText(/animales seleccionados/)).toBeInTheDocument();
  });

  it("shows common transitions for same-status animals", () => {
    render(<BatchStatusModal {...DEFAULT_PROPS} />);
    // intake can go to: quarantine, available, under_treatment
    expect(screen.getByText("Cuarentena")).toBeInTheDocument();
    expect(screen.getByText("Disponible")).toBeInTheDocument();
    expect(screen.getByText("En tratamiento")).toBeInTheDocument();
  });

  it("shows only shared transitions for mixed-status animals", () => {
    render(
      <BatchStatusModal
        {...DEFAULT_PROPS}
        animals={MIXED_ANIMALS}
      />
    );
    // intake: quarantine, available, under_treatment
    // available: foster, adopted, under_treatment, quarantine, deceased
    // Common: quarantine, under_treatment
    expect(screen.getByText("Cuarentena")).toBeInTheDocument();
    expect(screen.getByText("En tratamiento")).toBeInTheDocument();
  });

  it("shows confirmation step when a transition is selected", async () => {
    const user = userEvent.setup();
    render(<BatchStatusModal {...DEFAULT_PROPS} />);

    const buttons = screen.getAllByRole("button");
    const disponibleBtn = buttons.find((b) => b.textContent?.includes("Disponible"));
    await user.click(disponibleBtn!);

    expect(screen.getByText(/Cambiar el estado de/)).toBeInTheDocument();
    expect(screen.getByText("2 animales")).toBeInTheDocument();
  });

  it("shows animal names in confirmation view", async () => {
    const user = userEvent.setup();
    render(<BatchStatusModal {...DEFAULT_PROPS} />);

    const buttons = screen.getAllByRole("button");
    const disponibleBtn = buttons.find((b) => b.textContent?.includes("Disponible"));
    await user.click(disponibleBtn!);

    expect(screen.getByText("Luna")).toBeInTheDocument();
    expect(screen.getByText("Max")).toBeInTheDocument();
  });

  it("calls API for each animal on confirm", async () => {
    const user = userEvent.setup();
    vi.mocked(api.patch).mockResolvedValue({});

    render(<BatchStatusModal {...DEFAULT_PROPS} />);

    // Select transition
    const buttons = screen.getAllByRole("button");
    const disponibleBtn = buttons.find((b) => b.textContent?.includes("Disponible"));
    await user.click(disponibleBtn!);

    // Confirm
    await user.click(screen.getByText("Confirmar cambio"));

    expect(api.patch).toHaveBeenCalledTimes(2);
    expect(api.patch).toHaveBeenCalledWith("/animals/a1", { status: "available" });
    expect(api.patch).toHaveBeenCalledWith("/animals/a2", { status: "available" });
  });

  it("calls onBatchCompleted with successful IDs", async () => {
    const user = userEvent.setup();
    const onBatchCompleted = vi.fn();
    vi.mocked(api.patch).mockResolvedValue({});

    render(
      <BatchStatusModal
        {...DEFAULT_PROPS}
        onBatchCompleted={onBatchCompleted}
      />
    );

    const buttons = screen.getAllByRole("button");
    const disponibleBtn = buttons.find((b) => b.textContent?.includes("Disponible"));
    await user.click(disponibleBtn!);
    await user.click(screen.getByText("Confirmar cambio"));

    expect(onBatchCompleted).toHaveBeenCalledWith(["a1", "a2"], "available");
  });

  it("shows results with failure details", async () => {
    const user = userEvent.setup();
    const { ApiClientError } = await import("@/lib/api");
    vi.mocked(api.patch)
      .mockResolvedValueOnce({})
      .mockRejectedValueOnce(new ApiClientError("fail", 422, "Transicion invalida"));

    render(<BatchStatusModal {...DEFAULT_PROPS} />);

    const buttons = screen.getAllByRole("button");
    const disponibleBtn = buttons.find((b) => b.textContent?.includes("Disponible"));
    await user.click(disponibleBtn!);
    await user.click(screen.getByText("Confirmar cambio"));

    // Should show results
    expect(await screen.findByText(/exitosos/)).toBeInTheDocument();
    expect(screen.getByText(/fallidos/)).toBeInTheDocument();
    expect(screen.getByText(/Transicion invalida/)).toBeInTheDocument();
  });

  it("calls onClose when cancel button is clicked", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<BatchStatusModal {...DEFAULT_PROPS} onClose={onClose} />);

    await user.click(screen.getByText("Cancelar"));
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("shows terminal state warning for deceased target", async () => {
    const user = userEvent.setup();
    render(
      <BatchStatusModal
        {...DEFAULT_PROPS}
        animals={[
          { id: "a1", name: "Luna", status: "quarantine" as AnimalStatus },
        ]}
      />
    );

    const buttons = screen.getAllByRole("button");
    const deceasedBtn = buttons.find((b) => b.textContent?.includes("Fallecido"));
    expect(deceasedBtn).toBeDefined();
    await user.click(deceasedBtn!);

    expect(screen.getByText(/No se podra revertir/)).toBeInTheDocument();
  });
});
