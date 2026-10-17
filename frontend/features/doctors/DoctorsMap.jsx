"use client";

/**
 * Free map view — Leaflet + OpenStreetMap tiles. No Google Maps key, no billing.
 *
 * Leaflet touches `window` on import, so it is loaded lazily inside useEffect
 * (never during server rendering). Markers are CSS `divIcon`s rather than
 * Leaflet's default PNG pins, whose image paths break under bundlers.
 *
 * Props:
 *  - points: [{ id, lat, lng, title, subtitle?, href?, label? }]
 *      `label` (e.g. a stop number) is drawn inside the pin.
 *  - route: boolean — connect the points in order with a line (daily route).
 *  - origin: { lat, lng } | null — "you are here" marker; also the start of the route line.
 *  - height: CSS height of the map (default 420px).
 */
import "leaflet/dist/leaflet.css";
import { useEffect, useRef } from "react";

const TILE_URL = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png";
const ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';
const INDIA_CENTER = [22.5937, 78.9629];

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function pinIcon(L, label, variant = "doctor") {
  const bg = variant === "origin" ? "#E8A33D" : "#2B3A67";
  const size = variant === "origin" ? 18 : 28;
  const html = variant === "origin"
    ? `<span style="display:block;width:${size}px;height:${size}px;border-radius:9999px;background:${bg};border:3px solid #fff;box-shadow:0 0 0 2px ${bg}66"></span>`
    : `<span style="display:flex;align-items:center;justify-content:center;width:${size}px;height:${size}px;border-radius:9999px 9999px 9999px 0;transform:rotate(-45deg);background:${bg};border:2px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.35)"><span style="transform:rotate(45deg);color:#fff;font:600 11px/1 'IBM Plex Mono',monospace">${escapeHtml(label ?? "")}</span></span>`;
  return L.divIcon({
    html,
    className: "medroute-pin",
    iconSize: [size, size],
    iconAnchor: variant === "origin" ? [size / 2, size / 2] : [size / 2, size],
    popupAnchor: [0, variant === "origin" ? -size / 2 : -size],
  });
}

export default function DoctorsMap({ points = [], route = false, origin = null, height = "420px" }) {
  const containerRef = useRef(null);
  const mapRef = useRef(null);
  const layerRef = useRef(null);
  const leafletRef = useRef(null);
  // Latest props, read by draw(): the map finishes loading asynchronously, and
  // by then the closure from the first render would hold stale (empty) points.
  const propsRef = useRef({ points, route, origin });
  propsRef.current = { points, route, origin };

  // Create the map once.
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const mod = await import("leaflet");
      const L = mod.default || mod;
      if (cancelled || !containerRef.current || mapRef.current) return;
      leafletRef.current = L;
      const map = L.map(containerRef.current, { scrollWheelZoom: false }).setView(INDIA_CENTER, 5);
      L.tileLayer(TILE_URL, { attribution: ATTRIBUTION, maxZoom: 19 }).addTo(map);
      layerRef.current = L.layerGroup().addTo(map);
      mapRef.current = map;
      draw();
    })();
    return () => {
      cancelled = true;
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        layerRef.current = null;
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Redraw markers whenever the data changes.
  useEffect(() => {
    draw();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [points, route, origin]);

  function draw() {
    const L = leafletRef.current;
    const map = mapRef.current;
    const layer = layerRef.current;
    if (!L || !map || !layer) return;
    const { points, route, origin } = propsRef.current;
    layer.clearLayers();

    const located = points.filter((p) => Number.isFinite(Number(p.lat)) && Number.isFinite(Number(p.lng)) && p.lat !== null && p.lng !== null);
    const bounds = [];

    if (origin) {
      const o = [Number(origin.lat), Number(origin.lng)];
      L.marker(o, { icon: pinIcon(L, null, "origin"), title: "You are here" })
        .bindPopup("<strong>You are here</strong>")
        .addTo(layer);
      bounds.push(o);
    }

    located.forEach((p) => {
      const latLng = [Number(p.lat), Number(p.lng)];
      bounds.push(latLng);
      const link = p.href ? `<a href="${escapeHtml(p.href)}" style="display:inline-block;margin-top:6px;font-weight:600;color:#2B3A67">Open profile →</a>` : "";
      const popup = `<div style="min-width:160px"><strong>${escapeHtml(p.title)}</strong>${p.subtitle ? `<br/><span style="color:#64748b">${escapeHtml(p.subtitle)}</span>` : ""}${link ? `<br/>${link}` : ""}</div>`;
      L.marker(latLng, { icon: pinIcon(L, p.label), title: p.title }).bindPopup(popup).addTo(layer);
    });

    if (route && located.length > 0) {
      const line = located.map((p) => [Number(p.lat), Number(p.lng)]);
      if (origin) line.unshift([Number(origin.lat), Number(origin.lng)]);
      if (line.length > 1) {
        L.polyline(line, { color: "#E8A33D", weight: 4, opacity: 0.85, dashArray: "8 6" }).addTo(layer);
      }
    }

    if (bounds.length === 1) map.setView(bounds[0], 14);
    else if (bounds.length > 1) map.fitBounds(bounds, { padding: [32, 32], maxZoom: 15 });
    // Container may have just become visible (list -> map toggle).
    setTimeout(() => map.invalidateSize(), 0);
  }

  const missing = points.length - points.filter((p) => p.lat !== null && p.lat !== undefined && p.lng !== null && p.lng !== undefined).length;

  return (
    <div>
      <div
        ref={containerRef}
        style={{ height }}
        className="relative z-0 w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-100"
        role="region"
        aria-label="Map of doctor locations"
      />
      {missing > 0 && (
        <p className="mt-2 text-xs text-slate-500">
          {missing} {missing === 1 ? "doctor has" : "doctors have"} no coordinates on file and {missing === 1 ? "isn't" : "aren't"} shown on the map.
        </p>
      )}
    </div>
  );
}
