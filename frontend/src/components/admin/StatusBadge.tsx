/**
 * Colored status badge component for displaying entity statuses.
 */

const STATUS_COLORS: Record<string, string> = {
  available: "bg-green-100 text-green-800",
  adopted: "bg-blue-100 text-blue-800",
  fostered: "bg-purple-100 text-purple-800",
  medical_hold: "bg-red-100 text-red-800",
  intake: "bg-yellow-100 text-yellow-800",
  reserved: "bg-orange-100 text-orange-800",
  pending: "bg-yellow-100 text-yellow-800",
  approved: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  cancelled: "bg-gray-100 text-gray-800",
};

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const colorClasses = STATUS_COLORS[status] ?? "bg-gray-100 text-gray-800";
  const displayText = status.replace(/_/g, " ");

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${colorClasses}`}
    >
      {displayText}
    </span>
  );
}
