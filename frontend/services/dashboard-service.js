import { apiRequest } from "@/lib/api-client";

export async function getAdminDashboard() {
  return apiRequest("/admin/dashboard");
}

export async function getMRDashboard() {
  return apiRequest("/mr/dashboard");
}
