"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Stethoscope, Building2, Truck, Map, Sparkles } from "lucide-react";
import { PageHeader, StatCard } from "@/components/ui/PageHeader";
import { Card, ErrorState, Skeleton } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useAuth } from "@/hooks/use-auth";
import { getMRDashboard } from "@/services/dashboard-service";
import { getDailyPlan } from "@/services/ai-service";

export default function MRDashboardPage() {
  const { user } = useAuth();
  const { data, isLoading, isError } = useQuery({
    queryKey: ["mr-dashboard"],
    queryFn: getMRDashboard,
  });
  const { data: planData } = useQuery({ queryKey: ["daily-plan-preview"], queryFn: () => getDailyPlan(3) });

  const stats = data?.data;
  const topPicks = planData?.data || [];

  return (
    <div>
      <PageHeader title={`Welcome, ${user?.full_name?.split(" ")[0] || "there"}`} description="Here's what's happening in your territory." />

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-24" />)}
        </div>
      )}
      {isError && <ErrorState />}

      {stats && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Assigned Territories" value={stats.assigned_territory_count} icon={Map} />
            <StatCard label="Doctors" value={stats.total_doctors} icon={Stethoscope} />
            <StatCard label="Medical Shops" value={stats.total_medical_shops} icon={Building2} />
            <StatCard label="Stockists" value={stats.total_stockists} icon={Truck} />
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <Card>
              <h2 className="font-medium text-slate-900">Quick actions</h2>
              <div className="mt-4 grid grid-cols-2 gap-3">
                <Link href="/mr/doctors"><Button variant="secondary" className="w-full">Find Doctor</Button></Link>
                <Link href="/mr/medical-shops"><Button variant="secondary" className="w-full">Find Medical Shop</Button></Link>
                <Link href="/mr/stockists"><Button variant="secondary" className="w-full">Find Stockist</Button></Link>
                <Link href="/mr/territories"><Button variant="secondary" className="w-full">Explore Territory</Button></Link>
              </div>
            </Card>

            <Card>
              <div className="flex items-center justify-between">
                <h2 className="flex items-center gap-2 font-medium text-slate-900">
                  <Sparkles className="h-4 w-4 text-primary-500" aria-hidden="true" /> Today's top picks
                </h2>
                <Link href="/mr/ai/daily-plan" className="text-sm font-medium text-primary-600 hover:underline">
                  View full plan
                </Link>
              </div>
              {topPicks.length === 0 ? (
                <p className="mt-3 text-sm text-slate-500">No ranked doctors yet — check back once your territory has active doctors.</p>
              ) : (
                <ul className="mt-3 space-y-2">
                  {topPicks.map((item) => (
                    <li key={item.doctor.id} className="flex items-center justify-between text-sm">
                      <Link href={`/mr/doctors/${item.doctor.id}`} className="text-slate-700 hover:underline">
                        {item.doctor.full_name}
                      </Link>
                      <span className="badge bg-primary-50 text-primary-700">{item.score}/100</span>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
