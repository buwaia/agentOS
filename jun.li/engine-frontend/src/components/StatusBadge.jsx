const COLOR = {
  pending: "bg-gray-100 text-gray-600",
  running: "bg-blue-100 text-blue-700",
  waiting_approval: "bg-yellow-100 text-yellow-700",
  done: "bg-green-100 text-green-700",
  failed: "bg-red-100 text-red-700",
};

export function StatusBadge({ status }) {
  const cls = COLOR[status] ?? "bg-gray-100 text-gray-600";
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${cls}`}
    >
      {status}
    </span>
  );
}
