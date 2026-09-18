"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Route as RouteIcon } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import { getDailyRoute } from "@/services/visit-service";

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

export default function DailyRoutePage() {
  const [targetDate, setTargetDate] = useState(todayISO());

  const { data, isLoading, isError } = useQuery({
    queryKey: ["daily-route", targetDate],
    queryFn: () => getDailyRoute(targetDate),
  });

  const stops = data?.data || [];

  return (
    <div>
      <PageHeader
        title="Daily Route"
        description="Your planned visits for the day, ordered to minimize backtracking."
      />

      <div className="mb-4 max-w-[200px]">
        <Input id="route-date" type="date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
      </div>

      {isLoading && <SkeletonRows count={3} />}
      {isError && <ErrorState />}
      {!isLoading && stops.length === 0 && (
        <EmptyState icon={RouteIcon} title="No planned visits for this date." description="Add doctors to your visit plan from the Doctors page first." />
      )}

      <ol className="space-y-3">
        {stops.map((stop) => (
          <li key={stop.visit.id}>
            <Card>
              <div className="flex items-start gap-3">
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
                  {stop.order}
                </span>
                <div>
                  <p className="font-medium text-slate-900">{stop.doctor.full_name}</p>
                  <p className="text-sm text-slate-500">{[stop.doctor.area, stop.doctor.city].filter(Boolean).join(", ")}</p>
                  {!stop.doctor.latitude && (
                    <p className="mt-1 text-xs text-slate-400">No coordinates on file — placed at the end of the route.</p>
                  )}
                </div>
              </div>
            </Card>
          </li>
        ))}
      </ol>
    </div>
  );
}
