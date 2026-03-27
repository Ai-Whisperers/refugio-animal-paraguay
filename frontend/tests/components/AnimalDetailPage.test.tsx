import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi, beforeEach } from "vitest";
import type { Animal, AnimalStatus } from "@/types/api";

// Mock next/navigation
const mockPush = vi.fn();
const mockReplace = vi.fn();
vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: mockReplace }),
  useParams: () => ({ id: "test-animal-id" }),
}));

// Mock auth
vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "test-token"),
}));

// Mock API
vi.mock("@/lib/api", () => ({
  api: {
    get: vi.fn(),
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
import { isAuthenticated } from "@/lib/auth";
import AnimalDetailPage from "@/app/admin/animals/[id]/page";

const MOCK_ANIMAL: Animal = {
  id: "test-animal-id",
  name: "Luna",
  species: "dog",
  status: "available" as AnimalStatus,
  breed: "Mestiza",
  size: "medium",
  gender: "female",
  birth_date: "2023-06-15",
  description: "Luna es una perra muy cariñosa y juguetona.",
  primary_photo_url: "https://example.com/luna.jpg",
  photos: [
    {
      id: "photo-1",
      animal_id: "test-animal-id",
      url: "https://example.com/luna1.jpg",
      caption: "Luna jugando",
      display_order: 1,
      created_at: "2024-01-15T10:00:00Z",
    },
    {
      id: "photo-2",
      animal_id: "test-animal-id",
      url: "https://example.com/luna2.jpg",
      caption: null,
      display_order: 2,
      created_at: "2024-01-16T10:00:00Z",
    },
  ],
  created_at: "2024-01-10T10:00:00Z",
  updated_at: "2024-03-20T15:30:00Z",
};

describe("AnimalDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(isAuthenticated).mockReturnValue(true);
    vi.mocked(api.get).mockResolvedValue(MOCK_ANIMAL);
  });

  it("shows loading state initially", () => {
    // Don't resolve the API call yet
    vi.mocked(api.get).mockReturnValue(new Promise(() => {}));
    render(<AnimalDetailPage />);
    expect(screen.getByText("Cargando animal...")).toBeInTheDocument();
  });

  it("fetches and displays animal name", async () => {
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Luna")).toBeInTheDocument();
  });

  it("displays animal status badge", async () => {
    render(<AnimalDetailPage />);
    const badges = await screen.findAllByText("Disponible");
    expect(badges.length).toBeGreaterThan(0);
  });

  it("displays species info", async () => {
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Perro")).toBeInTheDocument();
  });

  it("displays breed info", async () => {
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Mestiza")).toBeInTheDocument();
  });

  it("displays size info", async () => {
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Mediano")).toBeInTheDocument();
  });

  it("displays gender info", async () => {
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Hembra")).toBeInTheDocument();
  });

  it("displays description", async () => {
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText(/Luna es una perra muy cariñosa/)
    ).toBeInTheDocument();
  });

  it("displays primary photo", async () => {
    render(<AnimalDetailPage />);
    const images = await screen.findAllByAltText("Luna");
    const primaryImg = images.find(
      (img) => img.getAttribute("src") === "https://example.com/luna.jpg"
    );
    expect(primaryImg).toBeDefined();
  });

  it("displays photo gallery", async () => {
    render(<AnimalDetailPage />);
    const galleryImg = await screen.findByAltText("Luna jugando");
    expect(galleryImg).toBeInTheDocument();
  });

  it("displays timeline with created event", async () => {
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText("Ingresado al sistema")
    ).toBeInTheDocument();
  });

  it("displays timeline with updated event when dates differ", async () => {
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText(/Ultima modificacion registrada/)
    ).toBeInTheDocument();
  });

  it("shows change status button for non-terminal status", async () => {
    render(<AnimalDetailPage />);
    const buttons = await screen.findAllByText("Cambiar Estado");
    expect(buttons.length).toBeGreaterThan(0);
  });

  it("hides change status button for terminal status (deceased)", async () => {
    vi.mocked(api.get).mockResolvedValue({
      ...MOCK_ANIMAL,
      status: "deceased",
    });
    render(<AnimalDetailPage />);
    await screen.findByText("Luna");
    expect(screen.queryByText("Cambiar Estado")).not.toBeInTheDocument();
  });

  it("shows edit button", async () => {
    render(<AnimalDetailPage />);
    const editButtons = await screen.findAllByText("Editar");
    expect(editButtons.length).toBeGreaterThan(0);
  });

  it("navigates to edit page when edit button is clicked", async () => {
    const user = userEvent.setup();
    render(<AnimalDetailPage />);
    const editButtons = await screen.findAllByText("Editar");
    await user.click(editButtons[0]);
    expect(mockPush).toHaveBeenCalledWith(
      "/admin/animals/test-animal-id/edit"
    );
  });

  it("shows back button that navigates to list", async () => {
    const user = userEvent.setup();
    render(<AnimalDetailPage />);
    await screen.findByText("Luna");
    const backButton = screen.getByLabelText("Volver a la lista");
    await user.click(backButton);
    expect(mockPush).toHaveBeenCalledWith("/admin/animals");
  });

  it("shows error state on API failure", async () => {
    const { ApiClientError } = await import("@/lib/api");
    vi.mocked(api.get).mockRejectedValue(
      new ApiClientError("fail", 500, "Server error")
    );
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText(/Error al cargar el animal/)
    ).toBeInTheDocument();
  });

  it("shows not found state on 404", async () => {
    const { ApiClientError } = await import("@/lib/api");
    vi.mocked(api.get).mockRejectedValue(
      new ApiClientError("not found", 404, "Animal not found")
    );
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText("Animal no encontrado")
    ).toBeInTheDocument();
  });

  it("redirects to login when not authenticated", () => {
    vi.mocked(isAuthenticated).mockReturnValue(false);
    render(<AnimalDetailPage />);
    expect(mockReplace).toHaveBeenCalledWith("/admin/login?expired=true");
  });

  it("shows empty photo gallery message when no photos", async () => {
    vi.mocked(api.get).mockResolvedValue({
      ...MOCK_ANIMAL,
      photos: [],
    });
    render(<AnimalDetailPage />);
    expect(
      await screen.findByText("No hay fotos registradas")
    ).toBeInTheDocument();
  });

  it("shows no description placeholder when description is null", async () => {
    vi.mocked(api.get).mockResolvedValue({
      ...MOCK_ANIMAL,
      description: null,
    });
    render(<AnimalDetailPage />);
    expect(await screen.findByText("Sin descripcion")).toBeInTheDocument();
  });
});
