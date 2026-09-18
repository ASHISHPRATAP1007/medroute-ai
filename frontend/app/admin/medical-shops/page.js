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
import { shopSchema } from "@/schemas/directory-schemas";
import { listShopsAdmin, createShop, deactivateShop } from "@/services/shop-service";

export default function AdminMedicalShopsPage() {
  const [search, setSearch] = useState("");
  const [city, setCity] = useState("");
  const [area, setArea] = useState("");
  const [page, setPage] = useState(1);
  const [showForm, setShowForm] = useState(false);
  const [pendingDeactivate, setPendingDeactivate] = useState(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-shops", { search, city, area, page }],
    queryFn: () => listShopsAdmin({ search, city, area, page, page_size: 20 }),
  });

  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm({ resolver: zodResolver(shopSchema) });

  const createMutation = useMutation({
    mutationFn: createShop,
    onSuccess: () => {
      showToast("Medical shop created.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-shops"] });
      reset();
      setShowForm(false);
    },
    onError: (err) => showToast(err.message || "Failed to create shop.", "error"),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id) => deactivateShop(id),
    onSuccess: () => {
      showToast("Medical shop deactivated.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-shops"] });
      setPendingDeactivate(null);
    },
    onError: (err) => showToast(err.message || "Action failed.", "error"),
  });

  const result = data?.data;
  const columns = [
    { key: "name", header: "Name" },
    { key: "contact_person", header: "Contact" },
    { key: "area", header: "Area" },
    { key: "city", header: "City" },
    { key: "phone", header: "Phone" },
    { key: "status", header: "Status", render: (row) => <Badge status={row.status} /> },
  ];

  return (
    <div>
      <PageHeader
        title="Medical Shops"
        description="Manage the medical shop directory."
        actions={<Button onClick={() => setShowForm((v) => !v)}>{showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}{showForm ? "Cancel" : "Add Shop"}</Button>}
      />

      {showForm && (
        <Card className="mb-6 max-w-2xl">
          <form className="space-y-4" noValidate onSubmit={handleSubmit((values) => createMutation.mutate(values))}>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Name" id="shop_name" error={errors.name?.message} {...register("name")} />
              <Input label="Contact Person" id="shop_contact" {...register("contact_person")} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <Input label="Phone" id="shop_phone" {...register("phone")} />
              <Input label="Email" id="shop_email" type="email" error={errors.email?.message} {...register("email")} />
            </div>
            <Input label="Address" id="shop_address" error={errors.address?.message} {...register("address")} />
            <div className="grid gap-4 sm:grid-cols-3">
              <Input label="Area" id="shop_area" {...register("area")} />
              <Input label="City" id="shop_city" error={errors.city?.message} {...register("city")} />
              <Input label="State" id="shop_state" error={errors.state?.message} {...register("state")} />
            </div>
            <Input label="Pincode" id="shop_pincode" error={errors.pincode?.message} {...register("pincode")} />
            <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Saving…" : "Create Shop"}</Button>
          </form>
        </Card>
      )}

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input id="shop-search" placeholder="Search shop name…" value={search} onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="sm:max-w-xs" />
        <Input id="shop-city" placeholder="City" value={city} onChange={(e) => { setCity(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
        <Input id="shop-area" placeholder="Area" value={area} onChange={(e) => { setArea(e.target.value); setPage(1); }} className="sm:max-w-[160px]" />
      </div>

      <DataTable
        columns={columns} rows={result?.items} isLoading={isLoading} isError={isError}
        emptyMessage="No medical shops found."
        rowActions={(shop) => (
          <Button variant="danger" className="!px-3 !py-1.5 text-xs" disabled={shop.status !== "ACTIVE"} onClick={() => setPendingDeactivate(shop)}>
            Deactivate
          </Button>
        )}
      />

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}

      <ConfirmDialog
        open={!!pendingDeactivate}
        title={pendingDeactivate ? `Deactivate ${pendingDeactivate.name}?` : ""}
        description="MRs will no longer see this shop in their discovery list."
        confirmLabel="Deactivate"
        variant="danger"
        onCancel={() => setPendingDeactivate(null)}
        onConfirm={() => deactivateMutation.mutate(pendingDeactivate.id)}
      />
    </div>
  );
}
