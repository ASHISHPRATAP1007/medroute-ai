"use client";

import { useState } from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Check, Download, Globe, MapPin, Search, Star } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import { Card, EmptyState, ErrorState, SkeletonRows } from "@/components/ui/Feedback";
import Button from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import DoctorsMap from "@/features/doctors/DoctorsMap";
import { listSpecializations } from "@/services/doctor-service";
import { importGoogleDoctor, searchGoogleDoctors } from "@/services/discovery-service";

export default function DiscoverDoctorsPage() {
  const { showToast } = useToast();
  const queryClient = useQueryClient();
  const [lastSearch, setLastSearch] = useState(null); // { specialization_id, specialization_name, area, city, state }
  const [imported, setImported] = useState({}); // place_id -> doctor id

  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const specializations = specData?.data || [];

  const { register, handleSubmit, formState: { errors } } = useForm({
    defaultValues: { specialization_id: "", area: "", city: "", state: "" },
  });

  const searchMutation = useMutation({
    mutationFn: (criteria) => searchGoogleDoctors(criteria),
    onError: (err) => showToast(err.message || "Search failed.", "error"),
  });

  const importMutation = useMutation({
    mutationFn: (candidate) => importGoogleDoctor({
      place_id: candidate.place_id,
      specialization_id: lastSearch.specialization_id,
      area: lastSearch.area,
      city: lastSearch.city,
      state: lastSearch.state,
    }),
    onSuccess: (res, candidate) => {
      setImported((prev) => ({ ...prev, [candidate.place_id]: res.data.id }));
      showToast(res.message || `${candidate.name} imported.`, "success");
      queryClient.invalidateQueries({ queryKey: ["admin-doctors"] });
    },
    onError: (err) => showToast(err.message || "Import failed.", "error"),
  });

  function onSearch(values) {
    const spec = specializations.find((s) => s.id === values.specialization_id);
    const criteria = {
      specialization_id: values.specialization_id,
      specialization_name: spec?.name || "",
      area: values.area.trim(),
      city: values.city.trim(),
      state: values.state.trim(),
    };
    setLastSearch(criteria);
    setImported({});
    searchMutation.mutate(criteria);
  }

  const candidates = searchMutation.data?.data || [];
  const notConfigured = searchMutation.error?.status === 503;

  return (
    <div>
      <Link href="/admin/doctors" className="mb-3 inline-flex items-center gap-1 text-sm font-medium text-primary-600 hover:underline">
        <ArrowLeft className="h-4 w-4" aria-hidden="true" /> Back to doctors
      </Link>
      <PageHeader
        title="Discover doctors from Google"
        description="Search real clinics on Google Places, review them, and import the ones you want. Nothing is saved until you click Import."
      />

      <Card>
        <form className="grid gap-3 sm:grid-cols-5 sm:items-end" onSubmit={handleSubmit(onSearch)} noValidate>
          <Select
            label="Specialization"
            id="disc-spec"
            error={errors.specialization_id && "Pick a specialization"}
            options={[{ value: "", label: "Select…" }, ...specializations.map((s) => ({ value: s.id, label: s.name }))]}
            {...register("specialization_id", { required: true })}
          />
          <Input label="Area (optional)" id="disc-area" placeholder="e.g. Gomti Nagar" {...register("area")} />
          <Input label="City" id="disc-city" placeholder="e.g. Lucknow" error={errors.city && "Required"} {...register("city", { required: true, minLength: 2 })} />
          <Input label="State" id="disc-state" placeholder="e.g. Uttar Pradesh" error={errors.state && "Required"} {...register("state", { required: true, minLength: 2 })} />
          <Button type="submit" disabled={searchMutation.isPending}>
            <Search className="h-4 w-4" aria-hidden="true" />
            {searchMutation.isPending ? "Searching…" : "Search Google"}
          </Button>
        </form>
        <p className="mt-3 text-xs text-slate-500">
          Each search and each import is one billed Google Places request on your API key.
        </p>
      </Card>

      <div className="mt-6">
        {searchMutation.isPending && <SkeletonRows count={4} />}

        {notConfigured && (
          <Card className="border-warning-500/40 bg-warning-50">
            <h2 className="flex items-center gap-2 font-medium text-warning-700"><Globe className="h-4 w-4" aria-hidden="true" /> Google Places isn&apos;t set up yet</h2>
            <ol className="mt-2 list-decimal space-y-1 pl-5 text-sm text-slate-700">
              <li>In Google Cloud Console, enable <strong>Places API (New)</strong> and link a billing account.</li>
              <li>Create an API key (restrict it to Places API (New)).</li>
              <li>On the backend set <code className="mono">GOOGLE_PLACES_ENABLED=true</code> and <code className="mono">GOOGLE_PLACES_API_KEY=&lt;your key&gt;</code>, then restart it.</li>
            </ol>
          </Card>
        )}
        {searchMutation.isError && !notConfigured && <ErrorState message={searchMutation.error.message} />}

        {searchMutation.isSuccess && candidates.length === 0 && (
          <EmptyState icon={Search} title="No doctors found." description="Try a nearby area, or leave Area empty to search the whole city." />
        )}

        {candidates.length > 0 && (
          <div className="grid gap-4 lg:grid-cols-2">
            <div className="order-2 space-y-3 lg:order-1">
              <p className="text-sm text-slate-500">{candidates.length} result{candidates.length === 1 ? "" : "s"} from Google</p>
              {candidates.map((c, i) => {
                const doneId = imported[c.place_id];
                const already = c.already_imported || !!doneId;
                return (
                  <Card key={c.place_id} className="!p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900">
                          <span className="mono mr-1.5 text-xs text-slate-400">{i + 1}.</span>{c.name}
                        </p>
                        {c.address && (
                          <p className="mt-1 flex items-start gap-1 text-sm text-slate-500">
                            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />{c.address}
                          </p>
                        )}
                        {c.rating != null && (
                          <p className="mt-1 flex items-center gap-1 text-sm text-slate-600">
                            <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" aria-hidden="true" />
                            {c.rating} <span className="text-slate-400">({c.user_ratings_total ?? 0})</span>
                          </p>
                        )}
                      </div>
                      {already ? (
                        doneId ? (
                          <Link href={`/admin/doctors/${doneId}`} className="shrink-0">
                            <Button variant="secondary" className="!px-3 !py-1.5 text-xs"><Check className="h-3.5 w-3.5" aria-hidden="true" />Imported</Button>
                          </Link>
                        ) : (
                          <span className="badge shrink-0 bg-success-50 text-success-700">In directory</span>
                        )
                      ) : (
                        <Button
                          className="shrink-0 !px-3 !py-1.5 text-xs"
                          disabled={importMutation.isPending && importMutation.variables?.place_id === c.place_id}
                          onClick={() => importMutation.mutate(c)}
                        >
                          <Download className="h-3.5 w-3.5" aria-hidden="true" />
                          {importMutation.isPending && importMutation.variables?.place_id === c.place_id ? "Importing…" : "Import"}
                        </Button>
                      )}
                    </div>
                  </Card>
                );
              })}
            </div>
            <div className="order-1 lg:order-2">
              <div className="lg:sticky lg:top-4">
                <DoctorsMap
                  height="60vh"
                  points={candidates.map((c, i) => ({
                    id: c.place_id, lat: c.latitude, lng: c.longitude, title: c.name, subtitle: c.address, label: i + 1,
                  }))}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
