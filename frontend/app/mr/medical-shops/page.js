"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Phone, Mail, MapPin } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Pagination from "@/components/ui/Pagination";
import { listShopsForMR } from "@/services/shop-service";

export default function MRMedicalShopsPage() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["mr-shops", { search, city, area, page }],
    queryFn: () => listShopsForMR({ search, city, area, page, page_size: 12 }),
  });

  const result = data?.data;

  return (
    <div>
      <PageHeader title="Medical Shops" description="Medical shops within your assigned territory." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input id="mr-shop-search" placeholder="Search shop name…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="sm:max-w-xs" />
        <Input id="mr-shop-city" placeholder="City" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
        <Input id="mr-shop-area" placeholder="Area" value={area} onChange={(e) => { setArea(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
      </div>

      {isLoading && <SkeletonRows count={4} />}
      {isError && <ErrorState />}
      {result && result.items.length === 0 && <EmptyState title="No medical shops found." />}

      {result && result.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {result.items.map((shop) => (
            <div key={shop.id} className="card p-4">
              <p className="font-medium text-slate-900">{shop.name}</p>
              {shop.contact_person && <p className="text-sm text-slate-500">{shop.contact_person}</p>}
              <p className="mt-2 flex items-center gap-1 text-xs text-slate-400">
                <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
                {[shop.area, shop.city].filter(Boolean).join(", ")}
              </p>
              {shop.phone && <p className="mt-1 flex items-center gap-1 text-sm text-slate-600"><Phone className="h-3.5 w-3.5" aria-hidden="true" />{shop.phone}</p>}
              {shop.email && <p className="flex items-center gap-1 text-sm text-slate-600"><Mail className="h-3.5 w-3.5" aria-hidden="true" />{shop.email}</p>}
            </div>
          ))}
        </div>
      )}

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}
    </div>
  );
}
