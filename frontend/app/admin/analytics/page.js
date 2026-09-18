"use client";

import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import { getMRPerformance, getTerritoryCoverage } from "@/services/analytics-service";

function CoverageBar({ percent }) {
  const tone = percent >= 70 ? "bg-success-500" : percent >= 40 ? "bg-warning-500" : "bg-danger-500";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div className={`h-full ${tone}`} style={{ width: `${percent}%` }} />
    </div>
  );
}

export default function AdminAnalyticsPage() {
  const { data: mrData, isLoading: mrLoading, isError: mrError } = useQuery({
    queryKey: ["mr-performance"], queryFn: getMRPerformance,
  });
  const { data: coverageData, isLoading: coverageLoading, isError: coverageError } = useQuery({
    queryKey: ["territory-coverage"], queryFn: getTerritoryCoverage,
  });

  const mrReports = mrData?.data || [];
  const coverageReports = coverageData?.data || [];

  return (
    <div>
      <PageHeader title="Analytics" description="Real visit and coverage figures — nothing here is estimated." />

      <Card className="mb-6">
        <h2 className="mb-3 font-medium text-slate-900">MR Performance</h2>
        {mrLoading && <SkeletonRows count={3} />}
        {mrError && <ErrorState />}
        {!mrLoading && mrReports.length === 0 && <EmptyState title="No approved MRs yet." />}
        {mrReports.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-slate-500">
                  <th className="py-2 pr-4">MR</th>
                  <th className="py-2 pr-4">Planned</th>
                  <th className="py-2 pr-4">Completed</th>
                  <th className="py-2 pr-4">Cancelled</th>
                  <th className="py-2 pr-4">Missed</th>
                  <th className="py-2 pr-4">Completion Rate</th>
                  <th className="py-2 pr-4">Doctors Covered</th>
                  <th className="py-2">Last Visit</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {mrReports.map((r) => (
                  <tr key={r.mr_id}>
                    <td className="py-2 pr-4 font-medium text-slate-900">{r.full_name}</td>
                    <td className="py-2 pr-4">{r.visits_planned}</td>
                    <td className="py-2 pr-4">{r.visits_completed}</td>
                    <td className="py-2 pr-4">{r.visits_cancelled}</td>
                    <td className="py-2 pr-4">{r.visits_missed}</td>
                    <td className="py-2 pr-4">{Math.round(r.completion_rate * 100)}%</td>
                    <td className="py-2 pr-4">{r.doctors_covered}</td>
                    <td className="py-2">{r.last_visit_date || "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      <Card>
        <h2 className="mb-3 font-medium text-slate-900">Territory Coverage</h2>
        {coverageLoading && <SkeletonRows count={3} />}
        {coverageError && <ErrorState />}
        {!coverageLoading && coverageReports.length === 0 && <EmptyState title="No territories created yet." />}
        <div className="space-y-4">
          {coverageReports.map((r) => (
            <div key={r.territory_id}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-900">{r.territory_name}</span>
                <span className="text-slate-500">{r.doctors_visited}/{r.total_active_doctors} doctors ({r.coverage_percent}%)</span>
              </div>
              <CoverageBar percent={r.coverage_percent} />
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
