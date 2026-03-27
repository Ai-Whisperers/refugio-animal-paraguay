/**
 * Admin layout: standalone chrome for staff/admin pages.
 * No public Navbar/Footer — admin has its own minimal header.
 */

export default function AdminLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-warm-bg">
      {children}
    </div>
  );
}
