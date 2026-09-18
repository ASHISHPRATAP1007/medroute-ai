"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  LayoutDashboard, Users, Stethoscope, Building2, Truck, Map, ScrollText, Settings, BarChart3,
} from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import { useAuth } from "@/hooks/use-auth";

const NAV_ITEMS = [
  { href: "/admin/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/admin/mrs", label: "MR Management", icon: Users },
  { href: "/admin/doctors", label: "Doctors", icon: Stethoscope },
  { href: "/admin/medical-shops", label: "Medical Shops", icon: Building2 },
  { href: "/admin/stockists", label: "Stockists", icon: Truck },
  { href: "/admin/territories", label: "Territories", icon: Map },
  { href: "/admin/analytics", label: "Analytics", icon: BarChart3 },
  { href: "/admin/audit-logs", label: "Audit Logs", icon: ScrollText },
  { href: "/admin/settings", label: "Settings", icon: Settings },
];

export default function AdminLayout({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    // Frontend guard only — a UX convenience. The backend independently
    // enforces role/status on every request (see core/dependencies.py).
    if (!isLoading) {
      if (!user) router.replace("/login");
      else if (user.role !== "ADMIN" && user.role !== "SUPER_ADMIN") router.replace("/mr/dashboard");
    }
  }, [isLoading, user, router]);

  if (isLoading || !user) {
    return <div className="flex min-h-screen items-center justify-center text-sm text-slate-500">Loading…</div>;
  }

  return (
    <div className="flex min-h-screen bg-slate-50">
      <Sidebar items={NAV_ITEMS} open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar onMenuClick={() => setDrawerOpen(true)} />
        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}
