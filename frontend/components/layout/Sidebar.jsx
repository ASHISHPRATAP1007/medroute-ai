"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import clsx from "clsx";
import { X } from "lucide-react";

export default function Sidebar({ items, open, onClose }) {
  const pathname = usePathname();

  const content = (
    <nav className="flex h-full flex-col gap-1 p-4">
      {items.map((item) => {
        const active = pathname === item.href || pathname?.startsWith(`${item.href}/`);
        return (
          <Link
            key={item.href}
            href={item.href}
            onClick={onClose}
            className={clsx(
              "flex items-center gap-2.5 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors relative",
              active ? "bg-primary-50 text-primary-700 before:absolute before:-left-3 before:top-2 before:bottom-2 before:w-[3px] before:rounded-full before:bg-signal-500" : "text-slate-600 hover:bg-slate-100"
            )}
          >
            <item.icon className="h-4.5 w-4.5" aria-hidden="true" />
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white sm:block">
        <div className="flex items-center gap-2 px-5 py-5 font-head text-lg font-bold text-slate-900">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M12 2L4 6v6c0 5 3.5 8.5 8 10 4.5-1.5 8-5 8-10V6l-8-4z" fill="#2B3A67" />
            <path d="M12 7v10M7.5 12h9" stroke="#E8A33D" strokeWidth="1.6" strokeLinecap="round" />
          </svg>
          MedRoute AI
        </div>
        {content}
      </aside>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 sm:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={onClose} aria-hidden="true" />
          <div className="absolute left-0 top-0 h-full w-72 bg-white shadow-lg">
            <div className="flex items-center justify-between border-b border-slate-100 p-4">
              <span className="font-head font-semibold text-slate-900">Menu</span>
              <button onClick={onClose} aria-label="Close menu" className="rounded-lg p-1.5 hover:bg-slate-100">
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>
            {content}
          </div>
        </div>
      )}
    </>
  );
}
