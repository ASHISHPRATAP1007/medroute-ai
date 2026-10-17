import { apiRequest } from "@/lib/api-client";

/** Grouped search across doctors, shops, stockists (and MRs for admins). */
export async function globalSearch(q, limit = 5) {
  return apiRequest(`/search?q=${encodeURIComponent(q)}&limit=${limit}`);
}
