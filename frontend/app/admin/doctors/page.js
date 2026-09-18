"use client";

import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { Plus, Download, Upload } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import DataTable from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useToast } from "@/components/ui/Toast";
import { listDoctorsAdmin, listSpecializations, deactivateDoctor, activateDoctor } from "@/services/doctor-service";
import { exportDoctorsCsv, importDoctorsCsv } from "@/services/bulk-service";

export default function AdminDoctorsPage() {
  const [search, setSearch] = useState("");
  const [specializationId, setSpecializationId] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState("name");
  const [sortOrder, setSortOrder] = useState("asc");
  const [pendingToggle, setPendingToggle] = useState(null);
  const fileInputRef = useRef(null);
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data: specData } = useQuery({ queryKey: ["specializations"], queryFn: listSpecializations });
  const specializations = specData?.data || [];

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-doctors", { search, specializationId, status, page, sortBy, sortOrder }],
    queryFn: () =>
      listDoctorsAdmin({
        search, specialization_id: specializationId, status, page, page_size: 20,
        sort_by: sortBy, sort_order: sortOrder,
      }),
  });

  const mutation = useMutation({
    mutationFn: ({ doctor }) => (doctor.status === "ACTIVE" ? deactivateDoctor(doctor.id) : activateDoctor(doctor.id)),
    onSuccess: () => {
      showToast("Doctor status updated.", "success");
      queryClient.invalidateQueries({ queryKey: ["admin-doctors"] });
      setPendingToggle(null);
    },
    onError: (err) => showToast(err.message || "Action failed.", "error"),
  });

  const importMutation = useMutation({
    mutationFn: (file) => importDoctorsCsv(file),
    onSuccess: (res) => {
      const { created, skipped, errors } = res.data;
      showToast(`Imported ${created}, skipped ${skipped}.${errors.length ? " See details." : ""}`, errors.length ? "info" : "success");
      queryClient.invalidateQueries({ queryKey: ["admin-doctors"] });
    },
    onError: (err) => showToast(err.message || "Import failed.", "error"),
  });

  async function handleExport() {
    try {
      const blob = await exportDoctorsCsv();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "doctors_export.csv";
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      showToast(err.message || "Export failed.", "error");
    }
  }

  function handleImportClick() {
    fileInputRef.current?.click();
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0];
    if (file) importMutation.mutate(file);
    e.target.value = "";
  }

  const result = data?.data;

  function handleSort(key) {
    const map = { full_name: "name", created_at: "recently_added" };
    const sortKey = map[key] || key;
    if (sortBy === sortKey) setSortOrder(sortOrder === "asc" ? "desc" : "asc");
    else { setSortBy(sortKey); setSortOrder("asc"); }
  }

  const columns = [
    { key: "full_name", header: "Name", sortable: true },
    { key: "clinic_name", header: "Clinic" },
    { key: "hospital_name", header: "Hospital" },
    { key: "area", header: "Area" },
    { key: "city", header: "City" },
    { key: "phone", header: "Phone" },
    { key: "status", header: "Status", render: (row) => <Badge status={row.status} /> },
  ];

  return (
    <div>
      <PageHeader
        title="Doctors"
        description="Manage the doctor directory available to your MRs."
        actions={
          <>
            <input ref={fileInputRef} type="file" accept=".csv" className="hidden" onChange={handleFileChange} />
            <Button variant="secondary" onClick={handleImportClick} disabled={importMutation.isPending}>
              <Upload className="h-4 w-4" aria-hidden="true" />
              {importMutation.isPending ? "Importing…" : "Import CSV"}
            </Button>
            <Button variant="secondary" onClick={handleExport}>
              <Download className="h-4 w-4" aria-hidden="true" />
              Export CSV
            </Button>
            <Link href="/admin/doctors/new">
              <Button><Plus className="h-4 w-4" aria-hidden="true" />Add Doctor</Button>
            </Link>
          </>
        }
      />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
        <Input id="doctor-search" placeholder="Search doctor name…" value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }} className="sm:max-w-xs" />
        <Select id="doctor-specialization" className="sm:max-w-[200px]" value={specializationId}
          onChange={(e) => { setSpecializationId(e.target.value); setPage(1); }}
          options={[{ value: "", label: "All Specializations" }, ...specializations.map((s) => ({ value: s.id, label: s.name }))]} />
        <Select id="doctor-status" className="sm:max-w-[160px]" value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          options={[{ value: "", label: "All Statuses" }, { value: "ACTIVE", label: "Active" }, { value: "INACTIVE", label: "Inactive" }]} />
      </div>

      <DataTable
        columns={columns}
        rows={result?.items}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="No doctors found in this area."
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSort={handleSort}
        rowActions={(doctor) => (
          <div className="flex justify-end gap-2">
            <Link href={`/admin/doctors/${doctor.id}`}>
              <Button variant="secondary" className="!px-3 !py-1.5 text-xs">Edit</Button>
            </Link>
            <Button
              variant={doctor.status === "ACTIVE" ? "danger" : "primary"}
              className="!px-3 !py-1.5 text-xs"
              onClick={() => setPendingToggle(doctor)}
            >
              {doctor.status === "ACTIVE" ? "Deactivate" : "Reactivate"}
            </Button>
          </div>
        )}
      />

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}

      <ConfirmDialog
        open={!!pendingToggle}
        title={pendingToggle ? `${pendingToggle.status === "ACTIVE" ? "Deactivate" : "Reactivate"} ${pendingToggle.full_name}?` : ""}
        description="This changes whether MRs can discover this doctor."
        confirmLabel={pendingToggle?.status === "ACTIVE" ? "Deactivate" : "Reactivate"}
        variant={pendingToggle?.status === "ACTIVE" ? "danger" : "primary"}
        onCancel={() => setPendingToggle(null)}
        onConfirm={() => mutation.mutate({ doctor: pendingToggle })}
      />
    </div>
  );
}
