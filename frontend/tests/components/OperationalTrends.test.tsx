import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

// ---------------------------------------------------------------------------
// Mocks
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

// recharts uses ResizeObserver — polyfill for jsdom
vi.stubGlobal("ResizeObserver", class {
  observe() {}
  unobserve() {}
  disconnect() {}
});

import OperationalTrendsPage from "@/app/admin/operational-dashboard/trends/page";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

const BASE_TRENDS: {
  interval: string;
  lookback_days: number;
  generated_at: string;
  data_points: { period_label: string; intake_count: number; outcome_count: number }[];
} = {
  interval: "monthly",
  lookback_days: 365,
  generated_at: "2026-03-29T10:00:00Z",
  data_points: [
    { period_label: "Ene 2026", intake_count: 20, outcome_count: 15 },
    { period_label: "Feb 2026", intake_count: 25, outcome_count: 18 },
    { period_label: "Mar 2026", intake_count: 30, outcome_count: 22 },
  ],
};

const EMPTY_TRENDS = {
  ...BASE_TRENDS,
  data_points: [],
};

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("OperationalTrendsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockResolvedValue(BASE_TRENDS);
  });

  it("renders the page title", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText("Tendencias de Ingresos y Egresos")).toBeInTheDocument();
    });
  });

  it("shows loading skeleton initially", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    const { container } = render(<OperationalTrendsPage />);
    expect(container.querySelector(".animate-pulse")).toBeInTheDocument();
  });

  it("displays total intake summary", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText("Ingresos totales")).toBeInTheDocument();
      // sum of 20+25+30 = 75
      expect(screen.getByText("75")).toBeInTheDocument();
    });
  });

  it("displays total outcome summary", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText("Egresos totales")).toBeInTheDocument();
      // sum of 15+18+22 = 55
      expect(screen.getByText("55")).toBeInTheDocument();
    });
  });

  it("shows the chart heading", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      // Matches the h2 "Tendencia Mensual (365 dias)" — distinct from h1
      expect(screen.getByText(/Tendencia Mensual/)).toBeInTheDocument();
    });
  });

  it("shows interval toggle buttons", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText("Diario")).toBeInTheDocument();
      expect(screen.getByText("Semanal")).toBeInTheDocument();
      expect(screen.getByText("Mensual")).toBeInTheDocument();
    });
  });

  it("shows Actualizar button", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByRole("button", { name: /Actualizar datos/ })).toBeInTheDocument();
    });
  });

  it("shows empty state when no data points", async () => {
    mockApiGet.mockResolvedValue(EMPTY_TRENDS);
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/No hay datos/)).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/Error al cargar/)).toBeInTheDocument();
    });
  });

  it("shows retry button on error", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText("Reintentar")).toBeInTheDocument();
    });
  });

  it("shows 401 specific error message", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApiGet.mockRejectedValue(new ApiClientError("Unauthorized", 401, "Unauthorized"));
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/Sesion expirada/)).toBeInTheDocument();
    });
  });

  it("calls api with monthly interval by default", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("interval=monthly")
      );
    });
  });

  it("calls api with correct lookback_days for monthly", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("lookback_days=365")
      );
    });
  });

  it("switches to daily interval on button click", async () => {
    mockApiGet.mockResolvedValue(BASE_TRENDS);
    render(<OperationalTrendsPage />);
    await waitFor(() => screen.getByText("Diario"));
    fireEvent.click(screen.getByText("Diario"));
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("interval=daily")
      );
    });
  });

  it("switches to weekly interval on button click", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => screen.getByText("Semanal"));
    fireEvent.click(screen.getByText("Semanal"));
    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("interval=weekly")
      );
    });
  });

  it("shows period count in subtitle", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/3 periodos/)).toBeInTheDocument();
    });
  });

  it("shows historical lookback days in subtitle", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/365 dias de historial/)).toBeInTheDocument();
    });
  });

  it("shows footer note about data methodology", async () => {
    render(<OperationalTrendsPage />);
    await waitFor(() => {
      expect(screen.getByText(/fecha de creacion/)).toBeInTheDocument();
    });
  });

  it("retry button refetches data", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    mockApiGet.mockResolvedValueOnce(BASE_TRENDS);
    render(<OperationalTrendsPage />);
    await waitFor(() => screen.getByText("Reintentar"));
    fireEvent.click(screen.getByText("Reintentar"));
    await waitFor(() => {
      expect(screen.getByText("Tendencias de Ingresos y Egresos")).toBeInTheDocument();
    });
    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });
});
