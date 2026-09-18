"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { SlidersHorizontal } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Pagination from "@/components/ui/Pagination";
import DoctorCard from "@/features/doctors/DoctorCard";
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

  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const specializations = specData?.data || [];

  const { data, isLoading, isError } = useQuery({
    queryKey: ["mr-doctors", { search, specializationId, city, area, sortBy, page }],
    queryFn: () =>
      listDoctorsForMR({
        search, specialization_id: specializationId, city, area,
        sort_by: sortBy, page, page_size: 12,
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
      <PageHeader title="Find a Doctor" description="Search doctors within your assigned territory." />

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

      {result && result.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {result.items.map((doctor) => (
            <DoctorCard
              key={doctor.id}
              doctor={{ ...doctor, specialization_name: specializations.find((s) => s.id === doctor.specialization_id)?.name }}
              mapUrl={
                doctor.latitude && doctor.longitude
                  ? `https://www.google.com/maps/search/?api=1&query=${doctor.latitude},${doctor.longitude}`
                  : doctor.address
                  ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(doctor.address)}`
                  : undefined
              }
            />
          ))}
        </div>
      )}

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}
    </div>
  );
}
