"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input, Select } from "@/components/ui/FormFields";
import DataTable from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import Badge from "@/components/ui/Badge";
import Button from "@/components/ui/Button";
import ConfirmDialog from "@/components/ui/ConfirmDialog";
import { useToast } from "@/components/ui/Toast";
import { listMRs, approveMR, rejectMR, suspendMR, activateMR } from "@/services/mr-service";

const STATUS_OPTIONS = [
  { value: "", label: "All Statuses" },
  { value: "PENDING", label: "Pending" },
  { value: "APPROVED", label: "Approved" },
  { value: "REJECTED", label: "Rejected" },
  { value: "SUSPENDED", label: "Suspended" },
];

const ACTIONS = {
  approve: { fn: approveMR, label: "approve", confirmLabel: "Approve", message: "This MR will gain access to the MR application." },
  reject: { fn: rejectMR, label: "reject", confirmLabel: "Reject", message: "This MR will not be able to log in." },
  suspend: { fn: suspendMR, label: "suspend", confirmLabel: "Suspend", message: "This MR will immediately lose access." },
  activate: { fn: activateMR, label: "reactivate", confirmLabel: "Reactivate", message: "This MR will regain access." },
};

export default function AdminMRsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [pendingAction, setPendingAction] = useState(null); // { type, mr }
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  const { data, isLoading, isError } = useQuery({
    queryKey: ["admin-mrs", { search, status, page }],
    queryFn: () => listMRs({ search, status, page, page_size: 20 }),
  });

  const mutation = useMutation({
    mutationFn: ({ type, mr }) => ACTIONS[type].fn(mr.id),
    onSuccess: (_, { type }) => {
      showToast(`MR ${ACTIONS[type].label}d successfully.`, "success");
      queryClient.invalidateQueries({ queryKey: ["admin-mrs"] });
      setPendingAction(null);
    },
    onError: (err) => {
      showToast(err.message || "Action failed.", "error");
      setPendingAction(null);
    },
  });

  const result = data?.data;

  const columns = [
    { key: "full_name", header: "Name", sortable: false },
    { key: "email", header: "Email" },
    { key: "phone", header: "Phone" },
    { key: "employee_id", header: "Employee ID", render: (row) => row.mr_profile?.employee_id || "—" },
    { key: "status", header: "Status", render: (row) => <Badge status={row.status} /> },
  ];

  function rowActions(mr) {
    return (
      <div className="flex justify-end gap-2">
        {mr.status === "PENDING" && (
          <>
            <Button className="!px-3 !py-1.5 text-xs" onClick={() => setPendingAction({ type: "approve", mr })}>Approve</Button>
            <Button variant="danger" className="!px-3 !py-1.5 text-xs" onClick={() => setPendingAction({ type: "reject", mr })}>Reject</Button>
          </>
        )}
        {mr.status === "APPROVED" && (
          <Button variant="danger" className="!px-3 !py-1.5 text-xs" onClick={() => setPendingAction({ type: "suspend", mr })}>Suspend</Button>
        )}
        {mr.status === "SUSPENDED" && (
          <Button className="!px-3 !py-1.5 text-xs" onClick={() => setPendingAction({ type: "activate", mr })}>Reactivate</Button>
        )}
      </div>
    );
  }

  return (
    <div>
      <PageHeader title="MR Management" description="Review, approve, and manage Medical Representative accounts." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input
          id="mr-search"
          placeholder="Search by name, email, or phone…"
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          className="sm:max-w-xs"
        />
        <Select
          id="mr-status-filter"
          options={STATUS_OPTIONS}
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="sm:max-w-[180px]"
        />
      </div>

      <DataTable
        columns={columns}
        rows={result?.items}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="No medical representatives found."
        rowActions={rowActions}
      />

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}

      <ConfirmDialog
        open={!!pendingAction}
        title={pendingAction ? `${ACTIONS[pendingAction.type].confirmLabel} ${pendingAction.mr.full_name}?` : ""}
        description={pendingAction ? ACTIONS[pendingAction.type].message : ""}
        confirmLabel={pendingAction ? ACTIONS[pendingAction.type].confirmLabel : ""}
        variant={pendingAction?.type === "reject" || pendingAction?.type === "suspend" ? "danger" : "primary"}
        onCancel={() => setPendingAction(null)}
        onConfirm={() => mutation.mutate(pendingAction)}
      />
    </div>
  );
}
