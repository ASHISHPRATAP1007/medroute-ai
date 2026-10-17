"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { PageHeader } from "@/components/ui/PageHeader";
import { Select, Input } from "@/components/ui/FormFields";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { listMyVisits, updateVisit } from "@/services/visit-service";
import { formatISODate, localISODate } from "@/lib/dates";

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "PLANNED", label: "Planned" },
  { value: "COMPLETED", label: "Completed" },
  { value: "CANCELLED", label: "Cancelled" },
  { value: "MISSED", label: "Missed" },
];

function CompleteVisitForm({ visit, onDone }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { register, handleSubmit } = useForm({
    defaultValues: { outcome: "", follow_up_date: "" },
  });

  const mutation = useMutation({
    mutationFn: (values) => updateVisit(visit.id, {
      status: "COMPLETED",
      outcome: values.outcome || null,
      follow_up_date: values.follow_up_date || null,
      notes: visit.notes,
    }),
    onSuccess: () => {
      showToast("Visit marked completed.", "success");
      queryClient.invalidateQueries({ queryKey: ["my-visits"] });
      onDone();
    },
    onError: (err) => showToast(err.message || "Failed to update visit.", "error"),
  });

  return (
    <form className="mt-3 space-y-3 border-t border-slate-100 pt-3" onSubmit={handleSubmit((v) => mutation.mutate(v))}>
      <Input label="Outcome / notes" id={`outcome-${visit.id}`} {...register("outcome")} />
      <Input label="Follow-up date (optional)" id={`followup-${visit.id}`} type="date" min={localISODate()} {...register("follow_up_date")} />
      <div className="flex gap-2">
        <Button type="submit" className="!px-3 !py-1.5 text-xs" disabled={mutation.isPending}>
          {mutation.isPending ? "Saving…" : "Mark Completed"}
        </Button>
        <Button type="button" variant="secondary" className="!px-3 !py-1.5 text-xs" onClick={onDone}>
          Cancel
        </Button>
      </div>
    </form>
  );
}

export default function MRVisitsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [expandedVisitId, setExpandedVisitId] = useState(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["my-visits", { statusFilter }],
    queryFn: () => listMyVisits({ status: statusFilter }),
  });

  const cancelMutation = useMutation({
    mutationFn: (visit) => updateVisit(visit.id, { status: "CANCELLED", notes: visit.notes, outcome: visit.outcome, follow_up_date: visit.follow_up_date }),
    onSuccess: () => {
      showToast("Visit cancelled.", "success");
      queryClient.invalidateQueries({ queryKey: ["my-visits"] });
    },
    onError: (err) => showToast(err.message || "Failed to cancel visit.", "error"),
  });

  const visits = data?.data || [];

  return (
    <div>
      <PageHeader title="My Visits" description="Doctors you've added to your visit plan." />

      <div className="mb-4 sm:max-w-[200px]">
        <Select id="visit-status-filter" value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)} options={STATUS_OPTIONS} />
      </div>

      {isLoading && <SkeletonRows count={4} />}
      {isError && <ErrorState />}
      {!isLoading && visits.length === 0 && <EmptyState title="No visits found." description="Add doctors to your plan from the Doctors page." />}

      <div className="space-y-3">
        {visits.map((visit) => (
          <Card key={visit.id}>
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                {visit.doctor ? (
                  <Link href={`/mr/doctors/${visit.doctor.id}`} className="font-medium text-slate-900 hover:underline">
                    {visit.doctor.full_name}
                  </Link>
                ) : (
                  <p className="font-medium text-slate-900">Doctor</p>
                )}
                <p className="text-sm text-slate-500">
                  {formatISODate(visit.scheduled_date)}
                  {visit.doctor && [visit.doctor.area, visit.doctor.city].filter(Boolean).length > 0 && (
                    <> · {[visit.doctor.area, visit.doctor.city].filter(Boolean).join(", ")}</>
                  )}
                </p>
                {visit.outcome && <p className="mt-1 text-sm text-slate-700">{visit.outcome}</p>}
                {visit.follow_up_date && <p className="mt-1 text-xs text-primary-600">Follow-up: {formatISODate(visit.follow_up_date)}</p>}
              </div>
              <Badge status={visit.status} />
            </div>

            {(visit.status === "PLANNED" || visit.status === "MISSED") && expandedVisitId !== visit.id && (
              <div className="mt-3 flex gap-2 border-t border-slate-100 pt-3">
                <Button className="!px-3 !py-1.5 text-xs" onClick={() => setExpandedVisitId(visit.id)}>
                  {visit.status === "MISSED" ? "Log as Completed" : "Mark Completed"}
                </Button>
                {visit.status === "PLANNED" && (
                  <Button variant="danger" className="!px-3 !py-1.5 text-xs" onClick={() => cancelMutation.mutate(visit)}>Cancel</Button>
                )}
              </div>
            )}
            {expandedVisitId === visit.id && (
              <CompleteVisitForm visit={visit} onDone={() => setExpandedVisitId(null)} />
            )}
          </Card>
        ))}
      </div>

      <p className="mt-4 text-sm text-slate-500">
        Want your day pre-ordered by travel distance? See your{" "}
        <Link href="/mr/visits/route" className="font-medium text-primary-600 hover:underline">Daily Route</Link>.
      </p>
    </div>
  );
}
