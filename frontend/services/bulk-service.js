import { getAccessToken } from "@/lib/api-client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function exportDoctorsCsv() {
  const token = getAccessToken();
  const res = await fetch(`${API_BASE_URL}/doctors/export`, {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (!res.ok) throw new Error("Failed to export doctors.");
  return res.blob();
}

export async function importDoctorsCsv(file) {
  const token = getAccessToken();
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/doctors/import`, {
    method: "POST",
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: formData,
    // Deliberately no Content-Type header — the browser sets the
    // multipart/form-data boundary automatically.
  });

  const body = await res.json();
  if (!res.ok) throw new Error(body?.message || "Import failed.");
  return body;
}
