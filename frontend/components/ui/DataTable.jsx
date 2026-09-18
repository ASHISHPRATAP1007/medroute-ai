import { SkeletonRows } from "@/components/ui/Feedback";
import { EmptyState, ErrorState } from "@/components/ui/Feedback";

/**
 * columns: [{ key, header, render?: (row) => node, sortable?: bool }]
 * rowActions: (row) => node
 */
export default function DataTable({
  columns,
  rows,
  isLoading,
  isError,
  emptyMessage = "No records found.",
  rowActions,
  sortBy,
  sortOrder,
  onSort,
  rowKey = "id",
}) {
  if (isLoading) return <SkeletonRows count={6} />;
  if (isError) return <ErrorState />;
  if (!rows || rows.length === 0) return <EmptyState title={emptyMessage} />;

  return (
    <>
      {/* Desktop table */}
      <div className="hidden overflow-x-auto rounded-xl border border-slate-200 sm:block">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  scope="col"
                  className="px-4 py-3 text-left font-medium text-slate-600"
                >
                  {col.sortable ? (
                    <button
                      type="button"
                      onClick={() => onSort?.(col.key)}
                      className="flex items-center gap-1 hover:text-slate-900"
                    >
                      {col.header}
                      {sortBy === col.key && <span aria-hidden="true">{sortOrder === "asc" ? "↑" : "↓"}</span>}
                    </button>
                  ) : (
                    col.header
                  )}
                </th>
              ))}
              {rowActions && <th scope="col" className="px-4 py-3 text-right font-medium text-slate-600">Actions</th>}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rows.map((row) => (
              <tr key={row[rowKey]} className="hover:bg-slate-50">
                {columns.map((col) => (
                  <td key={col.key} className="px-4 py-3 text-slate-700">
                    {col.render ? col.render(row) : row[col.key]}
                  </td>
                ))}
                {rowActions && <td className="px-4 py-3 text-right">{rowActions(row)}</td>}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Mobile card list */}
      <div className="space-y-3 sm:hidden">
        {rows.map((row) => (
          <div key={row[rowKey]} className="card space-y-2 p-4">
            {columns.map((col) => (
              <div key={col.key} className="flex justify-between gap-3 text-sm">
                <span className="text-slate-500">{col.header}</span>
                <span className="text-right text-slate-800">{col.render ? col.render(row) : row[col.key]}</span>
              </div>
            ))}
            {rowActions && <div className="pt-2">{rowActions(row)}</div>}
          </div>
        ))}
      </div>
    </>
  );
}
