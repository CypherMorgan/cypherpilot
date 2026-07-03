import { useState } from "react";
import { Outlet } from "react-router-dom";

import { Sidebar } from "@/layouts/sidebar";
import { Topbar } from "@/layouts/topbar";
import { BackendBanner } from "@/components/backend-banner";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Sheet,
  SheetContent,
  SheetTrigger,
} from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

/**
 * Root application layout.
 *
 * Provides the persistent shell: sidebar (desktop) + topbar + scrollable content area.
 * Uses React Router's <Outlet /> for child route rendering.
 *
 * On mobile (<1024px), the sidebar is hidden and toggled via a Sheet (drawer).
 */
export function RootLayout() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleSidebar = () => setSidebarCollapsed((prev) => !prev);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Desktop sidebar */}
      <div className="hidden lg:flex">
        <Sidebar collapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      </div>

      {/* Mobile sidebar (Sheet/drawer) */}
      <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
        <SheetTrigger asChild>
          <Button
            variant="ghost"
            size="icon"
            className="fixed left-4 top-3 z-40 lg:hidden"
            aria-label="Open navigation menu"
          >
            <Menu className="h-5 w-5" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <Sidebar collapsed={false} onToggle={() => setMobileMenuOpen(false)} />
        </SheetContent>
      </Sheet>

      {/* Main content area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <Topbar
          onMenuToggle={() => setMobileMenuOpen(true)}
        />

        <BackendBanner />

        <ScrollArea className="flex-1">
          <main className="flex-1">
            <Outlet />
          </main>
        </ScrollArea>
      </div>
    </div>
  );
}
