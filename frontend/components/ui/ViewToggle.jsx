"use client";

import clsx from "clsx";

/** Segmented control, e.g. List | Map. options: [{ value, label, icon }] */
export default function ViewToggle({ value, onChange, options, label = "View" }) {
  return (
    <div role="group" aria-label={label} className="inline-flex rounded-lg border border-slate-300 bg-white p-0.5">
      {options.map((opt) => {
        const active = opt.value === value;
        const Icon = opt.icon;
        return (
          <button
            key={opt.value}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(opt.value)}
            className={clsx(
              "inline-flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              active ? "bg-primary-600 text-white" : "text-slate-600 hover:bg-slate-100"
            )}
          >
            {Icon && <Icon className="h-4 w-4" aria-hidden="true" />}
            {opt.label}
          </button>
        );
      })}
    </div>
  );
}
