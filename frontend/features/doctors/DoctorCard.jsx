"use client";

import Link from "next/link";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { MapPin, Phone, Stethoscope, CalendarPlus } from "lucide-react";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { planVisit } from "@/services/visit-service";

export default function DoctorCard({ doctor, mapUrl }) {
  const initial = doctor.full_name?.trim()?.[0]?.toUpperCase() || "D";
  const { showToast } = useToast();
  const queryClient = useQueryClient();

  const addToPlanMutation = useMutation({
    mutationFn: () => planVisit(doctor.id, new Date().toISOString().slice(0, 10)),
    onSuccess: () => {
      showToast(`${doctor.full_name} added to today's visit plan.`, "success");
      queryClient.invalidateQueries({ queryKey: ["my-visits"] });
      queryClient.invalidateQueries({ queryKey: ["daily-route"] });
    },
    onError: (err) => showToast(err.message || "Could not add to visit plan.", "error"),
  });

  return (
    <div className="card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-start gap-3">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
          {initial}
        </div>
        <div>
          <p className="font-medium text-slate-900">{doctor.full_name}</p>
          <p className="flex items-center gap-1 text-sm text-slate-500">
            <Stethoscope className="h-3.5 w-3.5" aria-hidden="true" />
            {doctor.specialization_name || "Specialization"}
            {doctor.qualification ? ` • ${doctor.qualification}` : ""}
          </p>
          <p className="mt-1 text-sm text-slate-500">
            {doctor.clinic_name || doctor.hospital_name}
          </p>
          <p className="flex items-center gap-1 text-xs text-slate-400">
            <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
            {[doctor.area, doctor.city].filter(Boolean).join(", ")}
          </p>
          {doctor.phone && (
            <p className="mt-1 flex items-center gap-1 text-sm text-slate-600">
              <Phone className="h-3.5 w-3.5" aria-hidden="true" />
              {doctor.phone}
            </p>
          )}
        </div>
      </div>

      <div className="flex gap-2 sm:flex-col">
        <Link href={`/mr/doctors/${doctor.id}`} className="flex-1 sm:flex-none">
          <Button className="w-full">View Profile</Button>
        </Link>
        {mapUrl && (
          <a href={mapUrl} target="_blank" rel="noopener noreferrer" className="flex-1 sm:flex-none">
            <Button variant="secondary" className="w-full">
              Open Map
            </Button>
          </a>
        )}
        <Button
          variant="secondary"
          className="w-full"
          onClick={() => addToPlanMutation.mutate()}
          disabled={addToPlanMutation.isPending}
        >
          <CalendarPlus className="h-4 w-4" aria-hidden="true" />
          {addToPlanMutation.isPending ? "Adding…" : "Add to Visit Plan"}
        </Button>
      </div>
    </div>
  );
}
