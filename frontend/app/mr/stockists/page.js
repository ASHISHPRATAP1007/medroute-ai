"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Phone, Mail, MapPin } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import { EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Pagination from "@/components/ui/Pagination";
import { listStockistsForMR } from "@/services/stockist-service";

export default function MRStockistsPage() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["mr-stockists", { search, city, area, page }],
    queryFn: () => listStockistsForMR({ search, city, area, page, page_size: 12 }),
  });

  const result = data?.data;

  return (
    <div>
      <PageHeader title="Stockists" description="Stockists and distributors within your assigned territory." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input id="mr-stockist-search" placeholder="Search stockist name…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="sm:max-w-xs" />
        <Input id="mr-stockist-city" placeholder="City" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
        <Input id="mr-stockist-area" placeholder="Area" value={area} onChange={(e) => { setArea(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
      </div>

      {isLoading && <SkeletonRows count={4} />}
      {isError && <ErrorState />}
      {result && result.items.length === 0 && <EmptyState title="No stockists found." />}

      {result && result.items.length > 0 && (
        <div className="grid gap-3 sm:grid-cols-2">
          {result.items.map((stockist) => (
            <div key={stockist.id} className="card p-4">
              <p className="font-medium text-slate-900">{stockist.name}</p>
              {stockist.company_name && <p className="text-sm text-slate-500">{stockist.company_name}</p>}
              <p className="mt-2 flex items-center gap-1 text-xs text-slate-400">
                <MapPin className="h-3.5 w-3.5" aria-hidden="true" />
                {[stockist.area, stockist.city].filter(Boolean).join(", ")}
              </p>
              {stockist.phone && <p className="mt-1 flex items-center gap-1 text-sm text-slate-600"><Phone className="h-3.5 w-3.5" aria-hidden="true" />{stockist.phone}</p>}
              {stockist.email && <p className="flex items-center gap-1 text-sm text-slate-600"><Mail className="h-3.5 w-3.5" aria-hidden="true" />{stockist.email}</p>}
            </div>
          ))}
        </div>
      )}

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}
    </div>
  );
}
