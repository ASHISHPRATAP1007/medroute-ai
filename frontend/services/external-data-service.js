import { apiRequest } from "@/lib/api-client";

export async function getDoctorExternalData(doctorId) {
  return apiRequest(`/doctors/${doctorId}/external-data`);
}

export async function syncDoctorExternalData(doctorId) {
  return apiRequest(`/doctors/${doctorId}/sync-external`, { method: "POST" });
}
