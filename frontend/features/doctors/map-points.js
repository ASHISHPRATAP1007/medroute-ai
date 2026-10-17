/** Turn DoctorOut rows into DoctorsMap points. */
export function doctorsToMapPoints(doctors, { hrefFor, specializations = [] } = {}) {
  return (doctors || []).map((d) => ({
    id: d.id,
    lat: d.latitude === null || d.latitude === undefined ? null : Number(d.latitude),
    lng: d.longitude === null || d.longitude === undefined ? null : Number(d.longitude),
    title: d.full_name,
    subtitle: [
      specializations.find((s) => s.id === d.specialization_id)?.name,
      [d.area, d.city].filter(Boolean).join(", "),
    ].filter(Boolean).join(" · "),
    href: hrefFor ? hrefFor(d) : undefined,
  }));
}

/** Google Maps search link for a doctor (no API key needed). */
export function googleMapsUrl(doctor) {
  if (doctor.latitude && doctor.longitude) {
    return `https://www.google.com/maps/search/?api=1&query=${doctor.latitude},${doctor.longitude}`;
  }
  if (doctor.address) {
    const q = [doctor.address, doctor.area, doctor.city].filter(Boolean).join(", ");
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(q)}`;
  }
  return undefined;
}
