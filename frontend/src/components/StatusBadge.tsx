import { STATUS_HELP, STATUS_LABELS } from "../labels";

export default function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`} title={STATUS_HELP[status]}>{STATUS_LABELS[status] ?? status}</span>;
}
