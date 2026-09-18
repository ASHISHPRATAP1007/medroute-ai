import { apiRequest } from "@/lib/api-client";

function toQueryString(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export async function listStockistsAdmin(params) {
  return apiRequest(`/stockists${toQueryString(params)}`);
}

export async function listStockistsForMR(params) {
  return apiRequest(`/stockists/mine${toQueryString(params)}`);
}

export async function createStockist(payload) {
  return apiRequest("/stockists", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateStockist(id, payload) {
  return apiRequest(`/stockists/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deactivateStockist(id) {
  return apiRequest(`/stockists/${id}/deactivate`, { method: "POST" });
}
