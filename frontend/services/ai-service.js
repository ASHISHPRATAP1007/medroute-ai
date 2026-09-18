import { apiRequest } from "@/lib/api-client";

export async function getDailyPlan(limit = 10) {
  return apiRequest(`/ai/daily-plan?limit=${limit}`);
}

export async function getOpportunityScore(doctorId) {
  return apiRequest(`/ai/doctors/${doctorId}/opportunity-score`);
}
