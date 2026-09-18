import { apiRequest } from "@/lib/api-client";

function toQueryString(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export async function listMRs(params) {
  return apiRequest(`/admin/mrs${toQueryString(params)}`);
}

export async function getMR(id) {
  return apiRequest(`/admin/mrs/${id}`);
}

export async function approveMR(id) {
  return apiRequest(`/admin/mrs/${id}/approve`, { method: "POST" });
}

export async function rejectMR(id) {
  return apiRequest(`/admin/mrs/${id}/reject`, { method: "POST" });
}

export async function suspendMR(id) {
  return apiRequest(`/admin/mrs/${id}/suspend`, { method: "POST" });
}

export async function activateMR(id) {
  return apiRequest(`/admin/mrs/${id}/activate`, { method: "POST" });
}
