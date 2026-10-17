"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { LayoutDashboard, Stethoscope, Building2, Truck, Map, UserCircle, Sparkles, CalendarCheck, Route, Compass } from "lucide-react";
import Sidebar from "@/components/layout/Sidebar";
import Topbar from "@/components/layout/Topbar";
import MobileBottomNav from "@/components/layout/MobileBottomNav";
import { useAuth } from "@/hooks/use-auth";

const BOTTOM_NAV_ITEMS = [
  { href: "/mr/dashboard", label: "Home", icon: LayoutDashboard },
  { href: "/mr/doctors", label: "Doctors", icon: Stethoscope },
  { href: "/mr/explore", label: "Explore", icon: Compass },
  { href: "/mr/ai/daily-plan", label: "AI Plan", icon: Sparkles },
  // "Visits" stays highlighted on /mr/visits/route too. Profile is in the menu drawer.
  { href: "/mr/visits", label: "Visits", icon: CalendarCheck },
];

const NAV_ITEMS = [
  { href: "/mr/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mr/ai/daily-plan", label: "AI Daily Plan", icon: Sparkles },
  { href: "/mr/doctors", label: "Doctors", icon: Stethoscope },
  { href: "/mr/explore", label: "Explore Any Area", icon: Compass },
  { href: "/mr/visits", label: "My Visits", icon: CalendarCheck },
  { href: "/mr/visits/route", label: "Daily Route", icon: Route },
  { href: "/mr/medical-shops", label: "Medical Shops", icon: Building2 },
  { href: "/mr/stockists", label: "Stockists", icon: Truck },
  { href: "/mr/territories", label: "Territories", icon: Map },
  { href: "/mr/profile", label: "My Profile", icon: UserCircle },
];

export default function MRLayout({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading) {
      if (!user) router.replace("/login");
      else if (user.role !== "MR") router.replace("/admin/dashboard");
      else if (user.status !== "APPROVED") router.replace("/login");
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
        <main className="flex-1 p-4 pb-24 sm:p-6 sm:pb-6">{children}</main>
      </div>
      <MobileBottomNav items={BOTTOM_NAV_ITEMS} />
    </div>
  );
}
