import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import type { PaginatedVolunteerList } from "@/types/api";

// next/navigation is already globally mocked in tests/setup.ts

const mockApiGet = vi.fn();

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "mock-token"),
}));

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockApiGet(...args),
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

import VolunteerDirectoryPage from "@/app/admin/volunteers/directory/page";

// --- Helpers ---

function makeApprovedList(overrides: Partial<PaginatedVolunteerList> = {}): PaginatedVolunteerList {
  return {
    items: [
      {
        id: "vol-1",
        user_id: "user-1",
        full_name: "Ana Lopez",
        email: "ana@example.com",
        status: "approved",
        skills: ["animal_care", "photography"],
        hours_per_week: 8,
        created_at: "2025-01-15T10:00:00Z",
      },
      {
        id: "vol-2",
        user_id: "user-2",
        full_name: "Carlos Ruiz",
        email: "carlos@example.com",
        status: "approved",
        skills: ["transport_driving"],
        hours_per_week: 4,
        created_at: "2025-02-20T10:00:00Z",
      },
    ],
    total: 2,
    page: 1,
    page_size: 100,
    ...overrides,
  };
}

function makeInactiveList(overrides: Partial<PaginatedVolunteerList> = {}): PaginatedVolunteerList {
  return {
    items: [
      {
        id: "vol-3",
        user_id: "user-3",
        full_name: "Maria Torres",
        email: "maria@example.com",
        status: "inactive",
        skills: ["social_media"],
        hours_per_week: null,
        created_at: "2024-12-01T10:00:00Z",
      },
    ],
    total: 1,
    page: 1,
    page_size: 100,
    ...overrides,
  };
}

function makeEmptyList(): PaginatedVolunteerList {
  return { items: [], total: 0, page: 1, page_size: 100 };
}

// --- Tests ---

describe("VolunteerDirectoryPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders page title", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByText("Directorio de Voluntarios")).toBeInTheDocument();
  });

  it("renders subtitle", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByText("Voluntarios activos del refugio")).toBeInTheDocument();
  });

  it("renders loading state while fetching", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByText("Cargando directorio...")).toBeInTheDocument();
  });

  it("renders search input", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(
      screen.getByPlaceholderText("Buscar por nombre o correo...")
    ).toBeInTheDocument();
  });

  it("renders skill filter dropdown", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByLabelText("Filtrar por habilidad")).toBeInTheDocument();
  });

  it("renders status filter dropdown", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByLabelText("Estado")).toBeInTheDocument();
  });

  it("renders back button", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByLabelText("Volver a solicitudes")).toBeInTheDocument();
  });

  it("renders refresh button", () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<VolunteerDirectoryPage />);
    expect(screen.getByLabelText("Reintentar")).toBeInTheDocument();
  });

  it("renders volunteer cards after successful load", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    expect(await screen.findByText("Ana Lopez")).toBeInTheDocument();
    expect(screen.getByText("Carlos Ruiz")).toBeInTheDocument();
    expect(screen.getByText("Maria Torres")).toBeInTheDocument();
  });

  it("renders volunteer email in card", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    expect(await screen.findByText("ana@example.com")).toBeInTheDocument();
  });

  it("renders volunteer skill tags", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    // Skills appear in both the filter dropdown and the card tags — use getAllByText
    await screen.findByText("Ana Lopez");
    expect(screen.getAllByText("Cuidado animal").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("Fotografia").length).toBeGreaterThanOrEqual(1);
  });

  it("shows result count after load", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    expect(await screen.findByText("3 voluntarios encontrados")).toBeInTheDocument();
  });

  it("renders error state on API failure", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApiGet.mockRejectedValue(
      new ApiClientError("Server error", 500, "Fallo del servidor")
    );

    render(<VolunteerDirectoryPage />);

    expect(await screen.findByText("Error al cargar el directorio")).toBeInTheDocument();
  });

  it("shows retry link in error state", async () => {
    const { ApiClientError } = await import("@/lib/api");
    mockApiGet.mockRejectedValue(
      new ApiClientError("Server error", 500, "Fallo del servidor")
    );

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Error al cargar el directorio");
    expect(screen.getByText("Reintentar")).toBeInTheDocument();
  });

  it("renders empty state when no volunteers found", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeEmptyList())
      .mockResolvedValueOnce(makeEmptyList());

    render(<VolunteerDirectoryPage />);

    expect(
      await screen.findByText("No hay voluntarios en el directorio")
    ).toBeInTheDocument();
  });

  it("filters volunteers by name search", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const searchInput = screen.getByPlaceholderText("Buscar por nombre o correo...");
    fireEvent.change(searchInput, { target: { value: "carlos" } });

    expect(screen.queryByText("Ana Lopez")).not.toBeInTheDocument();
    expect(screen.getByText("Carlos Ruiz")).toBeInTheDocument();
  });

  it("filters volunteers by email search", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const searchInput = screen.getByPlaceholderText("Buscar por nombre o correo...");
    fireEvent.change(searchInput, { target: { value: "maria@example" } });

    expect(screen.queryByText("Ana Lopez")).not.toBeInTheDocument();
    expect(screen.getByText("Maria Torres")).toBeInTheDocument();
  });

  it("shows empty filtered state when search has no matches", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const searchInput = screen.getByPlaceholderText("Buscar por nombre o correo...");
    fireEvent.change(searchInput, { target: { value: "zzz-no-match-xyz" } });

    expect(
      screen.getByText("Ningun voluntario coincide con los filtros")
    ).toBeInTheDocument();
  });

  it("shows clear filters button when search is active", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const searchInput = screen.getByPlaceholderText("Buscar por nombre o correo...");
    fireEvent.change(searchInput, { target: { value: "ana" } });

    expect(screen.getByText("Limpiar filtros")).toBeInTheDocument();
  });

  it("clears filters and shows all volunteers when clear is clicked", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const searchInput = screen.getByPlaceholderText("Buscar por nombre o correo...");
    fireEvent.change(searchInput, { target: { value: "ana" } });

    expect(screen.queryByText("Carlos Ruiz")).not.toBeInTheDocument();

    const clearBtn = screen.getByText("Limpiar filtros");
    fireEvent.click(clearBtn);

    expect(screen.getByText("Ana Lopez")).toBeInTheDocument();
    expect(screen.getByText("Carlos Ruiz")).toBeInTheDocument();
  });

  it("filters by approved status only", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Maria Torres");

    const statusSelect = screen.getByLabelText("Estado");
    fireEvent.change(statusSelect, { target: { value: "approved" } });

    expect(screen.queryByText("Maria Torres")).not.toBeInTheDocument();
    expect(screen.getByText("Ana Lopez")).toBeInTheDocument();
    expect(screen.getByText("Carlos Ruiz")).toBeInTheDocument();
  });

  it("filters by inactive status only", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Maria Torres");

    const statusSelect = screen.getByLabelText("Estado");
    fireEvent.change(statusSelect, { target: { value: "inactive" } });

    expect(screen.queryByText("Ana Lopez")).not.toBeInTheDocument();
    expect(screen.getByText("Maria Torres")).toBeInTheDocument();
  });

  it("renders profile view button for each volunteer", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeEmptyList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    const viewButtons = screen.getAllByText("Ver perfil");
    expect(viewButtons).toHaveLength(2);
  });

  it("makes two API calls on load (approved + inactive)", async () => {
    mockApiGet
      .mockResolvedValueOnce(makeApprovedList())
      .mockResolvedValueOnce(makeInactiveList());

    render(<VolunteerDirectoryPage />);

    await screen.findByText("Ana Lopez");

    expect(mockApiGet).toHaveBeenCalledTimes(2);
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining("status=approved")
    );
    expect(mockApiGet).toHaveBeenCalledWith(
      expect.stringContaining("status=inactive")
    );
  });
});
