"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { SlidersHorizontal, List, Map as MapIcon } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Pagination from "@/components/ui/Pagination";
import ViewToggle from "@/components/ui/ViewToggle";
import DoctorCard from "@/features/doctors/DoctorCard";
import DoctorsMap from "@/features/doctors/DoctorsMap";
import { doctorsToMapPoints, googleMapsUrl } from "@/features/doctors/map-points";
import { listDoctorsForMR, listSpecializations } from "@/services/doctor-service";

const SORT_OPTIONS = [
  { value: "name", label: "Name" },
  { value: "recently_added", label: "Recently Added" },
  { value: "specialization", label: "Specialization" },
];

export default function MRDoctorsPage() {
  const [search, setSearch] = useState("");
  const [specializationId, setSpecializationId] = useState("");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [sortBy, setSortBy] = useState("name");
  const [page, setPage] = useState(1);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [view, setView] = useState("list");

  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const specializations = specData?.data || [];

  const isMap = view === "map";
  // The map shows every match on one screen (up to the API's 100-row page);
  // the list stays paginated.
  const { data, isLoading, isError } = useQuery({
    queryKey: ["mr-doctors", { search, specializationId, city, area, sortBy, page: isMap ? 1 : page, isMap }],
    queryFn: () =>
      listDoctorsForMR({
        search, specialization_id: specializationId, city, area,
        sort_by: sortBy, page: isMap ? 1 : page, page_size: isMap ? 100 : 12,
      }),
  });

  const result = data?.data;

  const filters = (
    <div className="grid gap-3 sm:grid-cols-4">
      <Select id="mr-doctor-specialization" value={specializationId}
        onChange={(e) => { setSpecializationId(e.target.value); setPage(1); }}
        options={[{ value: "", label: "All Specializations" }, ...specializations.map((s) => ({ value: s.id, label: s.name }))]} />
      <Input id="mr-doctor-city" placeholder="City" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }} />
      <Input id="mr-doctor-area" placeholder="Area" value={area} onChange={(e) => { setArea(e.target.value); setPage(1); }} />
      <Select id="mr-doctor-sort" value={sortBy} onChange={(e) => setSortBy(e.target.value)} options={SORT_OPTIONS} />
    </div>
  );

  return (
    <div>
      <PageHeader
        title="Find a Doctor"
        description="Search doctors within your assigned territory."
        actions={
          <ViewToggle
            value={view}
            onChange={setView}
            label="Doctor view"
            options={[{ value: "list", label: "List", icon: List }, { value: "map", label: "Map", icon: MapIcon }]}
          />
        }
      />

      <div className="mb-4 flex flex-col gap-3">
        <div className="flex gap-2">
          <Input
            id="mr-doctor-search"
            placeholder="Search doctor by name…"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="flex-1"
          />
          <button
            type="button"
            onClick={() => setFiltersOpen((v) => !v)}
            className="btn-secondary sm:hidden"
            aria-expanded={filtersOpen}
            aria-controls="mr-doctor-filters"
          >
            <SlidersHorizontal className="h-4 w-4" aria-hidden="true" />
            Filters
          </button>
        </div>
        <div id="mr-doctor-filters" className={filtersOpen ? "block" : "hidden sm:block"}>
          {filters}
        </div>
      </div>

      {isLoading && <SkeletonRows count={4} />}
      {isError && <ErrorState />}
      {result && result.items.length === 0 && (
        <EmptyState title="No doctors found in this area." description="Try adjusting your filters, or check with your admin about territory assignment." />
      )}

      {isMap && result && result.items.length > 0 && (
        <DoctorsMap
          points={doctorsToMapPoints(result.items, { specializations, hrefFor: (d) => `/mr/doctors/${d.id}` })}
          height="60vh"
        />
      )}

      {!isMap && result && result.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {result.items.map((doctor) => (
            <DoctorCard
              key={doctor.id}
              doctor={{ ...doctor, specialization_name: specializations.find((s) => s.id === doctor.specialization_id)?.name }}
              mapUrl={googleMapsUrl(doctor)}
            />
          ))}
        </div>
      )}

      {!isMap && result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}
    </div>
  );
}
