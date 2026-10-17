"use client";

import { useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LocateFixed, Navigation, Route as RouteIcon, X } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import DoctorsMap from "@/features/doctors/DoctorsMap";
import { getDailyRoute } from "@/services/visit-service";
import { formatISODate, localISODate } from "@/lib/dates";

// Google Maps directions URLs accept up to 9 waypoints between origin and destination.
const MAX_WAYPOINTS = 9;

function directionsUrl(stops, origin) {
  const coords = stops
    .filter((s) => s.doctor.latitude && s.doctor.longitude)
    .map((s) => `${s.doctor.latitude},${s.doctor.longitude}`);
  if (coords.length === 0) return null;
  const params = new URLSearchParams({ api: "1", travelmode: "driving" });
  let rest = coords;
  if (origin) {
    params.set("origin", `${origin.lat},${origin.lng}`);
  } else if (coords.length > 1) {
    params.set("origin", coords[0]);
    rest = coords.slice(1);
  }
  params.set("destination", rest[rest.length - 1]);
  const waypoints = rest.slice(0, -1).slice(0, MAX_WAYPOINTS);
  if (waypoints.length) params.set("waypoints", waypoints.join("|"));
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export default function DailyRoutePage() {
  const { showToast } = useToast();
  const [targetDate, setTargetDate] = useState(localISODate());
  const [origin, setOrigin] = useState(null); // { lat, lng }
  const [locating, setLocating] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["daily-route", targetDate, origin?.lat, origin?.lng],
    queryFn: () => getDailyRoute(targetDate, origin),
  });

  const stops = data?.data || [];
  const totalKm = stops.reduce((sum, s) => sum + (s.distance_from_previous_km || 0), 0);
  const navUrl = directionsUrl(stops, origin);

  function locateMe() {
    if (!("geolocation" in navigator)) {
      showToast("Location isn't available in this browser.", "error");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setOrigin({ lat: Number(pos.coords.latitude.toFixed(6)), lng: Number(pos.coords.longitude.toFixed(6)) });
        setLocating(false);
      },
      (err) => {
        setLocating(false);
        showToast(
          err.code === err.PERMISSION_DENIED
            ? "Location permission was denied. Allow it in your browser settings to start from where you are."
            : "Couldn't get your location. Try again outdoors or check GPS.",
          "error"
        );
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }

  return (
    <div>
      <PageHeader
        title="Daily Route"
        description="Your planned visits for the day, ordered nearest-first to minimize backtracking."
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="sm:w-48">
          <Input id="route-date" type="date" aria-label="Route date" value={targetDate} onChange={(e) => setTargetDate(e.target.value)} />
        </div>
        {origin ? (
          <Button variant="secondary" onClick={() => setOrigin(null)}>
            <X className="h-4 w-4" aria-hidden="true" /> Starting from your location
          </Button>
        ) : (
          <Button variant="secondary" onClick={locateMe} disabled={locating}>
            <LocateFixed className="h-4 w-4" aria-hidden="true" />
            {locating ? "Locating…" : "Start from my location"}
          </Button>
        )}
        {navUrl && (
          <a href={navUrl} target="_blank" rel="noopener noreferrer" className="sm:ml-auto">
            <Button className="w-full">
              <Navigation className="h-4 w-4" aria-hidden="true" /> Navigate in Google Maps
            </Button>
          </a>
        )}
      </div>

      {isLoading && <SkeletonRows count={3} />}
      {isError && <ErrorState />}
      {!isLoading && !isError && stops.length === 0 && (
        <EmptyState
          icon={RouteIcon}
          title={`No planned visits for ${formatISODate(targetDate)}.`}
          description="Add doctors to your visit plan from the Doctors page first."
        />
      )}

      {stops.length > 0 && (
        <div className="grid gap-4 lg:grid-cols-2">
          <div>
            <p className="mb-2 text-sm text-slate-500">
              {stops.length} stop{stops.length === 1 ? "" : "s"}
              {totalKm > 0 && <> · about <span className="font-medium text-slate-700">{totalKm.toFixed(1)} km</span> straight-line</>}
            </p>
            <ol className="space-y-3">
              {stops.map((stop) => (
                <li key={stop.visit.id}>
                  <Card className="!p-4">
                    <div className="flex items-start gap-3">
                      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary-100 text-sm font-semibold text-primary-700">
                        {stop.order}
                      </span>
                      <div className="min-w-0 flex-1">
                        <Link href={`/mr/doctors/${stop.doctor.id}`} className="font-medium text-slate-900 hover:underline">
                          {stop.doctor.full_name}
                        </Link>
                        <p className="text-sm text-slate-500">
                          {stop.doctor.clinic_name ? `${stop.doctor.clinic_name} · ` : ""}
                          {[stop.doctor.area, stop.doctor.city].filter(Boolean).join(", ")}
                        </p>
                        {!stop.doctor.latitude && (
                          <p className="mt-1 text-xs text-slate-400">No coordinates on file — placed at the end of the route.</p>
                        )}
                      </div>
                      {stop.distance_from_previous_km != null && (
                        <span className="mono shrink-0 text-xs text-slate-500">
                          {stop.order === 1 ? (origin ? "from you " : "") : "+"}{stop.distance_from_previous_km} km
                        </span>
                      )}
                    </div>
                  </Card>
                </li>
              ))}
            </ol>
            <p className="mt-3 text-xs text-slate-400">
              Distances are straight-line estimates; Google Maps shows real road distance and traffic.
            </p>
          </div>
          <div className="lg:sticky lg:top-4 lg:self-start">
            <DoctorsMap
              route
              origin={origin}
              height="55vh"
              points={stops.map((s) => ({
                id: s.doctor.id,
                lat: s.doctor.latitude,
                lng: s.doctor.longitude,
                title: s.doctor.full_name,
                subtitle: [s.doctor.area, s.doctor.city].filter(Boolean).join(", "),
                href: `/mr/doctors/${s.doctor.id}`,
                label: s.order,
              }))}
            />
          </div>
        </div>
      )}
    </div>
  );
}
