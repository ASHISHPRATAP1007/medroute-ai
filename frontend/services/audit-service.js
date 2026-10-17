import { apiRequest } from "@/lib/api-client";

export async function listAuditLogs(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== null && v !== "") query.set(k, v); });
  const qs = query.toString();
  return apiRequest(`/admin/audit-logs${qs ? `?${qs}` : ""}`);
}
