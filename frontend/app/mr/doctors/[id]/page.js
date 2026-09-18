"use client";

import { useParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Mail, MapPin, Phone, Stethoscope, Building2, Hospital, Star, Clock, Sparkles, History, CalendarClock } from "lucide-react";
import { Card, ErrorState, Skeleton } from "@/components/ui/Feedback";
import { PageHeader } from "@/components/ui/PageHeader";
import Button from "@/components/ui/Button";
import Badge from "@/components/ui/Badge";
import { getDoctor, listSpecializations } from "@/services/doctor-service";
import { getDoctorExternalData } from "@/services/external-data-service";
import { getOpportunityScore } from "@/services/ai-service";
import { getDoctorVisitHistory } from "@/services/visit-service";

export default function MRDoctorProfilePage() {
  const { id } = useParams();

  const { data, isLoading, isError } = useQuery({ queryKey: ["doctor", id], queryFn: () => getDoctor(id) });
  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const { data: externalData } = useQuery({
    queryKey: ["doctor-external", id],
    queryFn: () => getDoctorExternalData(id),
    enabled: !!id,
  });
  const { data: scoreData } = useQuery({
    queryKey: ["doctor-opportunity", id],
    queryFn: () => getOpportunityScore(id),
    enabled: !!id,
  });
  const { data: visitHistoryData } = useQuery({
    queryKey: ["doctor-visit-history", id],
    queryFn: () => getDoctorVisitHistory(id),
    enabled: !!id,
  });

  if (isLoading) return <Skeleton className="h-96 max-w-3xl" />;
  if (isError) return <ErrorState message="Doctor not found or not in your assigned territory." />;

  const doctor = data.data;
  const enrichment = externalData?.data || null;
  const opportunity = scoreData?.data || null;
  const visitHistory = visitHistoryData?.data || [];
  const upcomingFollowUp = visitHistory.find((v) => v.follow_up_date && new Date(v.follow_up_date) >= new Date(new Date().toDateString()));
  const specialization = (specData?.data || []).find((s) => s.id === doctor.specialization_id)?.name;

  const mapUrl =
    doctor.latitude && doctor.longitude
      ? `https://www.google.com/maps/search/?api=1&query=${doctor.latitude},${doctor.longitude}`
      : doctor.address
      ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(doctor.address)}`
      : null;

  return (
    <div className="max-w-3xl">
      <PageHeader title={doctor.full_name} description={`${specialization || "Specialization"}${doctor.qualification ? ` • ${doctor.qualification}` : ""}`} />

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <Stethoscope className="h-4 w-4 text-primary-600" aria-hidden="true" /> Basic Information
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Specialization</dt><dd>{specialization || "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Qualification</dt><dd>{doctor.qualification || "—"}</dd></div>
          </dl>
        </Card>

        <Card>
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <Building2 className="h-4 w-4 text-primary-600" aria-hidden="true" /> Practice Information
          </h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-500">Clinic</dt><dd>{doctor.clinic_name || "—"}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-500">Hospital</dt><dd className="flex items-center gap-1"><Hospital className="h-3.5 w-3.5" aria-hidden="true" />{doctor.hospital_name || "—"}</dd></div>
          </dl>
        </Card>

        <Card className="sm:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <MapPin className="h-4 w-4 text-primary-600" aria-hidden="true" /> Location
          </h2>
          <p className="text-sm text-slate-700">{doctor.address}</p>
          <p className="text-sm text-slate-500">{[doctor.area, doctor.city, doctor.state, doctor.pincode].filter(Boolean).join(", ")}</p>

          {(doctor.latitude && doctor.longitude) || doctor.address ? (
            <div className="mt-4 rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-center">
              <p className="text-sm text-slate-500">Live embedded map is not enabled — add a Google Maps key to unlock it.</p>
              {mapUrl && (
                <a href={mapUrl} target="_blank" rel="noopener noreferrer" className="mt-3 inline-block">
                  <Button variant="secondary">View Location</Button>
                </a>
              )}
            </div>
          ) : null}
        </Card>

        <Card className="sm:col-span-2">
          <h2 className="mb-3 font-medium text-slate-900">Contact</h2>
          <div className="space-y-2 text-sm">
            {doctor.phone && <p className="flex items-center gap-2"><Phone className="h-4 w-4 text-slate-400" aria-hidden="true" />{doctor.phone}</p>}
            {doctor.email && <p className="flex items-center gap-2"><Mail className="h-4 w-4 text-slate-400" aria-hidden="true" />{doctor.email}</p>}
            {!doctor.phone && !doctor.email && <p className="text-slate-500">No contact details available.</p>}
          </div>
        </Card>

        <Card className="sm:col-span-2">
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <Star className="h-4 w-4 text-primary-600" aria-hidden="true" /> Google Business Profile
          </h2>
          {enrichment ? (
            <>
              <div className="flex items-center gap-2 text-sm">
                <span className="flex items-center gap-1 font-medium text-amber-600">
                  <Star className="h-4 w-4 fill-amber-400 text-amber-400" aria-hidden="true" />
                  {enrichment.rating ?? "—"}
                </span>
                <span className="text-slate-500">({enrichment.user_ratings_total ?? 0} ratings)</span>
              </div>

              {enrichment.opening_hours?.weekday_text && (
                <div className="mt-3 flex items-start gap-2 text-sm text-slate-600">
                  <Clock className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                  <ul>
                    {enrichment.opening_hours.weekday_text.map((line) => <li key={line}>{line}</li>)}
                  </ul>
                </div>
              )}

              {enrichment.reviews?.length > 0 && (
                <div className="mt-4 space-y-3 border-t border-slate-100 pt-3">
                  {enrichment.reviews.map((review, i) => (
                    <div key={i} className="text-sm">
                      <p className="font-medium text-slate-800">{review.author} — {review.rating}★</p>
                      <p className="text-slate-500">{review.text}</p>
                    </div>
                  ))}
                </div>
              )}

              <p className="mt-3 text-xs text-slate-400">
                Synced {new Date(enrichment.last_synced_at).toLocaleString()}
              </p>
            </>
          ) : (
            <p className="text-sm text-slate-500">Not yet synced from Google. Ask your admin to sync this doctor's profile.</p>
          )}
        </Card>
      </div>

      {opportunity && (
        <Card className="mt-4">
          <div className="flex items-center justify-between">
            <h2 className="flex items-center gap-2 font-medium text-slate-900">
              <Sparkles className="h-4 w-4 text-primary-600" aria-hidden="true" /> AI Opportunity
            </h2>
            <span className="badge bg-primary-50 text-primary-700">{opportunity.score}/100</span>
          </div>
          <ul className="mt-3 space-y-1 border-t border-slate-100 pt-3 text-sm text-slate-600">
            {opportunity.reasons.map((reason, i) => (
              <li key={i} className="flex gap-2"><span aria-hidden="true">•</span>{reason}</li>
            ))}
          </ul>
        </Card>
      )}

      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <Card>
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <History className="h-4 w-4 text-primary-600" aria-hidden="true" /> Visit History
          </h2>
          {visitHistory.length === 0 ? (
            <p className="text-sm text-slate-500">You haven't visited this doctor yet.</p>
          ) : (
            <ul className="space-y-3">
              {visitHistory.map((visit) => (
                <li key={visit.id} className="border-b border-slate-100 pb-2 last:border-0 last:pb-0">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-700">{visit.scheduled_date}</span>
                    <Badge status={visit.status} />
                  </div>
                  {visit.outcome && <p className="mt-1 text-sm text-slate-500">{visit.outcome}</p>}
                </li>
              ))}
            </ul>
          )}
        </Card>

        <Card>
          <h2 className="mb-3 flex items-center gap-2 font-medium text-slate-900">
            <CalendarClock className="h-4 w-4 text-primary-600" aria-hidden="true" /> Follow-up
          </h2>
          {upcomingFollowUp ? (
            <p className="text-sm text-slate-700">
              Scheduled for <span className="font-medium">{upcomingFollowUp.follow_up_date}</span>
            </p>
          ) : (
            <p className="text-sm text-slate-500">No upcoming follow-up set for this doctor.</p>
          )}
        </Card>
      </div>
    </div>
  );
}

