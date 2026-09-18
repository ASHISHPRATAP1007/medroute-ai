import clsx from "clsx";

export default function Button({ variant = "primary", className, children, ...props }) {
  const base = variant === "primary" ? "btn-primary" : variant === "danger"
    ? "inline-flex items-center justify-center gap-2 rounded-lg bg-danger-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-danger-700 disabled:opacity-50"
    : "btn-secondary";

  return (
    <button className={clsx(base, className)} {...props}>
      {children}
    </button>
  );
}
