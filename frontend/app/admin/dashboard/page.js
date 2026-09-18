"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { Users, Clock, CheckCircle2, Stethoscope, Activity, Building2, Truck, Map } from "lucide-react";
import { PageHeader, StatCard } from "@/components/ui/PageHeader";
import { Card, EmptyState, ErrorState, Skeleton } from "@/components/ui/Feedback";
import Badge from "@/components/ui/Badge";
import { getAdminDashboard } from "@/services/dashboard-service";

export default function AdminDashboardPage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-dashboard"],
    queryFn: getAdminDashboard,
  });

  const stats = data?.data;

  return (
    <div>
      <PageHeader title="Dashboard" description="Live snapshot of MRs, doctors, and territories." />

      {isLoading && (
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      )}
      {isError && <ErrorState />}

      {stats && (
        <>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <StatCard label="Total MRs" value={stats.total_mrs} icon={Users} />
            <StatCard label="Pending MRs" value={stats.pending_mrs} icon={Clock} />
            <StatCard label="Approved MRs" value={stats.approved_mrs} icon={CheckCircle2} />
            <StatCard label="Total Doctors" value={stats.total_doctors} icon={Stethoscope} />
            <StatCard label="Active Doctors" value={stats.active_doctors} icon={Activity} />
            <StatCard label="Medical Shops" value={stats.medical_shops} icon={Building2} />
            <StatCard label="Stockists" value={stats.stockists} icon={Truck} />
            <StatCard label="Territories" value={stats.territories} icon={Map} />
          </div>

          <div className="mt-6">
            <Card>
              <div className="flex items-center justify-between">
                <h2 className="font-medium text-slate-900">Pending MR approvals</h2>
                <Link href="/admin/mrs?status=PENDING" className="text-sm font-medium text-primary-600 hover:underline">
                  View all
                </Link>
              </div>
              <div className="mt-4">
                {stats.recent_pending_mrs.length === 0 ? (
                  <EmptyState title="No pending registrations." />
                ) : (
                  <ul className="divide-y divide-slate-100">
                    {stats.recent_pending_mrs.map((mr) => (
                      <li key={mr.id} className="flex items-center justify-between py-3">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{mr.full_name}</p>
                          <p className="text-xs text-slate-500">{mr.email}</p>
                        </div>
                        <Badge status="PENDING" />
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
