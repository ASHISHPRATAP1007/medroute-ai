"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, X } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import DataTable from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { Card } from "@/components/ui/Feedback";
import { useToast } from "@/components/ui/Toast";
import { stockistSchema } from "@/schemas/directory-schemas";
import { listStockistsAdmin, createStockist, deactivateStockist } from "@/services/stockist-service";

export default function AdminStockistsPage() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [pendingDeactivate, setPendingDeactivate] = useState(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-stockists", { search, city, area, page }],
    queryFn: () => listStockistsAdmin({ search, city, area, page, page_size: 20 }),
  });

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(stockistSchema) });

  const createMutation = useMutation({
    mutationFn: createStockist,
    onSuccess: () => {
      showToast("Stockist created.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-stockists"] });
      reset();
      setShowForm(false);
    },
    onError: (err) => showToast(err.message || "Failed to create stockist.", "error"),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id) => deactivateStockist(id),
    onSuccess: () => {
      showToast("Stockist deactivated.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-stockists"] });
      setPendingDeactivate(null);
    },
    onError: (err) => showToast(err.message || "Action failed.", "error"),
  });

  const result = data?.data;
  const columns = [
    { key: "name", header: "Name" },
    { key: "company_name", header: "Company" },
    { key: "area", header: "Area" },
    { key: "city", header: "City" },
    { key: "phone", header: "Phone" },
    { key: "status", header: "Status", render: (row) => <Badge status={row.status} /> },
  ];

  return (
    <div>
      <PageHeader
        title="Stockists"
        description="Manage the stockist/distributor directory."
        actions={<Button onClick={() => setShowForm((v) => !v)}>{showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}{showForm ? "Cancel" : "Add Stockist"}</Button>}
      />

      {showForm && (
        <Card className="mb-6 max-w-2xl">
          <form className="space-y-4" noValidate onSubmit={handleSubmit((values) => createMutation.mutate(values))}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Name" id="stockist_name" error={errors.name?.message} {...register("name")} />
              <Input label="Company Name" id="stockist_company" {...register("company_name")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Contact Person" id="stockist_contact" {...register("contact_person")} />
              <Input label="Phone" id="stockist_phone" {...register("phone")} />
            </div>
            <Input label="Email" id="stockist_email" type="email" error={errors.email?.message} {...register("email")} />
            <Input label="Address" id="stockist_address" error={errors.address?.message} {...register("address")} />
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Area" id="stockist_area" {...register("area")} />
              <Input label="City" id="stockist_city" error={errors.city?.message} {...register("city")} />
              <Input label="State" id="stockist_state" error={errors.state?.message} {...register("state")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Pincode" id="stockist_pincode" error={errors.pincode?.message} {...register("pincode")} />
              <Input label="Coverage Area" id="stockist_coverage" {...register("coverage_area")} />
            </div>
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Create Stockist"}</Button>
          </form>
        </Card>
      )}

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input id="stockist-search" placeholder="Search stockist name…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="sm:max-w-xs" />
        <Input id="stockist-city" placeholder="City" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
        <Input id="stockist-area" placeholder="Area" value={area} onChange={(e) => { setArea(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
      </div>

      <DataTable
        columns={columns} rows={result?.items} isLoading={isLoading} isError={isError}
        emptyMessage="No stockists found."
        rowActions={(stockist) => (
          <Button variant="danger" className="!px-3 !py-1.5 text-xs" disabled={stockist.status !== "ACTIVE"} onClick={() => setPendingDeactivate(stockist)}>
            Deactivate
          </Button>
        )}
      />

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}

      <ConfirmDialog
        open={!!pendingDeactivate}
        title={pendingDeactivate ? `Deactivate ${pendingDeactivate.name}?` : ""}
        description="MRs will no longer see this stockist in their discovery list."
        confirmLabel="Deactivate"
        variant="danger"
        onCancel={() => setPendingDeactivate(null)}
        onConfirm={() => deactivateMutation.mutate(pendingDeactivate.id)}
      />
    </div>
  );
}
