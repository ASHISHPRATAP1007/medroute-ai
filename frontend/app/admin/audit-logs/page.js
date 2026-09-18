"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { PageHeader } from "@/components/ui/PageHeader";
import { Input } from "@/components/ui/FormFields";
import DataTable from "@/components/ui/DataTable";
import Pagination from "@/components/ui/Pagination";
import { apiRequest } from "@/lib/api-client";

async function listAuditLogs(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
  return apiRequest(`/admin/audit-logs?${query.toString()}`);
}

export default function AdminAuditLogsPage() {
  const [action, setAction] = useState("");
  const [page, setPage] = useState(1);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["audit-logs", { action, page }],
    queryFn: () => listAuditLogs({ action, page, page_size: 20 }),
  });

  const result = data?.data;
  const columns = [
    { key: "created_at", header: "Date", render: (row) => new Date(row.created_at).toLocaleString() },
    { key: "action", header: "Action" },
    { key: "entity_type", header: "Entity" },
    { key: "description", header: "Description" },
  ];

  return (
    <div>
      <PageHeader title="Audit Logs" description="A record of admin and system actions." />

      <div className="mb-4 flex flex-col gap-3 sm:flex-row">
        <Input id="audit-action" placeholder="Filter by action (e.g. MR_APPROVED)…" value={action}
          onChange={(e) => { setAction(e.target.value); setPage(1); }} className="sm:max-w-sm" />
      </div>

      <DataTable columns={columns} rows={result?.items} isLoading={isLoading} isError={isError} emptyMessage="No audit log entries found." />

      {result && <Pagination page={result.page} totalPages={result.total_pages} onPageChange={setPage} />}
    </div>
  );
}
