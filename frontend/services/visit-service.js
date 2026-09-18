import { apiRequest } from "@/lib/api-client";

export async function planVisit(doctorId, scheduledDate) {
  return apiRequest("/visits", {
    method: "POST",
    body: JSON.stringify({ doctor_id: doctorId, scheduled_date: scheduledDate }),
  });
}

export async function listMyVisits(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => { if (v) query.set(k, v); });
  const qs = query.toString();
  return apiRequest(`/visits${qs ? `?${qs}` : ""}`);
}

export async function updateVisit(visitId, payload) {
  return apiRequest(`/visits/${visitId}`, { method: "PUT", body: JSON.stringify(payload) });
}

export async function getUpcomingFollowUps() {
  return apiRequest("/visits/follow-ups");
}

export async function getDailyRoute(targetDate) {
  const qs = targetDate ? `?target_date=${targetDate}` : "";
  return apiRequest(`/visits/daily-route${qs}`);
}

export async function getDoctorVisitHistory(doctorId) {
  return apiRequest(`/visits/doctors/${doctorId}/history`);
}
