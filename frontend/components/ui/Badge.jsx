import clsx from "clsx";

const STATUS_STYLES = {
  ACTIVE: "bg-success-50 text-success-700",
  APPROVED: "bg-success-50 text-success-700",
  PENDING: "bg-warning-50 text-warning-700",
  INACTIVE: "bg-slate-100 text-slate-600",
  REJECTED: "bg-danger-50 text-danger-700",
  SUSPENDED: "bg-danger-50 text-danger-700",
};

export default function Badge({ status, children, className }) {
  const style = STATUS_STYLES[status] || "bg-slate-100 text-slate-600";
  return <span className={clsx("badge", style, className)}>{children || status}</span>;
}
