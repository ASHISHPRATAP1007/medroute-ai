"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Building2, Search, Stethoscope, Truck, User, X } from "lucide-react";
import { useAuth } from "@/hooks/use-auth";
import { globalSearch } from "@/services/search-service";

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(t);
  }, [value, delay]);
  return debounced;
}

function buildGroups(data, isAdmin) {
  if (!data) return [];
  const base = isAdmin ? "/admin" : "/mr";
  const place = (row) => [row.area, row.city].filter(Boolean).join(", ");
  return [
    {
      key: "doctors", label: "Doctors", icon: Stethoscope,
      items: data.doctors.map((d) => ({ id: d.id, title: d.full_name, subtitle: d.clinic_name || place(d), href: `${base}/doctors/${d.id}` })),
    },
    {
      key: "medical_shops", label: "Medical shops", icon: Building2,
      items: data.medical_shops.map((s) => ({ id: s.id, title: s.name, subtitle: [place(s), s.phone].filter(Boolean).join(" · "), href: `${base}/medical-shops` })),
    },
    {
      key: "stockists", label: "Stockists", icon: Truck,
      items: data.stockists.map((s) => ({ id: s.id, title: s.name, subtitle: [place(s), s.phone].filter(Boolean).join(" · "), href: `${base}/stockists` })),
    },
    {
      key: "mrs", label: "Medical representatives", icon: User,
      items: (data.mrs || []).map((m) => ({ id: m.id, title: m.full_name, subtitle: `${m.email} · ${m.status}`, href: "/admin/mrs" })),
    },
  ].filter((g) => g.items.length > 0);
}

/**
 * Topbar search. Desktop: inline field with a dropdown. Mobile: a search icon
 * that opens a full-width panel under the header.
 */
export default function GlobalSearch() {
  const { user } = useAuth();
  const router = useRouter();
  const [term, setTerm] = useState("");
  const [open, setOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const boxRef = useRef(null);
  const debounced = useDebounced(term.trim());
  const isAdmin = user?.role === "ADMIN" || user?.role === "SUPER_ADMIN";

  const { data, isFetching, isError } = useQuery({
    queryKey: ["global-search", debounced],
    queryFn: () => globalSearch(debounced),
    enabled: debounced.length >= 2,
    staleTime: 15_000,
  });

  const groups = buildGroups(data?.data, isAdmin);
  const flat = groups.flatMap((g) => g.items);

  useEffect(() => {
    function onClick(e) {
      if (boxRef.current && !boxRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", onClick);
    return () => document.removeEventListener("mousedown", onClick);
  }, []);

  function close() {
    setOpen(false);
    setMobileOpen(false);
  }

  function onKeyDown(e) {
    if (e.key === "Escape") {
      close();
      e.currentTarget.blur();
    } else if (e.key === "Enter" && flat[0]) {
      e.preventDefault();
      router.push(flat[0].href);
      close();
    }
  }

  const showPanel = open && term.trim().length >= 2;

  const results = (
    <div className="max-h-[70vh] overflow-y-auto p-2">
      {debounced.length >= 2 && isFetching && !data && <p className="px-2 py-4 text-center text-sm text-slate-400">Searching…</p>}
      {isError && <p className="px-2 py-4 text-center text-sm text-danger-600">Search failed. Try again.</p>}
      {data && groups.length === 0 && (
        <p className="px-2 py-4 text-center text-sm text-slate-400">No matches for “{debounced}”.</p>
      )}
      {groups.map((group) => (
        <div key={group.key} className="mb-1">
          <p className="flex items-center gap-1.5 px-2 pb-1 pt-2 text-xs font-medium uppercase tracking-wide text-slate-400">
            <group.icon className="h-3.5 w-3.5" aria-hidden="true" /> {group.label}
          </p>
          <ul>
            {group.items.map((item) => (
              <li key={item.id}>
                <Link href={item.href} onClick={close} className="block rounded-lg px-2 py-1.5 hover:bg-slate-50 focus:bg-slate-50 focus:outline-none">
                  <span className="block truncate text-sm font-medium text-slate-900">{item.title}</span>
                  {item.subtitle && <span className="block truncate text-xs text-slate-500">{item.subtitle}</span>}
                </Link>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );

  const input = (autoFocus) => (
    <input
      type="search"
      value={term}
      autoFocus={autoFocus}
      onChange={(e) => { setTerm(e.target.value); setOpen(true); }}
      onFocus={() => setOpen(true)}
      onKeyDown={onKeyDown}
      placeholder={isAdmin ? "Search doctors, shops, stockists, MRs…" : "Search doctors, shops, stockists…"}
      aria-label="Search"
      className="w-full min-w-0 border-none bg-transparent text-sm outline-none placeholder:text-slate-400"
    />
  );

  return (
    <>
      {/* Desktop */}
      <div ref={boxRef} className="relative hidden sm:block">
        <div className="flex items-center gap-2 rounded-xl border border-slate-200 px-3 py-2 focus-within:border-primary-600 focus-within:ring-2 focus-within:ring-primary-100">
          <Search className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
          <div className="w-64 lg:w-80">{input(false)}</div>
        </div>
        {showPanel && (
          <div className="absolute left-0 z-50 mt-2 w-[26rem] max-w-[80vw] rounded-xl border border-slate-200 bg-white shadow-lg">
            {results}
          </div>
        )}
      </div>

      {/* Mobile */}
      <button
        type="button"
        onClick={() => { setMobileOpen(true); setOpen(true); }}
        className="rounded-lg p-1.5 hover:bg-slate-100 sm:hidden"
        aria-label="Search"
      >
        <Search className="h-5 w-5 text-slate-500" aria-hidden="true" />
      </button>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 sm:hidden" onClick={close}>
          <div className="bg-white shadow-lg" onClick={(e) => e.stopPropagation()}>
            <div className="flex items-center gap-2 border-b border-slate-200 px-4 py-3">
              <Search className="h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
              {input(true)}
              <button type="button" onClick={close} aria-label="Close search" className="rounded-lg p-1 hover:bg-slate-100">
                <X className="h-5 w-5 text-slate-500" aria-hidden="true" />
              </button>
            </div>
            {term.trim().length >= 2 ? results : <p className="px-4 py-4 text-sm text-slate-400">Type at least 2 letters.</p>}
          </div>
        </div>
      )}
    </>
  );
}
