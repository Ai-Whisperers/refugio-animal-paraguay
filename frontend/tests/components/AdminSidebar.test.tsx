import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import AdminSidebar from "@/components/admin/AdminSidebar";

// Mock the auth module
vi.mock("@/lib/auth", () => ({
  clearAccessToken: vi.fn(),
  getCurrentUserRole: vi.fn(() => "staff"),
}));

// Import the mocked module so we can change return values per test
import { getCurrentUserRole } from "@/lib/auth";
const mockGetCurrentUserRole = vi.mocked(getCurrentUserRole);
const mockUsePathname = vi.mocked(usePathname);

const STAFF_VISIBLE_LABELS = ["Panel", "Animales", "Adopciones", "Donantes", "Donaciones"];
const ADMIN_ONLY_LABELS = ["Usuarios", "Configuracion"];

describe("AdminSidebar", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockUsePathname.mockReturnValue("/admin/dashboard");
  });

  describe("staff role", () => {
    beforeEach(() => {
      mockGetCurrentUserRole.mockReturnValue("staff");
    });

    it("renders all staff-permitted menu items", () => {
      render(<AdminSidebar />);
      for (const label of STAFF_VISIBLE_LABELS) {
        expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
      }
    });

    it("does not render admin-only menu items", () => {
      render(<AdminSidebar />);
      for (const label of ADMIN_ONLY_LABELS) {
        expect(screen.queryByText(label)).toBeNull();
      }
    });
  });

  describe("admin role", () => {
    beforeEach(() => {
      mockGetCurrentUserRole.mockReturnValue("admin");
    });

    it("renders all menu items including admin-only", () => {
      render(<AdminSidebar />);
      const allLabels = [...STAFF_VISIBLE_LABELS, ...ADMIN_ONLY_LABELS];
      for (const label of allLabels) {
        expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
      }
    });

    it("renders Usuarios menu item", () => {
      render(<AdminSidebar />);
      expect(screen.getAllByText("Usuarios").length).toBeGreaterThanOrEqual(1);
    });

    it("renders Configuracion menu item", () => {
      render(<AdminSidebar />);
      expect(screen.getAllByText("Configuracion").length).toBeGreaterThanOrEqual(1);
    });
  });

  describe("null role (unauthenticated or invalid token)", () => {
    beforeEach(() => {
      mockGetCurrentUserRole.mockReturnValue(null);
    });

    it("renders only items without requiredRole", () => {
      render(<AdminSidebar />);
      for (const label of STAFF_VISIBLE_LABELS) {
        expect(screen.getAllByText(label).length).toBeGreaterThanOrEqual(1);
      }
      for (const label of ADMIN_ONLY_LABELS) {
        expect(screen.queryByText(label)).toBeNull();
      }
    });
  });

  it("renders the shelter name", () => {
    mockGetCurrentUserRole.mockReturnValue("staff");
    render(<AdminSidebar />);
    expect(screen.getAllByText("Refugio Animal").length).toBeGreaterThanOrEqual(1);
  });

  it("renders the logout button", () => {
    mockGetCurrentUserRole.mockReturnValue("staff");
    render(<AdminSidebar />);
    expect(screen.getAllByText("Cerrar Sesion").length).toBeGreaterThanOrEqual(1);
  });
});
