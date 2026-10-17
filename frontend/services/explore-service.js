import { apiRequest } from "@/lib/api-client";

/**
 * Free Explore (OpenStreetMap) — healthcare places around any place or GPS point.
 * params: { category, location?, lat?, lng?, radius_km?, keyword? }
 */
export async function explorePlaces(params) {
  const query = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") query.set(k, v);
  });
  return apiRequest(`/explore/places?${query.toString()}`);
}
