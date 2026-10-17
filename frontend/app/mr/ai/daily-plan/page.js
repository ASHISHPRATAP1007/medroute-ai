"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { CalendarPlus, Sparkles } from "lucide-react";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { planVisit } from "@/services/visit-service";
import { localISODate } from "@/lib/dates";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import { getDailyPlan } from "@/services/ai-service";

function ScoreBadge({ score }) {
  const tone = score >= 70 ? "bg-success-50 text-success-700" : score >= 40 ? "bg-warning-50 text-warning-700" : "bg-slate-100 text-slate-600";
  return <span className={`badge ${tone}`}>{score}/100</span>;
}

export default function MRDailyPlanPage() {
  const { data, isLoading, isError } = useQuery({ queryKey: ["daily-plan"], queryFn: () => getDailyPlan(20) });
  const items = data?.data || [];
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const addMutation = useMutation({
    mutationFn: (doctor) => planVisit(doctor.id, localISODate()),
    onSuccess: (_, doctor) => {
      showToast(`${doctor.full_name} added to today's visit plan.`, "success");
      queryClient.invalidateQueries({ queryKey: ["my-visits"] });
      queryClient.invalidateQueries({ queryKey: ["daily-route"] });
    },
    onError: (err) => showToast(err.message || "Could not add to visit plan.", "error"),
  });

  return (
    <div>
      <PageHeader
        title="AI Daily Plan"
        description="Doctors in your territory ranked by a transparent opportunity score — see exactly why each one is ranked where it is."
      />

      {isLoading && <SkeletonRows count={5} />}
      {isError && <ErrorState />}
      {!isLoading && items.length === 0 && (
        <EmptyState
          icon={Sparkles}
          title="No ranked doctors yet."
          description="This fills in once you have active doctors in your assigned territory."
        />
      )}

      <div className="space-y-3">
        {items.map((item) => (
          <Card key={item.doctor.id}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <Link href={`/mr/doctors/${item.doctor.id}`} className="font-medium text-slate-900 hover:underline">
                  {item.doctor.full_name}
                </Link>
                <p className="text-sm text-slate-500">{[item.doctor.area, item.doctor.city].filter(Boolean).join(", ")}</p>
              </div>
              <div className="flex shrink-0 flex-col items-end gap-2">
                <ScoreBadge score={item.score} />
                <Button
                  variant="secondary"
                  className="!px-2.5 !py-1 text-xs"
                  disabled={addMutation.isPending && addMutation.variables?.id === item.doctor.id}
                  onClick={() => addMutation.mutate(item.doctor)}
                >
                  <CalendarPlus className="h-3.5 w-3.5" aria-hidden="true" /> Add to today
                </Button>
              </div>
            </div>
            <ul className="mt-3 space-y-1 border-t border-slate-100 pt-3 text-sm text-slate-600">
              {item.reasons.map((reason, i) => (
                <li key={i} className="flex gap-2">
                  <span aria-hidden="true">•</span>
                  {reason}
                </li>
              ))}
            </ul>
          </Card>
        ))}
      </div>
    </div>
  );
}
