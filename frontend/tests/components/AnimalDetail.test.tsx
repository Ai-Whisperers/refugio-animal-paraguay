import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { useParams } from "next/navigation";

// Mock modules before importing component
vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
}));

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

vi.mock("@/components/admin/StatusWorkflowModal", () => ({
  default: () => <div data-testid="status-workflow-modal">StatusWorkflowModal</div>,
}));

import AnimalDetailPage from "@/app/admin/animals/[id]/page";

const mockUseParams = vi.mocked(useParams);

describe("AnimalDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUseParams.mockReturnValue({ id: "animal-123" });
  });

  it("renders loading state initially", () => {
    render(<AnimalDetailPage />);
    expect(screen.getByText("Cargando animal...")).toBeDefined();
  });

  it("shows loading text with spinner", () => {
    const { container } = render(<AnimalDetailPage />);
    expect(screen.getByText("Cargando animal...")).toBeDefined();
    const spinner = container.querySelector(".animate-spin");
    expect(spinner).not.toBeNull();
  });
});
