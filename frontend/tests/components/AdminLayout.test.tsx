import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import AdminLayout from "@/app/admin/layout";

// Mock sidebar and breadcrumbs to isolate layout testing
vi.mock("@/components/admin/AdminSidebar", () => ({
  default: () => <div data-testid="admin-sidebar">Sidebar</div>,
}));

vi.mock("@/components/admin/Breadcrumbs", () => ({
  default: () => <div data-testid="breadcrumbs">Breadcrumbs</div>,
}));

const mockUsePathname = vi.mocked(usePathname);

describe("AdminLayout", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("authenticated admin pages", () => {
    beforeEach(() => {
      mockUsePathname.mockReturnValue("/admin/dashboard");
    });

    it("renders sidebar and main content area", () => {
      render(
        <AdminLayout>
          <div>Page Content</div>
        </AdminLayout>
      );
      expect(screen.getByTestId("admin-sidebar")).toBeDefined();
      expect(screen.getByText("Page Content")).toBeDefined();
    });

    it("main content has mobile-friendly padding with pt-16 for hamburger clearance", () => {
      const { container } = render(
        <AdminLayout>
          <div>Page Content</div>
        </AdminLayout>
      );
      const main = container.querySelector("main");
      expect(main).not.toBeNull();
      expect(main?.className).toContain("pt-16");
      expect(main?.className).toContain("md:p-6");
    });

    it("main content has compact horizontal padding on mobile", () => {
      const { container } = render(
        <AdminLayout>
          <div>Page Content</div>
        </AdminLayout>
      );
      const main = container.querySelector("main");
      expect(main?.className).toContain("px-4");
    });

    it("renders breadcrumbs inside main", () => {
      render(
        <AdminLayout>
          <div>Page Content</div>
        </AdminLayout>
      );
      expect(screen.getByTestId("breadcrumbs")).toBeDefined();
    });
  });

  describe("auth pages", () => {
    it("renders without sidebar for login page", () => {
      mockUsePathname.mockReturnValue("/admin/login");
      render(
        <AdminLayout>
          <div>Login Form</div>
        </AdminLayout>
      );
      expect(screen.queryByTestId("admin-sidebar")).toBeNull();
      expect(screen.getByText("Login Form")).toBeDefined();
    });

    it("renders without sidebar for forgot-password page", () => {
      mockUsePathname.mockReturnValue("/admin/forgot-password");
      render(
        <AdminLayout>
          <div>Forgot Password</div>
        </AdminLayout>
      );
      expect(screen.queryByTestId("admin-sidebar")).toBeNull();
    });
  });
});
