import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";

const { mockApiGet, mockApiPut } = vi.hoisted(() => ({
  mockApiGet: vi.fn(),
  mockApiPut: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: { get: mockApiGet, put: mockApiPut },
}));

vi.mock("@/lib/auth", () => ({
  isAuthenticated: vi.fn(() => true),
  getAccessToken: vi.fn(() => "mock-token"),
  decodeToken: vi.fn(() => ({ sub: "user-1", role: "admin", exp: 9999999999 })),
  clearAccessToken: vi.fn(),
}));

import NotificationPreferencesPage from "@/app/admin/settings/notifications/page";

const SAMPLE_PREFERENCES = {
  preferences: [
    { notification_type: "adoption_request_created", channel: "email", enabled: true },
    { notification_type: "adoption_request_created", channel: "in_app", enabled: false },
    { notification_type: "donation_received", channel: "email", enabled: true },
    { notification_type: "donation_received", channel: "in_app", enabled: true },
  ],
};

describe("NotificationPreferencesPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockApiGet.mockResolvedValue(SAMPLE_PREFERENCES);
    mockApiPut.mockResolvedValue({});
  });

  it("renders the page title", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      expect(screen.getByText("Notification Preferences")).toBeInTheDocument();
    });
  });

  it("shows a loading spinner while fetching", () => {
    mockApiGet.mockImplementation(() => new Promise(() => {})); // never resolves
    render(<NotificationPreferencesPage />);
    // Spinner present during loading
    expect(document.querySelector(".animate-spin")).toBeTruthy();
  });

  it("renders notification types as table rows", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      expect(screen.getByText("Adoption Application Received")).toBeInTheDocument();
      expect(screen.getByText("Donation Received")).toBeInTheDocument();
      expect(screen.getByText("System Alerts")).toBeInTheDocument();
    });
  });

  it("renders channel toggle buttons for each row", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      const switches = screen.getAllByRole("switch");
      // 8 notification types × 2 channels = 16 toggles
      expect(switches.length).toBe(16);
    });
  });

  it("reflects enabled=false from API as unchecked toggle", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      // adoption_request_created / in_app is disabled in sample data
      const switches = screen.getAllByRole("switch");
      const disabledSwitch = switches.find(
        (s) =>
          s.getAttribute("aria-label") ===
          "Enable Adoption Application Received via In-App"
      );
      expect(disabledSwitch).toBeTruthy();
      expect(disabledSwitch?.getAttribute("aria-checked")).toBe("false");
    });
  });

  it("toggles a preference when clicked", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      expect(screen.getByText("Adoption Application Received")).toBeInTheDocument();
    });

    const emailSwitch = screen.getByRole("switch", {
      name: /Disable Adoption Application Received via Email/i,
    });
    // Initially enabled — aria-checked true
    expect(emailSwitch.getAttribute("aria-checked")).toBe("true");

    fireEvent.click(emailSwitch);

    // After click, should toggle to false
    expect(emailSwitch.getAttribute("aria-checked")).toBe("false");
  });

  it("calls API PUT when save button is clicked", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      expect(screen.getByText("Save preferences")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Save preferences"));

    await waitFor(() => {
      expect(mockApiPut).toHaveBeenCalledWith(
        "/notification-preferences",
        expect.objectContaining({ preferences: expect.any(Array) }),
        expect.objectContaining({ requiresAuth: true })
      );
    });
  });

  it("shows success message after save", async () => {
    render(<NotificationPreferencesPage />);
    await waitFor(() => {
      expect(screen.getByText("Save preferences")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Save preferences"));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(
        "Preferences saved successfully."
      );
    });
  });

  it("shows error message when fetch fails", async () => {
    mockApiGet.mockRejectedValue(new Error("Network error"));
    render(<NotificationPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to load notification preferences"
      );
    });
  });

  it("shows error message when save fails", async () => {
    mockApiPut.mockRejectedValue(new Error("Server error"));
    render(<NotificationPreferencesPage />);

    await waitFor(() => {
      expect(screen.getByText("Save preferences")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText("Save preferences"));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Failed to save preferences"
      );
    });
  });
});
