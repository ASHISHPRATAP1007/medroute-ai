import { apiRequest } from "@/lib/api-client";

/** Search Google Places for doctors — returns candidates, saves nothing. */
export async function searchGoogleDoctors({ specialization_name, area, city, state }) {
  return apiRequest("/doctors/discovery/search", {
    method: "POST",
    body: JSON.stringify({ specialization_name, area, city, state }),
  });
}

/** Import one candidate into the doctor directory. */
export async function importGoogleDoctor({ place_id, specialization_id, area, city, state }) {
  return apiRequest("/doctors/discovery/import", {
    method: "POST",
    body: JSON.stringify({ place_id, specialization_id, area, city, state }),
  });
}
