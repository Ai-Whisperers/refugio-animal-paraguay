import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mock api client — use vi.hoisted so mockApiGet is available inside the factory
// ---------------------------------------------------------------------------

const { mockApiGet } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: { get: mockApiGet },
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

import OperationalDashboardPage from "@/app/admin/operational-dashboard/page";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const BASE_METRICS = {
  generated_at: "2026-03-29T10:00:00Z",
  population: {
    intake: 5,
    quarantine: 10,
    available: 40,
    foster: 8,
    under_treatment: 7,
    adopted: 120,
    deceased: 3,
    total: 70,
  },
  occupancy: {
    current_count: 70,
    capacity: 200,
    occupancy_rate_pct: 35.0,
  },
  period: {
    period_days: 30,
    intake_count: 15,
    outcome_count: 12,
  },
  species: {
    dog: 45,
    cat: 20,
    other: 5,
  },
  avg_los_days: 18.5,
};

const HIGH_OCCUPANCY_METRICS = {
  ...BASE_METRICS,
  occupancy: {
    current_count: 180,
    capacity: 200,
    occupancy_rate_pct: 90.0,
  },
};

const MODERATE_OCCUPANCY_METRICS = {
  ...BASE_METRICS,
  occupancy: {
    current_count: 150,
    capacity: 200,
    occupancy_rate_pct: 75.0,
  },
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("OperationalDashboardPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockResolvedValue(BASE_METRICS);
  });

  it("renders the page title", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Dashboard Operacional")).toBeInTheDocument();
    });
  });

  it("shows loading skeleton initially", () => {
    // Keep api pending
    mockApiGet.mockReturnValue(new Promise(() => {}));
    const { container } = render(<OperationalDashboardPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("displays occupancy rate KPI card", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("35%")).toBeInTheDocument();
    });
  });

  it("displays intake count KPI card", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("15")).toBeInTheDocument();
    });
  });

  it("displays outcome count KPI card", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("12")).toBeInTheDocument();
    });
  });

  it("displays average length of stay", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("18.5d")).toBeInTheDocument();
    });
  });

  it("displays population breakdown section", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Poblacion por Estado")).toBeInTheDocument();
    });
  });

  it("displays population status labels", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Disponible")).toBeInTheDocument();
      expect(screen.getByText("Cuarentena")).toBeInTheDocument();
      expect(screen.getByText("Ingreso")).toBeInTheDocument();
    });
  });

  it("displays species breakdown section", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Distribucion por Especie")).toBeInTheDocument();
    });
  });

  it("displays species counts", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Perros")).toBeInTheDocument();
      expect(screen.getByText("Gatos")).toBeInTheDocument();
      expect(screen.getByText("Otros")).toBeInTheDocument();
    });
  });

  it("shows adopted and deceased summary", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/120 adoptados/)).toBeInTheDocument();
      expect(screen.getByText(/3 fallecidos/)).toBeInTheDocument();
    });
  });

  it("shows capacity alert for high occupancy", async () => {
    mockApiGet.mockResolvedValue(HIGH_OCCUPANCY_METRICS);
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Alerta de capacidad/)).toBeInTheDocument();
    });
  });

  it("shows moderate capacity warning", async () => {
    mockApiGet.mockResolvedValue(MODERATE_OCCUPANCY_METRICS);
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Capacidad moderada/)).toBeInTheDocument();
    });
  });

  it("does not show alert for normal occupancy", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.queryByText(/Alerta de capacidad/)).not.toBeInTheDocument();
      expect(screen.queryByText(/Capacidad moderada/)).not.toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Error al cargar/)).toBeInTheDocument();
    });
  });

  it("shows retry button on error", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Reintentar")).toBeInTheDocument();
    });
  });

  it("refetches on retry button click", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    mockApiGet.mockResolvedValueOnce(BASE_METRICS);
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText("Reintentar")).toBeInTheDocument();
    });
    fireEvent.click(screen.getByText("Reintentar"));
    await waitFor(() => {
      expect(screen.getByText("Dashboard Operacional")).toBeInTheDocument();
    });
    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  it("renders period selector with default 30 days", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      const select = screen.getByRole("combobox", { name: /Periodo de analisis/ });
      expect(select).toBeInTheDocument();
    });
  });

  it("shows Actualizar button", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Actualizar datos/ })).toBeInTheDocument();
    });
  });

  it("calls api with correct period_days parameter", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("period_days=30")
      );
    });
  });

  it("shows capacity current vs total", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/70 \/ 200 lugares/)).toBeInTheDocument();
    });
  });

  it("shows occupancy progress bar with aria attributes", async () => {
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      const bar = screen.getByRole("progressbar");
      expect(bar).toHaveAttribute("aria-valuenow", "35");
    });
  });

  it("shows 401 specific error message", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApiGet.mockRejectedValue(new ApiClientError("Unauthorized", 401, "Unauthorized"));
    render(<OperationalDashboardPage />);
    await waitFor(() => {
      expect(screen.getByText(/Sesion expirada/)).toBeInTheDocument();
    });
  });
});
