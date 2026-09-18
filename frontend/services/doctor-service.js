import { apiRequest } from "@/lib/api-client";

function toQueryString(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") query.set(key, value);
  });
  const str = query.toString();
  return str ? `?${str}` : "";
}

export async function listDoctorsAdmin(params) {
  return apiRequest(`/doctors${toQueryString(params)}`);
}

export async function listDoctorsForMR(params) {
  return apiRequest(`/doctors/mine${toQueryString(params)}`);
}

export async function getDoctor(id) {
  return apiRequest(`/doctors/${id}`);
}

export async function createDoctor(payload) {
  return apiRequest("/doctors", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateDoctor(id, payload) {
  return apiRequest(`/doctors/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function deactivateDoctor(id) {
  return apiRequest(`/doctors/${id}/deactivate`, { method: "POST" });
}

export async function activateDoctor(id) {
  return apiRequest(`/doctors/${id}/activate`, { method: "POST" });
}

export async function listSpecializations() {
  return apiRequest("/specializations");
}
