import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import UserActivityTimelinePage from "@/app/admin/audit-logs/user/[userId]/page";

const mockPush = vi.fn();
const mockReplace = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: vi.fn(() => ({
    push: mockPush,
    replace: mockReplace,
  })),
  useParams: vi.fn(() => ({
    userId: "bbbbbbbb-0000-0000-0000-000000000001",
  })),
}));

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
}));

const mockApiGet = vi.fn(() => new Promise(() => {}));

vi.mock("@/lib/api", () => ({
  api: {
    get: (...args: unknown[]) => mockApiGet(...args),
  },
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

const MOCK_RESPONSE = {
  items: [
    {
      id: "aaaaaaaa-0000-0000-0000-000000000001",
      user_id: "bbbbbbbb-0000-0000-0000-000000000001",
      action: "create",
      resource_type: "animal",
      resource_id: "cccc1111-0000-0000-0000-000000000001",
      timestamp: "2026-03-29T10:00:00Z",
      ip_address: "192.168.1.1",
      user_agent: "Mozilla/5.0",
      old_values: null,
      new_values: { name: "Firulais" },
      request_id: "req-001",
    },
    {
      id: "aaaaaaaa-0000-0000-0000-000000000002",
      user_id: "bbbbbbbb-0000-0000-0000-000000000001",
      action: "login",
      resource_type: "session",
      resource_id: null,
      timestamp: "2026-03-29T09:00:00Z",
      ip_address: "192.168.1.1",
      user_agent: null,
      old_values: null,
      new_values: null,
      request_id: null,
    },
  ],
  total: 2,
  page: 1,
  page_size: 30,
};

describe("UserActivityTimelinePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockReturnValue(new Promise(() => {}));
  });

  it("renders the page title", () => {
    render(<UserActivityTimelinePage />);
    expect(screen.getByText("Actividad del Usuario")).toBeDefined();
  });

  it("renders the user ID in header", () => {
    render(<UserActivityTimelinePage />);
    expect(
      screen.getByText("bbbbbbbb-0000-0000-0000-000000000001")
    ).toBeDefined();
  });

  it("renders loading state", () => {
    render(<UserActivityTimelinePage />);
    expect(screen.getByText("Cargando actividad...")).toBeDefined();
  });

  it("renders the back button", () => {
    render(<UserActivityTimelinePage />);
    expect(screen.getByLabelText("Volver a Auditoria")).toBeDefined();
  });

  it("renders timeline entries after successful fetch", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(screen.getByText("Creo")).toBeDefined();
    });
    expect(screen.getByText("Inicio sesion")).toBeDefined();
  });

  it("renders resource type in timeline", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(screen.getByText("animal")).toBeDefined();
    });
    expect(screen.getByText("session")).toBeDefined();
  });

  it("renders empty state when no entries", async () => {
    mockApiGet.mockResolvedValueOnce({
      items: [],
      total: 0,
      page: 1,
      page_size: 30,
    });
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(
        screen.getByText("Sin actividad registrada para este usuario")
      ).toBeDefined();
    });
  });

  it("renders error state on API failure", async () => {
    mockApiGet.mockRejectedValueOnce(new Error("Network error"));
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(
        screen.getByText("Error al cargar actividad del usuario")
      ).toBeDefined();
    });
    expect(screen.getByText("Reintentar")).toBeDefined();
  });

  it("passes user_id as query param in API call", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        expect.stringContaining("user_id=bbbbbbbb-0000-0000-0000-000000000001")
      );
    });
  });

  it("shows IP address in timeline entry when present", async () => {
    mockApiGet.mockResolvedValueOnce(MOCK_RESPONSE);
    render(<UserActivityTimelinePage />);

    await waitFor(() => {
      expect(screen.getAllByText("192.168.1.1").length).toBeGreaterThan(0);
    });
  });
});
