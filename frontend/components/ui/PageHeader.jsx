export function PageHeader({ title, description, actions }) {
  return (
    <div className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 className="text-xl font-bold text-slate-900">{title}</h1>
        {description && <p className="mt-1 text-sm text-slate-500">{description}</p>}
      </div>
      {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
    </div>
  );
}

export function StatCard({ label, value, icon: Icon }) {
  return (
    <div className="card flex items-center justify-between p-5">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="font-head mt-1 text-3xl font-bold text-slate-900">{value}</p>
      </div>
      {Icon && (
        <div className="rounded-lg bg-primary-50 p-2.5">
          <Icon className="h-5 w-5 text-primary-600" aria-hidden="true" />
        </div>
      )}
    </div>
  );
}
