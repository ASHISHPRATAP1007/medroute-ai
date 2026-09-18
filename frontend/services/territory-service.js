import { apiRequest } from "@/lib/api-client";

export async function listCities() {
  return apiRequest("/cities");
}

export async function createCity(payload) {
  return apiRequest("/cities", { method: "POST", body: JSON.stringify(payload) });
}

export async function listAreas(cityId) {
  const qs = cityId ? `?city_id=${cityId}` : "";
  return apiRequest(`/areas${qs}`);
}

export async function createArea(payload) {
  return apiRequest("/areas", { method: "POST", body: JSON.stringify(payload) });
}

export async function listTerritories() {
  return apiRequest("/territories");
}

export async function listMyTerritories() {
  return apiRequest("/territories/mine");
}

export async function createTerritory(payload) {
  return apiRequest("/territories", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateTerritory(id, payload) {
  return apiRequest(`/territories/${id}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function assignMRToTerritory(territoryId, mrId) {
  return apiRequest(`/territories/${territoryId}/assign-mr`, {
    method: "POST",
    body: JSON.stringify({ mr_id: mrId }),
  });
}

export async function removeMRFromTerritory(territoryId, mrId) {
  return apiRequest(`/territories/${territoryId}/remove-mr`, {
    method: "POST",
    body: JSON.stringify({ mr_id: mrId }),
  });
}
