import clsx from "clsx";

export function Card({ className, children }) {
  return <div className={clsx("card p-5", className)}>{children}</div>;
}

export function EmptyState({ title = "Nothing here yet", description, icon: Icon }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      {Icon && <Icon className="mb-3 h-10 w-10 text-slate-300" aria-hidden="true" />}
      <p className="text-sm font-medium text-slate-700">{title}</p>
      {description && <p className="mt-1 max-w-sm text-sm text-slate-500">{description}</p>}
    </div>
  );
}

export function ErrorState({ message = "Something went wrong. Please try again." }) {
  return (
    <div role="alert" className="flex flex-col items-center justify-center rounded-xl border border-danger-100 bg-danger-50 py-10 text-center">
      <p className="text-sm font-medium text-danger-700">{message}</p>
    </div>
  );
}

export function Skeleton({ className }) {
  return <div className={clsx("animate-pulse rounded-lg bg-slate-200", className)} />;
}

export function SkeletonRows({ count = 5 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} className="h-14 w-full" />
      ))}
    </div>
  );
}
