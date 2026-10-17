"use client";

/**
 * MR dashboard panel: the doctors in the MR's assigned area(s), on a map and
 * as a list. With location permission the list is sorted nearest-first and
 * shows the distance to each doctor.
 */
import { useMemo, useState } from "react";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { LocateFixed, MapPin, Stethoscope } from "lucide-react";
import { Card, EmptyState, Skeleton } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import DoctorsMap from "@/features/doctors/DoctorsMap";
import { doctorsToMapPoints } from "@/features/doctors/map-points";
import { listDoctorsForMR, listSpecializations } from "@/services/doctor-service";
import { listMyTerritories } from "@/services/territory-service";

function distanceKm(a, b) {
  const R = 6371;
  const toRad = (d) => (d * Math.PI) / 180;
  const dLat = toRad(b.lat - a.lat);
  const dLng = toRad(b.lng - a.lng);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * Math.sin(dLng / 2) ** 2;
  return 2 * R * Math.asin(Math.min(1, Math.sqrt(h)));
}

export default function AreaDoctorsPanel() {
  const { showToast } = useToast();
  const [origin, setOrigin] = useState(null);
  const [locating, setLocating] = useState(false);

  const { data: terrData, isLoading: terrLoading } = useQuery({ queryKey: ["my-territories"], queryFn: listMyTerritories });
  const { data: docData, isLoading: docLoading } = useQuery({
    queryKey: ["mr-area-doctors"],
    queryFn: () => listDoctorsForMR({ page: 1, page_size: 100, sort_by: "name" }),
  });
  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });

  const territories = terrData?.data || [];
  const doctors = docData?.data?.items || [];
  const specializations = specData?.data || [];
  const areaNames = [...new Set(doctors.map((d) => d.area).filter(Boolean))];

  const ranked = useMemo(() => {
    const rows = doctors.map((d) => {
      const has = d.latitude != null && d.longitude != null;
      const km = origin && has ? distanceKm(origin, { lat: Number(d.latitude), lng: Number(d.longitude) }) : null;
      return { doctor: d, km };
    });
    if (origin) rows.sort((a, b) => (a.km ?? Infinity) - (b.km ?? Infinity));
    return rows;
  }, [doctors, origin]);

  function locate() {
    if (!("geolocation" in navigator)) {
      showToast("Location isn't available in this browser.", "error");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => { setOrigin({ lat: pos.coords.latitude, lng: pos.coords.longitude }); setLocating(false); },
      () => { setLocating(false); showToast("Couldn't get your location. Allow location access and try again.", "error"); },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }

  if (terrLoading || docLoading) return <Skeleton className="mt-6 h-80" />;

  if (territories.length === 0) {
    return (
      <Card className="mt-6">
        <EmptyState
          icon={MapPin}
          title="No area assigned yet."
          description="Your admin will assign your working area. Doctors, medical shops and stockists of that area will then appear here on the map."
        />
      </Card>
    );
  }

  return (
    <Card className="mt-6">
      <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="flex items-center gap-2 font-medium text-slate-900">
            <MapPin className="h-4 w-4 text-primary-600" aria-hidden="true" /> Doctors in your area
          </h2>
          <p className="text-sm text-slate-500">
            {territories.map((t) => t.name).join(", ")}
            {areaNames.length > 0 && ` · ${doctors.length} doctor${doctors.length === 1 ? "" : "s"}`}
          </p>
        </div>
        <Button variant="secondary" onClick={locate} disabled={locating}>
          <LocateFixed className="h-4 w-4" aria-hidden="true" />
          {locating ? "Locating…" : origin ? "Update my location" : "Nearest to me"}
        </Button>
      </div>

      {doctors.length === 0 ? (
        <EmptyState
          icon={Stethoscope}
          title="No doctors added in your area yet."
          description="Your admin can add doctors for this area or import them from Google."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <DoctorsMap
              height="360px"
              origin={origin}
              points={doctorsToMapPoints(doctors, { specializations, hrefFor: (d) => `/mr/doctors/${d.id}` })}
            />
          </div>
          <ul className="max-h-[360px] divide-y divide-slate-100 overflow-y-auto lg:col-span-2">
            {ranked.slice(0, 30).map(({ doctor, km }) => (
              <li key={doctor.id} className="flex items-center justify-between gap-3 py-2">
                <div className="min-w-0">
                  <Link href={`/mr/doctors/${doctor.id}`} className="block truncate text-sm font-medium text-slate-900 hover:underline">
                    {doctor.full_name}
                  </Link>
                  <p className="truncate text-xs text-slate-500">
                    {[specializations.find((s) => s.id === doctor.specialization_id)?.name, doctor.clinic_name || doctor.area]
                      .filter(Boolean).join(" · ")}
                  </p>
                </div>
                {km != null && <span className="mono shrink-0 text-xs text-slate-500">{km.toFixed(1)} km</span>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </Card>
  );
}
