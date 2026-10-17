/**
 * Today's date as YYYY-MM-DD in the user's *local* timezone.
 *
 * `new Date().toISOString().slice(0, 10)` gives the UTC date, which in India
 * (UTC+5:30) is still "yesterday" until 5:30 AM — so a visit planned early in
 * the morning would land on the wrong day.
 */
export function localISODate(date = new Date()) {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}

/** "2026-10-17" -> "Sat, 17 Oct 2026" (parsed as a local date, not UTC). */
export function formatISODate(iso) {
  if (!iso) return "";
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d).toLocaleDateString(undefined, {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}
