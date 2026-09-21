import { forwardRef } from "react";
import clsx from "clsx";

export const Input = forwardRef(function Input({ label, error, id, className, ...props }, ref) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <input
        id={id}
        ref={ref}
        className={clsx("input-field", error && "border-danger-500 focus:border-danger-500 focus:ring-danger-100", className)}
        aria-invalid={!!error}
        aria-describedby={error ? `${id}-error` : undefined}
        {...props}
      />
      {error && (
        <p id={`${id}-error`} className="text-xs text-danger-600">
          {error}
        </p>
      )}
    </div>
  );
});

export const Select = forwardRef(function Select({ label, error, id, options = [], className, ...props }, ref) {
  return (
    <div className="space-y-1.5">
      {label && (
        <label htmlFor={id} className="block text-sm font-medium text-slate-700">
          {label}
        </label>
      )}
      <select
        id={id}
        ref={ref}
        className={clsx("input-field", error && "border-danger-500", className)}
        aria-invalid={!!error}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && <p className="text-xs text-danger-600">{error}</p>}
    </div>
  );
});
