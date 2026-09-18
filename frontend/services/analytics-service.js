import { apiRequest } from "@/lib/api-client";

export async function getMRPerformance() {
  return apiRequest("/admin/analytics/mr-performance");
}

export async function getTerritoryCoverage() {
  return apiRequest("/admin/analytics/territory-coverage");
}
