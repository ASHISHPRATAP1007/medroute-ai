"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Compass, ExternalLink, LocateFixed, MapPin, Navigation, PhoneCall, Search } from "lucide-react";
import clsx from "clsx";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import DoctorsMap from "@/features/doctors/DoctorsMap";
import { explorePlaces } from "@/services/explore-service";

const CATEGORIES = [
  { value: "doctor", label: "Doctors & clinics", google: "doctor", hint: "e.g. cardiologist, child, dental" },
  { value: "hospital", label: "Hospitals", google: "hospital", hint: "e.g. multispeciality" },
  { value: "pharmacy", label: "Medical stores", google: "medical store", hint: "e.g. Apollo, 24 hours" },
  { value: "distributor", label: "Distributors", google: "pharma distributor", hint: "e.g. surgical, pharma" },
];
const RADII = [2, 5, 10, 15].map((km) => ({ value: String(km), label: `${km} km around` }));

/** Free deep link: the same search in Google Maps, which lists Google Business Profiles with ratings & reviews. */
function googleMapsListUrl(what, center, placeText) {
  if (placeText) return `https://www.google.com/maps/search/${encodeURIComponent(`${what} in ${placeText}`)}`;
  if (center) return `https://www.google.com/maps/search/${encodeURIComponent(what)}/@${center.lat},${center.lng},14z`;
  return null;
}

export default function ExplorePage() {
  const { showToast } = useToast();
  const [category, setCategory] = useState("doctor");
  const [keyword, setKeyword] = useState("");
  const [place, setPlace] = useState("");
  const [radius, setRadius] = useState("5");
  const [gps, setGps] = useState(null);
  const [locating, setLocating] = useState(false);
  const [lastSearch, setLastSearch] = useState(null);

  const cat = CATEGORIES.find((c) => c.value === category);

  const search = useMutation({ mutationFn: (params) => explorePlaces(params) });

  /** A typed place wins; otherwise search around the GPS point (passed in, or remembered). */
  function run(gpsPoint) {
    const point = gpsPoint || (place.trim() ? null : gps);
    const params = {
      category, keyword: keyword.trim(), radius_km: radius,
      ...(point ? { lat: point.lat, lng: point.lng } : { location: place.trim() }),
    };
    if (!point && !params.location) {
      showToast("Type a place (e.g. Gomti Nagar, Lucknow) or tap Near me.", "info");
      return;
    }
    setLastSearch({ ...params, placeText: params.location || null });
    search.mutate(params);
  }

  function nearMe() {
    if (!("geolocation" in navigator)) {
      showToast("Location isn't available in this browser.", "error");
      return;
    }
    setLocating(true);
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const g = { lat: Number(pos.coords.latitude.toFixed(5)), lng: Number(pos.coords.longitude.toFixed(5)) };
        setGps(g);
        setPlace("");
        setLocating(false);
        run(g);
      },
      () => { setLocating(false); showToast("Couldn't get your location. Allow location access, or type a place.", "error"); },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 60000 }
    );
  }

  const result = search.data?.data;
  const places = result?.places || [];
  const what = [keyword.trim(), cat.google].filter(Boolean).join(" ");
  const googleList = googleMapsListUrl(what, result?.center, lastSearch?.placeText);
  const errorMessage = search.error?.status === 429
    ? "Too many searches in a minute — please wait a moment and try again."
    : search.error?.message;

  return (
    <div>
      <PageHeader
        title="Explore any area"
        description="Find doctors, hospitals and medical stores anywhere — free map data from OpenStreetMap, plus a one-tap link to Google Maps for ratings and reviews."
      />

      <Card>
        <div role="tablist" aria-label="What to find" className="mb-4 flex flex-wrap gap-2">
          {CATEGORIES.map((c) => (
            <button
              key={c.value}
              type="button"
              role="tab"
              aria-selected={category === c.value}
              onClick={() => { if (c.value !== category) setKeyword(""); setCategory(c.value); }}
              className={clsx(
                "rounded-full border px-3.5 py-1.5 text-sm font-medium transition-colors",
                category === c.value ? "border-primary-600 bg-primary-600 text-white" : "border-slate-300 bg-white text-slate-700 hover:bg-slate-50"
              )}
            >
              {c.label}
            </button>
          ))}
        </div>
        <form
          className="grid gap-3 sm:grid-cols-12 sm:items-end"
          onSubmit={(e) => { e.preventDefault(); run(); }}
        >
          <div className="sm:col-span-3">
            <Input label="Speciality / name (optional)" id="explore-keyword" placeholder={cat.hint} value={keyword} onChange={(e) => setKeyword(e.target.value)} />
          </div>
          <div className="sm:col-span-4">
            <Input
              label="Where"
              id="explore-place"
              placeholder={gps ? "Using your location — or type any place" : "Any area, city or pincode"}
              value={place}
              onChange={(e) => setPlace(e.target.value)}
            />
          </div>
          <div className="sm:col-span-2">
            <Select label="Radius" id="explore-radius" value={radius} onChange={(e) => setRadius(e.target.value)} options={RADII} />
          </div>
          <div className="flex gap-2 sm:col-span-3">
            <Button type="submit" className="flex-1" disabled={search.isPending}>
              <Search className="h-4 w-4" aria-hidden="true" /> {search.isPending ? "Searching…" : "Search"}
            </Button>
            <Button type="button" variant="secondary" onClick={nearMe} disabled={locating || search.isPending} aria-label="Search near me">
              <LocateFixed className="h-4 w-4" aria-hidden="true" /> {locating ? "…" : "Near me"}
            </Button>
          </div>
        </form>
      </Card>

      <div className="mt-6">
        {search.isPending && <SkeletonRows count={4} />}
        {search.isError && <ErrorState message={errorMessage} />}

        {search.isIdle && (
          <EmptyState icon={Compass} title="Search any place to see who's there." description="Try “Gomti Nagar, Lucknow” or tap Near me." />
        )}

        {result && (
          <>
            <div className="mb-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-slate-600">
                <span className="font-medium text-slate-900">{places.length}</span> {cat.label.toLowerCase()} within {result.radius_km} km of{" "}
                <span className="font-medium text-slate-900">{result.center.label.split(",").slice(0, 3).join(",")}</span>
              </p>
              {googleList && (
                <a href={googleList} target="_blank" rel="noopener noreferrer">
                  <Button variant="secondary" className="w-full sm:w-auto">
                    <ExternalLink className="h-4 w-4" aria-hidden="true" /> Full list with ratings on Google Maps
                  </Button>
                </a>
              )}
            </div>

            {places.length === 0 ? (
              <EmptyState
                icon={MapPin}
                title="No listings found on the free map here."
                description="Try a bigger radius, a nearby area, or open the full Google Maps list above."
              />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="order-1 lg:order-2">
                  <div className="lg:sticky lg:top-20">
                    <DoctorsMap
                      height="60vh"
                      origin={{ lat: result.center.lat, lng: result.center.lng }}
                      points={places.map((p, i) => ({
                        id: p.id, lat: p.latitude, lng: p.longitude, title: p.name,
                        subtitle: [p.speciality, p.address].filter(Boolean).join(" · "), label: i + 1,
                      }))}
                    />
                  </div>
                </div>
                <ol className="order-2 space-y-3 lg:order-1">
                  {places.map((p, i) => (
                    <li key={p.id}>
                      <Card className="!p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div className="min-w-0">
                            <p className="font-medium text-slate-900">
                              <span className="mono mr-1.5 text-xs text-slate-400">{i + 1}.</span>{p.name}
                            </p>
                            <p className="text-sm text-slate-500">
                              {[p.speciality && p.speciality.charAt(0).toUpperCase() + p.speciality.slice(1), p.type_label].filter(Boolean).join(" · ")}
                            </p>
                            {p.address && <p className="mt-1 text-sm text-slate-600">{p.address}</p>}
                            {p.opening_hours && <p className="mt-1 text-xs text-slate-500">Hours: {p.opening_hours}</p>}
                          </div>
                          <span className="mono shrink-0 text-xs text-slate-500">{p.distance_km} km</span>
                        </div>
                        <div className="mt-3 flex flex-wrap gap-2">
                          {p.phone && (
                            <a href={`tel:${p.phone.split(/[;,]/)[0].replace(/\s+/g, "")}`}>
                              <Button className="!px-3 !py-1.5 text-xs"><PhoneCall className="h-3.5 w-3.5" aria-hidden="true" /> Call</Button>
                            </a>
                          )}
                          <a href={`https://www.google.com/maps/dir/?api=1&destination=${p.latitude},${p.longitude}`} target="_blank" rel="noopener noreferrer">
                            <Button variant="secondary" className="!px-3 !py-1.5 text-xs"><Navigation className="h-3.5 w-3.5" aria-hidden="true" /> Directions</Button>
                          </a>
                          <a href={p.google_maps_url} target="_blank" rel="noopener noreferrer">
                            <Button variant="secondary" className="!px-3 !py-1.5 text-xs"><ExternalLink className="h-3.5 w-3.5" aria-hidden="true" /> Reviews on Google</Button>
                          </a>
                        </div>
                      </Card>
                    </li>
                  ))}
                </ol>
              </div>
            )}
            <p className="mt-4 text-xs text-slate-400">
              Map data © OpenStreetMap contributors. Listings can be incomplete — use the Google Maps button for the full list.
            </p>
          </>
        )}
      </div>
    </div>
  );
}
