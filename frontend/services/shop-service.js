import { apiRequest } from "@/lib/api-client";

function toQueryString(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export async function listShopsAdmin(params) {
  return apiRequest(`/medical-shops${toQueryString(params)}`);
}

export async function listShopsForMR(params) {
  return apiRequest(`/medical-shops/mine${toQueryString(params)}`);
}

export async function createShop(payload) {
  return apiRequest("/medical-shops", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateShop(id, payload) {
  return apiRequest(`/medical-shops/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deactivateShop(id) {
  return apiRequest(`/medical-shops/${id}/deactivate`, { method: "POST" });
}
