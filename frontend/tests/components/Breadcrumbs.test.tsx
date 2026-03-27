import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { usePathname } from "next/navigation";
import Breadcrumbs, { buildBreadcrumbs } from "@/components/admin/Breadcrumbs";

const mockUsePathname = vi.mocked(usePathname);

describe("buildBreadcrumbs", () => {
  it("returns correct items for /admin/animals", () => {
    const items = buildBreadcrumbs("/admin/animals");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Animales", href: "/admin/animals" },
    ]);
  });

  it("returns correct items for /admin/animals/123/edit", () => {
    const items = buildBreadcrumbs("/admin/animals/123/edit");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Animales", href: "/admin/animals" },
      { label: "Detalle", href: "/admin/animals/123" },
      { label: "Editar", href: "/admin/animals/123/edit" },
    ]);
  });

  it("handles UUID segments as Detalle", () => {
    const items = buildBreadcrumbs("/admin/donors/550e8400-e29b-41d4-a716-446655440000");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Donantes", href: "/admin/donors" },
      { label: "Detalle", href: "/admin/donors/550e8400-e29b-41d4-a716-446655440000" },
    ]);
  });

  it("uses Spanish labels for known segments", () => {
    const items = buildBreadcrumbs("/admin/adoptions/analytics");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Adopciones", href: "/admin/adoptions" },
      { label: "Analiticas", href: "/admin/adoptions/analytics" },
    ]);
  });

  it("title-cases unknown segments", () => {
    const items = buildBreadcrumbs("/admin/reports");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Reports", href: "/admin/reports" },
    ]);
  });

  it("returns single item for /admin", () => {
    const items = buildBreadcrumbs("/admin");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
    ]);
  });

  it("handles /admin/dashboard", () => {
    const items = buildBreadcrumbs("/admin/dashboard");
    expect(items).toEqual([
      { label: "Admin", href: "/admin" },
      { label: "Panel", href: "/admin/dashboard" },
    ]);
  });
});

describe("Breadcrumbs component", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing for /admin (too shallow)", () => {
    mockUsePathname.mockReturnValue("/admin");
    const { container } = render(<Breadcrumbs />);
    expect(container.innerHTML).toBe("");
  });

  it("renders nothing for /admin/dashboard (only 2 segments)", () => {
    mockUsePathname.mockReturnValue("/admin/dashboard");
    const { container } = render(<Breadcrumbs />);
    expect(container.innerHTML).toBe("");
  });

  it("renders breadcrumbs for /admin/animals/123", () => {
    mockUsePathname.mockReturnValue("/admin/animals/123");
    render(<Breadcrumbs />);
    expect(screen.getByText("Animales")).toBeInTheDocument();
    expect(screen.getByText("Detalle")).toBeInTheDocument();
  });

  it("renders the last item as non-clickable text", () => {
    mockUsePathname.mockReturnValue("/admin/animals/123/edit");
    render(<Breadcrumbs />);
    const editText = screen.getByText("Editar");
    expect(editText.tagName).toBe("SPAN");
    expect(editText).toHaveAttribute("aria-current", "page");
  });

  it("renders intermediate items as links", () => {
    mockUsePathname.mockReturnValue("/admin/animals/123/edit");
    render(<Breadcrumbs />);
    const animalsLink = screen.getByText("Animales");
    expect(animalsLink.closest("a")).toHaveAttribute("href", "/admin/animals");
  });

  it("renders a home icon link at the start", () => {
    mockUsePathname.mockReturnValue("/admin/animals/123");
    render(<Breadcrumbs />);
    const homeLink = screen.getByRole("link", { name: /admin/i });
    expect(homeLink).toHaveAttribute("href", "/admin/dashboard");
  });

  it("has proper aria-label on the nav element", () => {
    mockUsePathname.mockReturnValue("/admin/animals/123");
    render(<Breadcrumbs />);
    expect(screen.getByLabelText("Breadcrumb")).toBeInTheDocument();
  });
});
